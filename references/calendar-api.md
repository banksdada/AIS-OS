# Google Calendar API Reference

## Auth
- Service account `aios-bot@aios-credentials.iam.gserviceaccount.com` (credentials.json in scripts/)
- Scopes: `https://www.googleapis.com/auth/calendar.readonly` (read), `.events` (write)
- **Blocker:** Calendar API must be enabled in GCP project `266063022919` before the service account can call it. Same 403 as Gmail — API disabled, not a credential problem.

## Setup
1. Open: https://console.cloud.google.com/apis/library/calendar.googleapis.com?project=266063022919
2. Click **Enable**
3. Share the target calendar with `aios-bot@aios-credentials.iam.gserviceaccount.com` as Viewer
4. Re-run the connection test below

## Common Queries

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=['https://www.googleapis.com/auth/calendar.readonly'])
service = build('calendar', 'v3', credentials=creds)

# List upcoming events
service.events().list(
    calendarId='primary', maxResults=10,
    timeMin='2026-10-14T00:00:00Z', singleEvents=True,
    orderBy='startTime').execute()

# Get one event
service.events().get(calendarId='primary', eventId=EVENT_ID).execute()
```

## Notes
- The service account has its own calendar unless the user's `primary` calendar is shared with it
- TidyCal bookings land in the user's calendar once connected; TidyCal itself is a separate API (no API key found yet)
- Recurring events: set `singleEvents=True` to expand them

## Rate Limits
- 1 million quota units/day (free tier); list = 1 unit, get = 1 unit
- Use `maxResults` + `pageToken` for pagination

## Integration Tips
- Use `timeMin`/`timeMax` ISO-8601 timestamps to bound queries
- `orderBy='startTime'` requires `singleEvents=True`
- Syncing: store `nextSyncToken` to do incremental fetches