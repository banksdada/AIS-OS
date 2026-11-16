# webawesome-site-agent

**Webby** — the WebAwesome site agent. Public chat widget for webawesome.co.uk
plus a shared agent brain. One brain, two doors: the site widget and an opencode
subagent answer from the same `knowledge/` folder and use the same booking tool.

## Status

- [x] TidyCal token verified; live slots read OK (booking type `1292586`)
- [x] FastAPI skeleton: `/health`, `/slots`, `/chat`, `/book`, `/lead`
- [x] TidyCal client with 409/429 handling, browser User-Agent, Europe/London labels
- [x] Knowledge loader + keyword context (no vector DB)
- [x] Widget (`widget/widget.js`) with slots, booking and human handoff
- [x] WordPress scrape tool (`tools/scrape_site.py`)
- [ ] Create a real booking with your own email (needs your say-so; it emails you)
- [ ] Wire `knowledge/products.md` + `knowledge/ai-audit.md` from reviewed copy
- [ ] Deploy to Coolify at `agent.webawesome.co.uk`
- [ ] Paste widget tag in the WordPress footer
- [ ] Add opencode door: `agents/custom/webawesome-site.md`

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Config + knowledge count |
| GET | `/slots?limit=3` | Next free discovery slots (UK time) |
| POST | `/chat` | `{message}` -> `{reply, slots?}` |
| POST | `/book` | `{name,email,starts_at}` -> booking (409 = slot gone) |
| POST | `/lead` | `{name,email,question}` -> stores + emails Banks |

## Run locally

```sh
cd projects/webawesome-site-agent
python3 -m uvicorn app.main:app --reload --port 8000
```

`.env` at the repo root supplies `TIDYCAL_API_TOKEN` and
`TIDYCAL_BOOKING_TYPE_ID`.

## Test

```sh
cd projects/webawesome-site-agent
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## Knowledge

`knowledge/` is the single source of truth. `tools/scrape_site.py` writes
public WordPress pages and posts into `knowledge/site/`. Hand-written pages
(`products.md`, `ai-audit.md`, `faq.md`) take precedence and are never
overwritten by the scraper.

There is no admin UI and no runtime write API: the container is read-only and
only `/app/data` persists, so knowledge is changed through git.

### Updating knowledge

1. Edit an existing file or add a new `.md` in `knowledge/`. Use a plain title,
   short paragraphs, real links, and the words a customer would search for.
   Hand-written files rank above scraped ones, so put client examples and
   services here rather than in `knowledge/site/`.
2. Optional: refresh the scraped site copy with
   `python3 tools/scrape_site.py` (writes `knowledge/site/`).
3. Check retrieval and answers:
   ```bash
   PYTHONPATH=. python3 -m unittest discover -s tests -v
   PYTHONPATH=. python3 -c "from app.knowledge import search; print([n for n,_ in search('your question')])"
   ```
4. Commit and push. Coolify redeploys and `/health` reports the new
   `knowledge_docs` count. Confirm with the real question you care about.

`knowledge/site/` is generated: safe to delete and regenerate, do not hand-edit.


## TidyCal notes

- Only **free** booking types can be auto-booked; priced types need a 100%-off coupon.
- Requests must send a browser-like `User-Agent`; Cloudflare blocks `Python-urllib`.
- `timeslots` requires `starts_at`/`ends_at`.
- No reschedule endpoint: cancel and rebook.
- Creating a booking emails the booker.

## Deploy to Coolify

This project lives inside the `AIS-OS` repo, so the service needs a **base
directory** or Coolify will build the root Dockerfile instead.

1. **Resources → New → Git Repository**, repo `github.com/banksdada/AIS-OS`,
   branch `main`.
2. **Build Pack: Dockerfile**.
3. **Base Directory: `/projects/webawesome-site-agent`**
   (this is the step people miss).
4. **Dockerfile Location: `/Dockerfile`** (relative to the base directory).
5. **Ports Exposes: `8000`**.
6. **Domains:** `https://agent.webawesome.co.uk`, target port `8000`.
7. **Health Check:** path `/health`, expected `200`.
8. **Environment variables** (Environment tab, never commit them):
   `TIDYCAL_API_TOKEN`, `TIDYCAL_BOOKING_TYPE_ID=1292586`,
   `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o-mini`, `RESEND_API_KEY`,
   `FROM_EMAIL=agent@webawesome.co.uk`, `NOTIFY_EMAIL=bankoledada@gmail.com`,
   `ALLOWED_ORIGINS=https://www.webawesome.co.uk,https://webawesome.co.uk,https://agent.webawesome.co.uk`,
   `HTTP_USER_AGENT=<Chrome UA>`, `DATA_DIR=/app/data`.
9. **Persistent storage:** mount a volume at `/app/data` so `leads.jsonl`
   survives redeploys.
10. Click **Deploy**, then open `https://agent.webawesome.co.uk/health` and
    expect `{"status":"ok","tidycal_configured":true,...}`.

The WordPress embed is one script tag (site footer, once):

```html
<script>window.WebAwesomeAgentConfig={apiBase:"https://agent.webawesome.co.uk"};</script>
<script src="https://agent.webawesome.co.uk/widget.js" defer></script>
```

`/widget.js` is served by the same container, so there is no second host.
`DATA_DIR=/app/data` only works with the volume mounted; without it leads are
lost on every redeploy.
