# Deploying the AI OS on Coolify

Coolify is a self-hosted PaaS — point it at this repo and it builds the
`Dockerfile` and runs your scripts on a schedule. Secrets go in Coolify's env
UI, **not** in a committed `.env`.

## Prerequisites
- A Coolify instance running somewhere that can reach
  `meetup.mentoringba.org` (if it can't, run the bot locally instead).
- The `aios-bot` user enabled for the HumHub REST API (Administration → REST API).
- Google Calendar API enabled in GCP project `266063022919`, with the `primary`
  calendar shared with `aios-bot@aios-credentials.iam.gserviceaccount.com`.

## Step 1 — New resource
1. In Coolify, **Resources → New**.
2. Source: **Git** → repo `github.com/banksdada/AIS-OS` (or your fork).
3. Build preset: **Dockerfile**.
4. Click **Create**. Coolify builds the image and starts it.

## Step 2 — Environment variables
Go to the resource's **Environment** tab and add these. Never commit them.

| Key | Value | Where it comes from |
|---|---|---|
| `HUMHUB_USER` | `aios-bot` | your HumHub bot account |
| `HUMHUB_PASSWORD` | (your bot's password) | `.env` on your machine |
| `GMAIL_CLIENT_ID` | `266063022919-…apps.googleusercontent.com` | `.env` |
| `GMAIL_CLIENT_SECRET` | `GOCSPX-…` | `.env` |
| `GMAIL_REFRESH_TOKEN` | `1//03LKCoxP8…` | `.env` |
| `CLIENT_TRACKER_ID` | `1OuqO9tpzgH-…` | `.env` |
| `TIDYCAL_OAUTH_FILE` | `/run/secrets/tidycal-oauth.json` | mount an owner-protected OAuth file created by `python3 scripts/tidycal_mcp.py login`; see `references/tidycal-api.md` |
| `GOOGLE_CREDENTIALS_PATH` | `/app/scripts/credentials.json` | the service-account key is NOT copied into the image — it is provided at runtime as a mounted file, see below |
| `LODGIFY_API_KEY` | (your Lodgify API key) | `.env` — Lodgify dashboard → Integrations → API. Same Name/Value method as the rows above; powers the read-only Lodgify inbox panel |

> **The service-account JSON is a secret.** It is gitignored and excluded
> from the image by `.dockerignore`, so it never travels with the build.
> Provide it at runtime, one of:
> - **Coolify secret volume (recommended)** — mount the file at
>   `/app/scripts/credentials.json` in the resource's **Volumes** tab. The
>   scripts read it from `GOOGLE_CREDENTIALS_PATH`, which defaults to
>   `scripts/credentials.json` relative to the script directory, so the mount
>   path above works without changing any env var.
> - **Copy it in manually** — `docker cp` the file into a running container
>   at `scripts/credentials.json`, or
> - **Local runs** — keep `scripts/credentials.json` on your machine as you
>   already have it; the scripts resolve it relative to their own directory.

## Step 3 — Deploy the dashboard
The default container command now serves the live AI OS dashboard on port
`8080`.

1. Open the resource → **Domains** and set the target port to `8080` (the
  container's internal listening port). Do not use the public host port or
  `80`/`443` as the target. The resource must be running and healthy.
2. In the resource → **Commands** section, the default command is already:

```
python3 scripts/dashboard/serve.py
```

3. Visit the resource's public URL or `http://<host>:8080/` to view the live
   dashboard.

The dashboard fetches `/data` from the same container and refreshes the payload
with the latest connection and CRM status.
Coolify/Docker can verify the process through `GET /health`, which returns
`200 OK` without running any external integrations.

## Step 4 — Run a task
To run a specific script instead of the dashboard, open the resource →
**Commands** → run:

```
python3 scripts/verify-connections.py
```

For the HumHub bot:

```
python3 scripts/humhub-bot.py poll
```

## Step 5 — Schedules (optional)
In the resource → **Schedules**, add a cron job to refresh the generated data
and keep the dashboard current. For example:

```
0 8 * * *  python3 scripts/dashboard/generate.py
```

Or run the verifier daily:

```
0 8 * * *  python3 scripts/verify-connections.py
```

Coolify runs the command inside the container, so it inherits the env vars
from Step 2.

## Troubleshooting
- **Build fails** → check the resource log for `pip install` errors. Confirm
  `requirements.txt` pins versions that exist on PyPI.
- **502 / "no available server"** → the proxy cannot find a healthy app
  container. Confirm the resource is running, its domain target port is `8080`,
  and `GET /health` returns `200` inside the container. Check deployment logs
  for a startup or image-build failure, then redeploy the latest `main` commit.
- **"403" on HumHub** → the `aios-bot` account isn't enabled for the REST API.
  Enable it in the admin panel (Administration → REST API).
- **"403" on Calendar** → the Calendar API isn't enabled in GCP project
  `266063022919`, or the service account isn't shared on the calendar.
- **Can't reach the host** → the Coolify server's outbound HTTPS to
  `meetup.mentoringba.org` is blocked. Run the bot on your local machine
  instead — it works identically there.
