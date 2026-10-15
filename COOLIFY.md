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
| `GOOGLE_CREDENTIALS_PATH` | `/app/scripts/credentials.json` | the service-account key is NOT copied into the image — it is provided at runtime as a mounted file, see below |

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

## Step 3 — Run a task
The container's default command is the connection verifier. To run a specific
script, open the resource → **Commands** → run:

```
python3 scripts/verify-connections.py
```

For the HumHub bot:

```
python3 scripts/humhub-bot.py poll
```

## Step 4 — Schedules (optional)
In the resource → **Schedules**, add a cron job to run the bot daily, e.g.:

```
0 8 * * *  python3 scripts/humhub-bot.py poll
```

Coolify runs the command inside the container, so it inherits the env vars
from Step 2.

## Troubleshooting
- **Build fails** → check the resource log for `pip install` errors. Confirm
  `requirements.txt` pins versions that exist on PyPI.
- **"403" on HumHub** → the `aios-bot` account isn't enabled for the REST API.
  Enable it in the admin panel (Administration → REST API).
- **"403" on Calendar** → the Calendar API isn't enabled in GCP project
  `266063022919`, or the service account isn't shared on the calendar.
- **Can't reach the host** → the Coolify server's outbound HTTPS to
  `meetup.mentoringba.org` is blocked. Run the bot on your local machine
  instead — it works identically there.