#!/usr/bin/env python3
"""
Upload a file to a Drive folder as the user (OAuth delegation).

The service account has no Drive storage quota, so it cannot own files. This
uses the user's own DRIVE_REFRESH_TOKEN instead, so the file is owned by the
account that has the storage.

Usage:
  python3 scripts/gdrive-upload.py LOCAL_FILE --folder FOLDER_ID --name "name.txt"
  python3 scripts/gdrive-upload.py LOCAL_FILE --folder FOLDER_ID   # keeps the local name
"""

import argparse
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
ENV_FILE = os.path.join(_REPO_ROOT, '.env')

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def _read_env(name):
    if not os.path.exists(ENV_FILE):
        return None
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith(name + '='):
                return line.split('=', 1)[1].strip()
    return None


def get_service():
    """Build a Drive service that acts as the user, not the service account."""
    token = os.environ.get('DRIVE_REFRESH_TOKEN') or _read_env('DRIVE_REFRESH_TOKEN')
    if not token:
        print('ERROR: DRIVE_REFRESH_TOKEN not set. Run scripts/gdrive-authorize.py first.')
        sys.exit(1)
    creds = Credentials(
        token=None, refresh_token=token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.environ.get('GMAIL_CLIENT_ID') or _read_env('GMAIL_CLIENT_ID'),
        client_secret=os.environ.get('GMAIL_CLIENT_SECRET') or _read_env('GMAIL_CLIENT_SECRET'),
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)


def upload(service, path, folder_id, name=None, mime='text/plain'):
    name = name or os.path.basename(path)
    media = MediaFileUpload(path, mimetype=mime, resumable=True)
    body = {'name': name, 'parents': [folder_id]}
    f = service.files().create(body=body, media_body=media,
                               fields='id,name,webViewLink,owners').execute()
    return f


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--folder', required=True, help='Parent folder ID')
    parser.add_argument('--name', help='Name to save as (default: local filename)')
    parser.add_argument('--mime', default='text/plain')
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f'ERROR: {args.path} not found.')
        sys.exit(1)

    service = get_service()
    f = upload(service, args.path, args.folder, args.name, args.mime)
    print('Uploaded:', f['name'])
    print('Owner:', [o.get('emailAddress') for o in f.get('owners', [])])
    print(f.get('webViewLink', ''))


if __name__ == '__main__':
    main()
