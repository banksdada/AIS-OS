#!/usr/bin/env python3
"""
Download and extract text from Google Drive files.

Usage:
  python3 gdrive-get.py FILE_ID                 # print extracted text
  python3 gdrive-get.py FILE_ID --out out.txt   # save extracted text
  python3 gdrive-get.py --folder FOLDER_ID      # all files in a folder
  python3 gdrive-get.py --folder FOLDER_ID --save-dir tmp/  # also keep originals

Handles Google Docs (export), PDFs, DOCX, and plain text. Extracted text is
printed to stdout so it can be piped or read directly.
"""

import argparse
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get(
    'GOOGLE_CREDENTIALS_PATH', os.path.join(_SCRIPT_DIR, 'credentials.json'))

EXPORT_TYPES = {
    'application/vnd.google-apps.document': ('text/plain', '.txt'),
    'application/vnd.google-apps.spreadsheet': ('text/csv', '.csv'),
    'application/vnd.google-apps.presentation': ('text/plain', '.txt'),
}

PDF_CTX = "@SQL=SELECT xObject, xObject[2] FROM Page"


def _pdf_text(path):
    """Extract text from a PDF. Tries common libraries in order."""
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except ImportError:
        pass
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    except ImportError:
        return None


def _docx_text(path):
    """Extract text from a DOCX, including tables."""
    try:
        import docx
    except ImportError:
        return None
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    for table in d.tables:
        for row in table.rows:
            parts.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(parts)


def extract_text(path, mime):
    """Return extracted text for a downloaded file, or None if unsupported."""
    lower = path.lower()
    if lower.endswith('.pdf'):
        return _pdf_text(path)
    if lower.endswith(('.docx', '.doc')):
        return _docx_text(path)
    if lower.endswith(('.txt', '.csv', '.md')):
        with open(path, errors='replace') as f:
            return f.read()
    return None


def download(service, file_id, dest, export_mime=None):
    """Download a Drive file to dest. Exports Google-native docs."""
    if export_mime:
        req = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        req = service.files().get_media(fileId=file_id)
    with open(dest, 'wb') as f:
        downloader = MediaIoBaseDownload(f, req)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def process(service, meta, save_dir=None, out=None):
    """Download one file, extract its text, print or save it."""
    name, fid, mime = meta['name'], meta['id'], meta['mimeType']
    export = EXPORT_TYPES.get(mime)
    suffix = export[1] if export else os.path.splitext(name)[1]

    tmp_dest = os.path.join('/tmp', f'gdrive-{fid}{suffix}')
    download(service, fid, tmp_dest, export_mime=export[0] if export else None)

    text = extract_text(tmp_dest, mime)
    if text is None:
        # Google-native with no exporter, or an unsupported binary.
        return f"[{name}: could not extract text ({mime})]"

    header = f"===== {name} ====="
    body = f"{header}\n{text.strip()}\n"

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        safe = name.replace('/', '_')
        with open(os.path.join(save_dir, safe + '.txt'), 'w') as f:
            f.write(body)

    if out:
        with open(out, 'w') as f:
            f.write(body)
    else:
        print(body)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_id', nargs='?', help='Drive file ID')
    parser.add_argument('--folder', help='Folder ID: process all files in it')
    parser.add_argument('--out', help='Save extracted text to this file')
    parser.add_argument('--save-dir', help='Save each extracted text to this dir')
    parser.add_argument('--max', type=int, default=50)
    args = parser.parse_args()

    if not args.file_id and not args.folder:
        parser.error('give a file_id or --folder')

    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    if args.folder:
        results = service.files().list(
            q=f"'{args.folder}' in parents and trashed=false",
            pageSize=args.max,
            fields="files(id, name, mimeType, modifiedTime)",
        ).execute()
        files = sorted(results.get('files', []), key=lambda f: f['name'])
        if not files:
            print('No files in that folder (or not shared with the service account).')
            return
        for meta in files:
            note = process(service, meta, save_dir=args.save_dir)
            if note:
                print(note)
    else:
        meta = service.files().get(
            fileId=args.file_id, fields='id, name, mimeType').execute()
        note = process(service, meta, out=args.out)
        if note:
            print(note, file=sys.stderr)


if __name__ == '__main__':
    main()
