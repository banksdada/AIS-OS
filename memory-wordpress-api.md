---
name: wordpress-api-creds
description: WordPress Application Passwords for three sites, stored without spaces
metadata:
  type: user
---

## WordPress app passwords

Three WordPress sites are configured for the AI OS dashboard in `.env` as
`WP_SITES` (JSON list):

| name | url | user |
|---|---|---|
| webawesome | https://www.webawesome.co.uk | banksdada |
| mentoringba | https://mentoringba.org | mentorbank |
| bhoSupport | https://besthomesupport.uk | developer |

**Critical:** app passwords must be stored **without the spaces** that
WordPress displays them in. WordPress shows passwords as groups of 4
(e.g. `XXXX WXXX XXXX XXXX XXXX XXXX`), but the actual credential is the
concatenated string (`XXXXXXXXXXXXXXXXXXXXXXXX`). Storing the spaced form
causes 401 errors because the `.env` loader splits on `=` and preserves
the literal value including spaces.

**How to apply:** When adding new WordPress sites, generate an Application
Password in WP Admin → Users → Your Profile → Application Passwords, paste it
into `.env` without spaces, then run
`python3 scripts/dashboard/generate.py` to verify.

**Why:** The dashboard's `_wordpress()` function (in `scripts/dashboard/
generate.py`) reads `WP_SITES` from the environment and probes each site's
`wp-json/wp/v2/posts?per_page=1` endpoint. It uses `requests` for better
TLS handling than stdlib `urllib`. Reference: `references/wordpress-api.md`.

[[wordpress-api-creds]]