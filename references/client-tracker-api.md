# Google Sheets API Reference (client-tracker)

## Auth
- Same service account setup as Drive
- Scopes: `https://www.googleapis.com/auth/spreadsheets`
- `credentials.json` from GCP project with Sheets API enabled

## Setup
1. Create Google Sheet → copy its ID
2. Share sheet with service account email
3. Set `CLIENT_TRACKER_ID` env var

## Endpoints (via Google Sheets API v4)

### Read all client rows
```
GET https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values?range=A1%3AE
Authorization: Bearer {ACCESS_TOKEN}
```
Returns all rows including headers.

### Append new client
```
POST https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate
Authorization: Bearer {ACCESS_TOKEN}
```
Body: `{"requests": [{"appendDimension": {"range": {"sheetId": 0, "dimension": "ROWS", "startRowIndex": 1}, "values": [[name, email, stage, '', '']]}}]}`

### Update stage column
```
PATCH https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{range}
Authorization: Bearer {ACCESS_TOKEN}
```
Range format: `C2` (first data row, column C = stage)
Value: `"Won"` or whatever stage name

## Common Operations

| Operation | Method | Range |
|-----------|--------|-------|
| List all clients | `GET /values` | `A1:E` |
| Add client | `batchUpdate` append | `A1:E` |
| Move to Won | `PATCH` | `C{N}` |
| Search by name | `GET /values` then filter client-side |
| Export to CSV | Read all rows, format |

## Rate Limits
- 500 requests/100 sec/project (Sheets)
- Use `maxResults` + `pageToken` for pagination
- Batch requests for bulk updates

## Integration Tips
- Set `CLIENT_TRACKER_ID` in your env
- Keep the sheet shared with service account
- Stage progression: Lead → Contacted → Proposal → Won → Lost
- Weekly review: run `/audit` to check freshness