#!/usr/bin/env python3
"""
List files/folders in Google Drive.
Usage: python3 gdrive-list.py [--query "name contains 'clients'"] [--folder FOLDER_ID] [--max 10]
"""

import os
import sys
import argparse
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_PATH', os.path.join(_SCRIPT_DIR, 'credentials.json'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query', default=None, help='GDRIVE query filter')
    parser.add_argument('--folder', default=None, help='Parent folder ID')
    parser.add_argument('--max', type=int, default=20, help='Max results')
    args = parser.parse_args()

    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    query = f"'{args.folder}' in parents" if args.folder else ""
    if args.query:
        query = f"({query}) and {args.query}" if query else args.query

    results = service.files().list(q=query, pageSize=args.max, fields="files(id, name, mimeType, modifiedTime)").execute()
    files = results.get('files', [])

    for f in files:
        print(f"{f['name']} ({f['id']}): {f['mimeType']} [{f['modifiedTime']}]")

if __name__ == '__main__':
    main()