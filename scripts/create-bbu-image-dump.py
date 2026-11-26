#!/usr/bin/env python3
"""Create and share the Beauty Booked Up Google Drive image dump and prompt bank."""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
PROMPT_PATH = ROOT / "projects" / "beautybookedup" / "canva-image-prompts.txt"

PARENT_FOLDER_ID = "1J8HSyf8QjfCLh5PH8Atm-iGsyQZml-7H"
MAIN_FOLDER_NAME = "Beauty Booked Up - Canva image dump"
SUBFOLDERS = ["01 Raw uploads", "02 Approved", "03 Used in drafts", "Prompt bank"]
DOC_NAME = "Beauty Booked Up - Canva image prompts (244)"
MANIFEST_NAME = "Beauty Booked Up - image manifest"
PEOPLE = ["bankoledada@gmail.com", "sharon.darasimi@gmail.com"]
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def read_env(name):
    for line in ENV_FILE.read_text().splitlines():
        if line.strip().startswith(name + "="):
            return line.strip().split("=", 1)[1].strip()
    return None


def get_credentials():
    token = os.environ.get("DRIVE_REFRESH_TOKEN") or read_env("DRIVE_REFRESH_TOKEN")
    client_id = os.environ.get("GMAIL_CLIENT_ID") or read_env("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET") or read_env("GMAIL_CLIENT_SECRET")
    if not token or not client_id or not client_secret:
        print("ERROR: Drive/Sheets credentials are missing. Run scripts/gdrive-authorize.py first.")
        raise SystemExit(1)
    creds = Credentials(
        token=None,
        refresh_token=token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    try:
        creds.refresh(Request())
    except Exception as exc:
        print("ERROR: could not refresh Drive/Sheets access. Run scripts/gdrive-authorize.py again.")
        print(str(exc))
        raise SystemExit(1)
    return creds


def find_file(drive, name, mime_type, parent):
    query = (
        f"name = '{name}' and mimeType = '{mime_type}' and "
        f"'{parent}' in parents and trashed = false"
    )
    results = drive.files().list(q=query, fields="files(id,name,webViewLink)").execute()
    files = results.get("files", [])
    return files[0] if files else None


def ensure_folder(drive, name, parent):
    existing = find_file(drive, name, "application/vnd.google-apps.folder", parent)
    if existing:
        print("Folder exists:", name)
        return existing
    created = drive.files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent],
        },
        fields="id,name,webViewLink",
    ).execute()
    print("Folder created:", name)
    return created


def share(drive, file_id, email):
    permissions = drive.permissions().list(
        fileId=file_id, fields="permissions(id,emailAddress)"
    ).execute().get("permissions", [])
    if any(p.get("emailAddress", "").lower() == email.lower() for p in permissions):
        return
    drive.permissions().create(
        fileId=file_id,
        body={"type": "user", "role": "writer", "emailAddress": email},
        sendNotificationEmail=False,
        fields="id",
    ).execute()


def ensure_prompt_doc(drive, folder_id):
    existing = find_file(drive, DOC_NAME, "application/vnd.google-apps.document", folder_id)
    if existing:
        print("Prompt Doc exists:", DOC_NAME)
        return existing
    media = MediaFileUpload(str(PROMPT_PATH), mimetype="text/plain", resumable=True)
    created = drive.files().create(
        body={
            "name": DOC_NAME,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_id],
        },
        media_body=media,
        fields="id,name,webViewLink",
    ).execute()
    print("Prompt Doc created:", DOC_NAME)
    return created


def ensure_manifest(sheets, drive, folder_id):
    existing = find_file(drive, MANIFEST_NAME, "application/vnd.google-apps.spreadsheet", folder_id)
    if existing:
        print("Manifest Sheet exists:", MANIFEST_NAME)
        return existing
    spreadsheet = sheets.spreadsheets().create(
        body={
            "properties": {"title": MANIFEST_NAME},
            "sheets": [
                {"properties": {"title": "Image manifest"}},
                {"properties": {"title": "How to use"}},
            ],
        }
    ).execute()
    spreadsheet_id = spreadsheet["spreadsheetId"]
    headers = [
        "filename",
        "drive_link",
        "category",
        "niche",
        "location",
        "topic",
        "status",
        "credit",
        "licence",
        "approved",
        "used_in_draft",
        "notes",
    ]
    instructions = [
        ["Field", "What it means"],
        ["filename", "Exact file name downloaded from Canva or supplied by Sharon."],
        ["drive_link", "Share link to the image in this folder."],
        ["category", "Prompt category from the prompt bank."],
        ["niche", "lash tech, nail tech, hairdresser, African hair, aesthetics, and so on."],
        ["location", "Wigan, Manchester, North West, or general."],
        ["topic", "The blog or microsite topic this image suits."],
        ["status", "raw, approved, used, or rejected."],
        ["credit", "Canva, Sharon, or source name."],
        ["licence", "Record the licence or export rights."],
        ["approved", "yes or no. The draft script may only use approved images."],
        ["used_in_draft", "Draft file path once the image is used."],
    ]
    sheets.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "RAW",
            "data": [
                {"range": "Image manifest!A1:L1", "values": [headers]},
                {"range": "How to use!A1:B13", "values": instructions},
            ],
        },
    ).execute()
    drive.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        fields="id,parents",
    ).execute()
    print("Manifest Sheet created:", MANIFEST_NAME)
    return {
        "id": spreadsheet_id,
        "webViewLink": spreadsheet.get("spreadsheetUrl", ""),
    }


def main():
    creds = get_credentials()
    drive = build("drive", "v3", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)

    main_folder = ensure_folder(drive, MAIN_FOLDER_NAME, PARENT_FOLDER_ID)
    children = {
        name: ensure_folder(drive, name, main_folder["id"]) for name in SUBFOLDERS
    }
    prompt_doc = ensure_prompt_doc(drive, children["Prompt bank"]["id"])
    manifest = ensure_manifest(sheets, drive, main_folder["id"])

    shared_files = [main_folder, prompt_doc, manifest] + list(children.values())
    seen = set()
    for item in shared_files:
        if not item or item["id"] in seen:
            continue
        seen.add(item["id"])
        for email in PEOPLE:
            share(drive, item["id"], email)

    print("Main folder:", main_folder.get("webViewLink", ""))
    print("Prompt Doc:", prompt_doc.get("webViewLink", ""))
    print("Manifest Sheet:", manifest.get("webViewLink", ""))
    for name, folder in children.items():
        print(f"{name}:", folder.get("webViewLink", ""))
    print("Shared with:", ", ".join(PEOPLE))


if __name__ == "__main__":
    main()
