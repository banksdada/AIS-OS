# Client Tracker Workflow

A documented workflow for tracking clients and moving them through the sales pipeline.

## Trigger
- Manually run: `python3 scripts/client-tracker.py list`
- Or when a new lead is added: `python3 scripts/client-tracker.py add "Name" "Email" "Stage"`

## Input
- Google Sheet (CLIENT_TRACKER_ID env var)
- Client data: name, email, stage, last contact, notes

## Setup
1. Create a Google Sheet named "webawesome CRM" with a sheet tab called "Clients".
2. Share it with `aios-bot@aios-credentials.iam.gserviceaccount.com` as Editor.
3. Set `CLIENT_TRACKER_ID` to the sheet ID (from the URL: `/d/<ID>/edit`).
4. The service account cannot create its own sheets (no Drive quota), so the sheet must be created in the main account and shared.

## Stages
1. **Lead** — new contact, not yet contacted
2. **Contacted** — reached out, awaiting response
3. **Proposal** — sent a proposal, waiting for decision
4. **Won** — signed contract, client acquired
5. **Lost** — did not close

## Output
- List of all clients with current stage
- Stage transitions logged to decisions/log.md

## Commands
```bash
# List all clients
python3 scripts/client-tracker.py list

# Add a new client
python3 scripts/client-tracker.py add "Client Name" "email@example.com" "Lead"

# Move a client to a new stage
python3 scripts/client-tracker.py stage "Client Name" "Proposal"
```

## Acceptance Criteria
- At least one client tracked in the sheet
- Stage transitions recorded in decisions/log.md
- Weekly review: run `/audit` to check freshness

## Failure Handling
- If credentials.json missing: print error, suggest `gcloud auth application-default login`
- If CLIENT_TRACKER_ID missing: print error, suggest creating a Google Sheet and sharing it with the service account
- If Sheets API returns 403 "caller does not have permission": the service account lacks editor access to the sheet. Re-share the sheet with `aios-bot@aios-credentials.iam.gserviceaccount.com` as Editor. Note the service account cannot create its own sheets (no Drive quota).

## Next Step
- Wire up Stripe to track revenue per client (Domain 1)
- Add automated weekly digest via Gmail API (Domain 2)