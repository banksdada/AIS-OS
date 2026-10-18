# TidyCal MCP Connector

The dashboard reads upcoming bookings and booking types from TidyCal's
read-only MCP server at `https://tidycal.com/mcp`. It uses OAuth 2.1 with PKCE
and the `mcp:scheduling:read` scope described in `CLAUDE.md`. TidyCal Pro is
required.

## Connect locally

Run this on the machine hosting the dashboard:

```sh
python3 scripts/tidycal_mcp.py login
```

The command dynamically registers an OAuth client, opens TidyCal sign-in, and
receives the authorization callback on `127.0.0.1:8765`. Approve read-only
access in TidyCal. Tokens are stored outside the repository at
`~/.config/aios/tidycal-oauth.json` with owner-only permissions. To use another
path, set `TIDYCAL_OAUTH_FILE` before running the command and dashboard.

The connector refreshes access tokens as needed. Dashboard snapshots include
only each booking's type/title, start/end time, and status plus booking type
names and durations. Guest names, email addresses, answers, payment data, and
meeting locations are not persisted or sent to the browser.

## Coolify

Complete `login` on a trusted local machine, then securely mount the generated
OAuth file into the dashboard container. Set `TIDYCAL_OAUTH_FILE` to that mount
path in Coolify. Do not commit or paste the file contents into Git or logs.
The OAuth client is registered for a loopback callback; the token file can be
used by the server after the local authorization is complete.

If the account is not Pro, or authorization expires/revokes, the dashboard
shows a disconnected state. Re-run `login` to reconnect. The dashboard caches
successful results for five minutes and failed connection status for one
minute.
