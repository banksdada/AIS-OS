# WordPress REST API Reference

Three WordPress sites connected to the AI OS dashboard via Application Passwords.

| Site | URL | WP user | Purpose |
|---|---|---|---|
| webawesome | `https://www.webawesome.co.uk` | `banksdada` | UK digital agency — main site |
| mentoringba | `https://mentoringba.org` | `mentorbank` | Business analysis mentoring |
| bhoSupport | `https://besthomesupport.uk` | `developer` | Home care referrals |

All three are self-hosted WordPress on LiteSpeed. `wp-json/wp/v2/` is reachable
without auth; the endpoints below require an Application Password.

## Auth

**Application Password** (Users → Edit → Application Passwords in the WP admin).
Sent as HTTP Basic auth:

```python
import base64, requests

token = base64.b64encode(f"{user}:{app_password}".encode()).decode()
r = requests.get(url + '/wp-json/wp/v2/posts?per_page=1',
                 headers={'Authorization': 'Basic ' + token})
```

> **Important — app passwords are stored WITHOUT the spaces WordPress displays
> them in.** WordPress shows them as groups of 4 (e.g.
> `XXXX WXXX XXXX XXXX XXXX XXXX`), but the actual credential is the
> concatenated string `XXXXXXXXXXXXXXXXXXXXXXXX`. The `.env` loader splits each
> line on `=`, so spaces inside the value are preserved as written — which is
> why the spaced form fails with `401`. Always store the no-space form.

Credentials live in `.env` as `WP_SITES` (a JSON list). Never commit the
passwords — `.env` is gitignored.

## Setup

1. Log in to each site's WordPress admin.
2. Go to **Users → Your Profile → Application Passwords**.
3. Add a new application password (name it "AIOS Dashboard").
4. Copy the password and paste it into `.env` **without the spaces**.
5. Run `python3 scripts/dashboard/generate.py` — the WordPress panel should
   show each site with its latest post.

## Dashboard integration

`scripts/dashboard/generate.py::_wordpress()` reads `WP_SITES` from the
environment and probes each site's `wp-json/wp/v2/posts?per_page=1`. The
dashboard page renders one card per site showing:

- OK / Issue status
- Site name and URL
- Latest post title and date

The probe is read-only — it only lists posts. It never creates, edits, or
deletes content.

## Common queries

```python
import base64, requests

BASE = 'https://www.webawesome.co.uk'
USER = 'banksdada'
PW = 'XXXXXXXXXXXXXXXXXXXXXXXX'   # no spaces — real password lives in .env

def api(path, **params):
    token = base64.b64encode(f"{USER}:{PW}".encode()).decode()
    r = requests.get(BASE + '/wp-json/wp/v2/' + path,
                     headers={'Authorization': 'Basic ' + token}, params=params)
    r.raise_for_status()
    return r.json()

# Latest posts
posts = api('posts', per_page=5)

# One post by ID
api('posts/12421')

# Pages
api('pages', per_page=5)

# Media / images
api('media', per_page=5)

# Categories and tags
api('categories'); api('tags')

# User profile (who am I, what can I do)
me = api('users/me')
```

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| GET | `posts` | list posts (paginated) |
| GET | `posts/<id>` | one post |
| GET | `pages` | list pages |
| GET | `media` | list media |
| GET | `categories` | list categories |
| GET | `tags` | list tags |
| GET | `users/me` | authenticated user profile |
| GET | `users` | list users (needs edit_users cap) |

Pagination: `?per_page=` (max 100) and `?page=`. Responses are JSON arrays;
list endpoints return `[...]` directly.

## Notes

- The REST API is enabled by default in WordPress 4.7+. No plugin needed.
- Application Passwords only work over HTTPS — the dashboard probes use
  `https://`.
- If a site returns 401, check the username and that the password is stored
  without spaces. If it returns 403, the user lacks the `read` capability.
- CSRF is not needed for read-only GET requests.

## Rate limits

No documented limit. The dashboard probes once per page load (every 60 s on
the auto-refresh). Keep it to a handful of calls per minute per site.