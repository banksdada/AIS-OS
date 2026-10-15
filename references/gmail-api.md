# Gmail API Reference

## Auth — OAuth 2.0 (refresh-token flow)

**Why OAuth, not a service account:** the target mailbox is `bankoledada@gmail.com`,
a *consumer* Gmail account. Service accounts only work with Google Workspace
accounts via domain-wide delegation in an Admin console — there is no Admin
console for a personal `gmail.com` address, and Gmail's "Grant access to your
account" rejects service-account identities outright ("Google account address you
have specified is invalid"). So OAuth 2.0 is the only path that works here.

- **Client ID / secret** — from the OAuth client in GCP (see Setup).
- **Refresh token** — stored in `.env` as `GMAIL_REFRESH_TOKEN`. Never commit it.
- **Scopes:** `https://www.googleapis.com/auth/gmail.readonly` (read).
  Add `gmail.modify` (labels / mark read) and/or `gmail.send` (send) if needed.
- The verifier uses `userId='me'`, which resolves to the mailbox that consented.

## Setup status: COMPLETE (2026-10-15)

All steps below are done. Values live in `.env`:
- `GMAIL_CLIENT_ID=266063022919-5nmtj9vvutmpb55io5ifa5475gmeki91.apps.googleusercontent.com`
- `GMAIL_CLIENT_SECRET=GOCSPX-…` (never commit)
- `GMAIL_REFRESH_TOKEN=1//03LKCoxP8…` (never commit)

Verified live: `python3 scripts/verify-connections.py` → Gmail OK, est. 201 messages.

## Setup (one time, ~10 min)

1. Open **https://console.cloud.google.com/apis/credentials** (project `266063022919`).
2. **OAuth consent screen** → choose **External**.
   - App name: anything, e.g. "webawesome AIOS".
   - Developer contact: `bankoledada@gmail.com`.
   - App domain: app URL `https://webawesome.co.uk` (or any), privacy policy link optional for testing.
   - **Scopes** → Add/remove scopes → search "Gmail" → **gmail.readonly**
     (add `gmail.modify` / `gmail.send` if you want those).
   - **Test users** → add `bankoledada@gmail.com`.
   - Save and continue through the screens.
3. **Credentials** → **Create credentials** → **OAuth client ID** → application type **Web application**.
   - Name: anything.
   - **Authorized redirect URIs** → add `http://localhost:8085/` (fine for testing).
   - Create.
4. Copy the **Client ID** and **Client Secret** into `.env`:
   ```
   GMAIL_CLIENT_ID=xxxxxxx-xxxxx.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=xxxx
   ```
5. **Get a refresh token** — run once in a browser:
   ```
   https://accounts.google.com/o/oauth2/v2/auth?
     client_id=<GMAIL_CLIENT_ID>&
     redirect_uri=http://localhost:8085/&
     response_type=code&
     scope=https://www.googleapis.com/auth/gmail.readonly&
     access_type=offline&
     prompt=consent
   ```
   Sign in as `bankoledada@gmail.com`, consent, then the browser lands on
   `http://localhost:8085/?code=<CODE>`. Copy `CODE`.
6. Exchange the code (or use any OAuth playground) to get the refresh token, and
   paste it into `.env`:
   ```
   GMAIL_REFRESH_TOKEN=xxxx
   ```
7. Run `python3 scripts/verify-connections.py` — Gmail should flip to OK.

## Common queries

```python
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials(
    token=None,
    refresh_token=os.environ['GMAIL_REFRESH_TOKEN'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id=os.environ['GMAIL_CLIENT_ID'],
    client_secret=os.environ['GMAIL_CLIENT_SECRET'],
    scopes=['https://www.googleapis.com/auth/gmail.readonly'])

service = build('gmail', 'v1', credentials=creds)

# List inbox messages
service.users().messages().list(userId='me', maxResults=10, q='label:inbox').execute()

# Read one message (full, with HTML body)
service.users().messages().get(userId='me', id=MESSAGE_ID, format='full').execute()

# Search by query
service.users().messages().list(userId='me', q='subject:"client" newer_than:7d').execute()
```

## Message format notes
- `format='full'` returns `payload.parts` with `mimeType` and `body.data` (base64url-encoded)
- `format='metadata'` returns headers only — cheaper for listing
- Thread access: `service.users().threads().get(userId='me', id=THREAD_ID).execute()`

## Rate Limits
- 1 billion quota units/day (free tier); read = 1 unit, metadata = 1 unit, full = 5 units
- Use `maxResults` + `pageToken` for pagination

## Integration Tips
- Refresh tokens are long-lived but can be revoked by Google if the app is unused
  for a long time, or if you revoke it in Google Account → Security → Third-party apps.
- Use `q=` search syntax: `from:`, `to:`, `subject:`, `label:`, `is:`, `newer_than:`,
  `older_than:`, `in:`.
- Stage progression for customer emails: new lead → follow-up → proposal → won.