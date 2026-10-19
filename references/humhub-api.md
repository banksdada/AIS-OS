# HumHub REST API Reference (meetup.mentoringba.org)

Site: `https://meetup.mentoringba.org` — "Business Analysis Community", a self-hosted
HumHub instance (NOT meetup.com). Spaces include *Ask Experts*, *Generative AI*,
*Leadership Talks*. Admin username: `tribal_chief`.

## Auth

Two methods, both configured from the admin panel (**Administration → REST API**):

1. **HTTP Basic Auth** — send `Authorization: Basic base64(user:pass)`. Simplest.
2. **JWT** — `POST api/v1/auth/login` with `username`/`password` → returns
   `auth_token`. Use it as `Authorization: Bearer <token>`.

Whichever is enabled, the user must also be **enabled for the API**: in
**Administration → REST API**, tick *Enabled for all registered users*, or add
`tribal_chief` to the *Enabled users* list. A correct password with the user not
enabled returns `401 "Invalid user!"`.

> Do not paste the password into chat. Store it in `.env` (e.g.
> `HUMHUB_PASSWORD=...`) and load it from there — never commit it.

## Host WAF gotcha (diagnosed 2026-10-19)

The server behind meetup.mentoringba.org (LiteSpeed) has a WAF rule that
answers **non-browser User-Agents with a 403 HTML block page** (`<title>
403 Forbidden</title>`, no HumHub branding) instead of reaching the REST
module. urllib's default `Python-urllib/...` UA always hits this; a browser
UA (`Mozilla/5.0 ...`) gets through. Sending several probes in quick
succession additionally triggers **connection resets** (temporary
rate-limit ban) that last a few minutes. So:

- Always send a browser-like `User-Agent` on this host (the verifier does).
- Space out probes; if you see `Connection reset by peer`, wait ~2 min.
- A **403 HTML page** means the WAF blocked the request — it does NOT mean
  the password or API access is wrong. A real auth failure is `401` with
  JSON `{"message": "Invalid user!"}`.
- "Egress unreliable" in older notes was this rate-limiting, not the
  sandbox.

## Setup
1. Log in as `tribal_chief` at `https://meetup.mentoringba.org`.
2. **Administration → REST API** → enable *Allow HTTP Basic Authentication*
   (and optionally *Enabled for all registered users*).
3. Save the password in `.env` as `HUMHUB_PASSWORD`.
4. Run `python3 scripts/verify-connections.py` — Domain 8 should flip to OK.

## Common queries

```python
import base64, os, requests

BASE = 'https://meetup.mentoringba.org'
USER = os.environ['HUMHUB_USER']        # aios-bot (content admin)
PASS = os.environ['HUMHUB_PASSWORD']

def api(method, path, **kwargs):
    r = requests.request(method, BASE + '/api/v1/' + path,
                         auth=(USER, PASS), **kwargs)
    r.raise_for_status()
    return r.json()

# Who am I?
api('GET', 'auth/current')

# List spaces
spaces = api('GET', 'space/list')['results']
# -> each has 'id', 'name', 'description'

# List posts across the site
api('GET', 'post/find', params={'limit': 25})

# Posts in one space (containerId = space id)
api('GET', f'post/findByContainer/{space_id}', params={'limit': 25})

# Create a post in a space
api('POST', f'post/create/{space_id}', json={
    'data': {
        'message': 'Your post text here',
        'content': {'metadata': {'visibility': 2}},   # 0 private, 1 owner, 2 public
    }
})

# Comments on a post
api('GET', f'comment/findByContent/{post_id}')

# Notifications (engagement)
api('GET', 'notification/list')
api('GET', 'notification/unseen')
```

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| POST | `auth/login` | get a JWT token |
| GET | `auth/current` | who am I |
| GET | `user/list` | list users (paginated) |
| GET | `user/username/<name>` | one user by username |
| GET | `space/list` | list spaces |
| GET | `space/view/<id>` | one space |
| POST | `space/create` | create a space |
| GET | `post/find` | all posts (paginated) |
| GET | `post/findByContainer/<id>` | posts in a space |
| POST | `post/create/<containerId>` | create a post |
| GET | `post/view/<id>` | one post |
| PUT | `post/update/<id>` | edit a post |
| DELETE | `post/delete/<id>` | delete a post |
| GET | `comment/findByContent/<id>` | comments on a post |
| POST | `comment/create/<contentId>` | add a comment |
| GET | `notification/list` | notifications (paginated) |
| GET | `notification/unseen` | unseen count |
| POST | `notification/markAsSeen` | mark seen |

Pagination: `?limit=` (max 100) and `?page=` (1-based). Responses are
`{total, page, pages, links, results}`.

## Notes
- CSRF is disabled for the REST module — no token needed.
- Response format is JSON; errors return `{code, message}` with the HTTP status.
- `post/create` body is `data.message` for the text; `data.content.metadata.visibility`
  is `0` private / `1` owner-only / `2` public.
- The space's numeric `id` doubles as its `containerId` for posts and comments.

## Rate limits
No documented limit. Be reasonable: poll notifications every few minutes, not
every second.