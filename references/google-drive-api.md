# Google Drive API Reference

## Auth
- Service Account with Domain-Wide Delegation (recommended for org use)
- Or OAuth 2.0 user consent flow
- Scopes: `https://www.googleapis.com/auth/drive.readonly` (or `.drive` for write)

## Setup
1. Create GCP project → Enable Google Drive API
2. Create Service Account → download JSON key → save as `credentials.json`
3. Share target folders with the service account email

## Common Queries

```python
# List files in a folder
service.files().list(q="'FOLDER_ID' in parents", fields="files(id, name, mimeType)").execute()

# Search by name
service.files().list(q="name contains 'client'", fields="files(id, name)").execute()

# Get file metadata
service.files().get(fileId='FILE_ID', fields='id, name, modifiedTime').execute()

# Export Google Doc as text
service.files().export(fileId='DOC_ID', mimeType='text/plain').execute()
```

## Files API Quick Reference

| Method | Use Case |
|--------|----------|
| `files.list` | List/search files |
| `files.get` | Get metadata |
| `files.export` | Export Google Workspace formats |
| `files.create` | Upload new file |
| `files.update` | Update metadata/content |

## Sheets API (for CRM tracking)
- Separate API: `sheets.googleapis.com`
- Use `spreadsheets.values.get/update/append` for rows
- Range notation: `Sheet1!A2:E`

## Rate Limits
- 1,000 requests/100 sec/user (Drive)
- 500 requests/100 sec/user (Sheets)
- Use batch requests for bulk operations