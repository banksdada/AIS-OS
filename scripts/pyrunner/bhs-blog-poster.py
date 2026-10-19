import os
import re
import csv
import io
import json
import base64
import hashlib
import hmac
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import date
from pyrunner_datastore import DataStore

# ---------- AI OS dashboard reporting ----------
# Inlined so the script has no extra module to import: PyRunner runs each
# script standalone and cannot see a separate aios_report.py file.

AIOS_WEBHOOK_URL = "https://aios.webawesome.co.uk/webhook/pyrunner"


def report(agent, status, message=""):
    """Send one status event to the AI OS dashboard. Never raises."""
    secret = os.environ.get("PYRUNNER_WEBHOOK_SECRET", "")
    if not secret:
        print("AIOS report skipped: PYRUNNER_WEBHOOK_SECRET not set")
        return False
    try:
        data = {"agent": agent, "status": status, "message": str(message)[:500]}
        body = json.dumps(data).encode()
        ts = str(int(time.time()))
        signed = f"{ts}.".encode() + body
        sig = "sha256=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-AIOS-Timestamp": ts,
            "X-AIOS-Signature": sig,
        }
        req = urllib.request.Request(AIOS_WEBHOOK_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("AIOS report sent:", resp.status)
        return True
    except Exception as e:
        print("AIOS report failed:", e)
        return False


# Best Homes Support blog poster (adapted from the MentoringBA / WebAwesome scripts).
WP_BASE_URL = "https://besthomesupport.uk"
# SEPARATE secrets from the other scripts, because besthomesupport.uk is its own
# WordPress site with its own login. Add them on the PyRunner Secrets page and
# grant them to this script (do not paste them into the code).
# The password must be an application password created on besthomesupport.uk.
WP_USERNAME = os.environ.get("WP_USERNAME_BHS")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD_BHS")

OPENCODE_API_KEY = os.environ.get("OPENCODE_API_KEY")
# minimax/deepseek/glm/kimi models go through the OpenAI-compatible
# chat/completions endpoint, NOT the Anthropic-style /v1/messages endpoint.
OPENCODE_URL = "https://opencode.ai/zen/v1/chat/completions"
# Same model as your working scripts. Change the name here if you want another.
OPENCODE_MODEL = "minimax-m2.5"

MAX_OUTPUT_TOKENS = 16000
AI_TIMEOUT_SECONDS = 300
AI_ATTEMPTS = 2  # tries per post before giving up

# Call-to-action links added to the bottom of EVERY post by the script itself
# (not left to the AI), taken from besthomesupport.uk.
REFERRAL_URL = "https://besthomesupport.uk/referral/"
CONTACT_URL = "https://besthomesupport.uk/contact-us/"
PHONE_DISPLAY = "020 8075 5833"
PHONE_TEL = "02080755833"

# Best Homes Support keyword Google Sheet (columns: keyword, pattern, notes).
# It must stay shared as "Anyone with the link" (Viewer), and the keywords must
# stay on the FIRST tab.
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1-OUgnZAQvRXfa_PqZYOwN8Qub8B8vAnD3dHWFengG78/gviz/tq?tqx=out:csv&gid=0"

# Optional: a category that already exists on besthomesupport.uk. Leave as ""
# to use the WordPress default category.
DEFAULT_CATEGORY_NAME = ""

# Separate store so Best Homes Support keywords are tracked independently.
# You must create a data store with exactly this name in the PyRunner UI first.
DATASTORE_NAME = "bhs_blog_processed"

# "draft" = you review and publish in WordPress (recommended for a CQC-regulated
# provider). Set the POST_STATUS environment variable to "publish" to go live
# automatically with no review.
POST_STATUS = os.environ.get("POST_STATUS", "draft").strip().lower()

# DRY_RUN = true  -> generate the post and print a preview only.
# DRY_RUN = false, or not set -> create the post in WordPress and mark the
#                                keyword as done.
DRY_RUN = os.environ.get("DRY_RUN", "false").strip().lower() in ("true", "1", "yes", "on")


# ---------- WordPress helpers ----------

def wp_auth_header():
    token = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "User-Agent": "Mozilla/5.0 (compatible; BHSAutomation/1.0)",
    }


def wp_get(url):
    req = urllib.request.Request(url, headers=wp_auth_header())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def wp_post(url, data):
    payload = json.dumps(data).encode()
    headers = wp_auth_header()
    headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_link_candidates(limit=15):
    """Pull recent published post titles + URLs to offer the model as internal
    link options, so generated posts can link to real existing content."""
    url = f"{WP_BASE_URL}/wp-json/wp/v2/posts?per_page={limit}&status=publish&_fields=id,title,link"
    try:
        posts = wp_get(url)
    except urllib.error.HTTPError as e:
        print(f"  Warning: could not fetch link candidates ({e.code}), continuing without them.")
        return []
    return [{"title": p["title"]["rendered"], "url": p["link"]} for p in posts]


def get_category_id(name):
    if not name:
        return None
    url = f"{WP_BASE_URL}/wp-json/wp/v2/categories?search={urllib.parse.quote(name)}"
    try:
        results = wp_get(url)
    except urllib.error.HTTPError as e:
        print(f"  Warning: could not look up category '{name}' ({e.code}).")
        return None
    for c in results:
        if c["name"].lower() == name.lower():
            return c["id"]
    return results[0]["id"] if results else None


# ---------- Google Sheet queue ----------

def fetch_sheet_rows():
    req = urllib.request.Request(
        SHEET_CSV_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BHSAutomation/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8-sig")

    if "<html" in raw[:2000].lower():
        print("PROBLEM: Google returned a web page instead of the sheet's data.")
        print("The sheet is probably not shared as 'Anyone with the link' (Viewer).")
        return []

    reader = csv.DictReader(io.StringIO(raw))
    headers = [(h or "").strip() for h in (reader.fieldnames or [])]
    print(f"Sheet columns found in row 1: {headers}")
    if "keyword" not in [h.lower() for h in headers]:
        print("PROBLEM: no column named 'keyword' in row 1 of the sheet's first tab.")
        return []

    # Headers are matched in any capitalisation (Keyword / keyword / KEYWORD).
    rows = []
    for row in reader:
        clean = {
            (k or "").strip().lower(): (v.strip() if isinstance(v, str) else "")
            for k, v in row.items()
        }
        if clean.get("keyword"):
            rows.append({
                "pattern": clean.get("pattern", ""),
                "keyword": clean["keyword"],
                "notes": clean.get("notes", ""),
            })
    return rows


def row_key(row):
    """Identify a sheet row by pattern + keyword, so the same keyword can be
    used under different patterns without being skipped as 'already done'."""
    return f"{row['pattern']}|{row['keyword']}"


def load_processed(store):
    raw = store.get("processed_keywords", default=None)
    if not raw:
        return set()
    return set(json.loads(raw))


def save_processed(store, processed_set):
    store["processed_keywords"] = json.dumps(sorted(processed_set))


# ---------- OpenCode Zen call ----------

class AIReplyProblem(Exception):
    """The AI answered, but the answer can't be used (cut off, empty, bad format)."""


def call_ai(prompt):
    headers = {
        "Authorization": f"Bearer {OPENCODE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; BHSAutomation/1.0)",
    }
    body = {
        "model": OPENCODE_MODEL,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        OPENCODE_URL, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=AI_TIMEOUT_SECONDS) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="replace")
        print(f"OpenCode Zen HTTP Error {e.code}: {error_body}")
        raise

    try:
        choice = result["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError):
        print("Unexpected response shape from OpenCode Zen. Full response was:")
        print(json.dumps(result, indent=2))
        raise

    if choice.get("finish_reason") == "length":
        raise AIReplyProblem(
            f"The AI's reply was cut off because it reached the {MAX_OUTPUT_TOKENS}-token "
            "limit before finishing the post. Raise MAX_OUTPUT_TOKENS at the top of the script."
        )
    if not content or not content.strip():
        raise AIReplyProblem("The AI returned an empty reply.")
    return content


def parse_ai_json(raw):
    """Turn the AI's reply into a dict, tolerating the usual ways models
    wrap or bend JSON: thinking blocks, markdown code fences, text before or
    after the object, and real line breaks inside the HTML string."""
    text = re.sub(r"```.*?```", "", raw, flags=re.DOTALL).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise AIReplyProblem("The AI's reply did not contain a complete JSON object (it was probably cut off).")
    try:
        parsed = json.loads(text[start:end + 1], strict=False)
    except json.JSONDecodeError as e:
        raise AIReplyProblem(f"The AI's reply was not valid JSON ({e}).")
    if not isinstance(parsed, dict):
        raise AIReplyProblem("The AI's reply was JSON but not the expected object.")
    missing = [k for k in ("title", "content_html", "excerpt") if not parsed.get(k)]
    if missing:
        raise AIReplyProblem(f"The AI's reply was missing: {', '.join(missing)}.")
    return parsed


# ---------- Content generation ----------

def clean_content(html):
    """Strip stray malformed tags the model occasionally produces (e.g. a
    literal "<n>" where it meant a paragraph break) instead of valid HTML."""
    html = re.sub(r"</?n\s*/?>", "", html)
    return html


def cta_html():
    """The call to action added to the end of EVERY post by the script."""
    return f"""
<hr />
<h2>Make a referral or get in touch</h2>
<p>If you are a social worker, health professional or housing professional, you can <a href="{REFERRAL_URL}">make a professional referral</a> to Best Homes Support. If you are a family member, or you are looking for support for yourself, you can <a href="{CONTACT_URL}">contact our team</a> or call us on <a href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>.</p>
<p><em>This article is general information only. It is not clinical, legal or financial advice.</em></p>
"""


def build_prompt(pattern, keyword, link_candidates, notes=""):
    links_text = "\n".join(f"- {c['title']} ({c['url']})" for c in link_candidates) or "(none available)"
    today_str = date.today().strftime("%B %Y")
    notes_block = ""
    if notes and notes.strip():
        notes_block = f"""
Extra facts or angles supplied by Best Homes Support for this topic (you may
use these, they are true):
{notes.strip()}
"""
    return f"""You are writing a blog post for Best Homes Support Limited
(besthomesupport.uk), a CQC-registered care provider in London.

THE ONLY FACTS YOU KNOW ABOUT THE COMPANY (do not add to them):
- It is registered with the Care Quality Commission (CQC).
- It currently operates in Bromley, Lewisham and Southwark. Enquiries are
  welcomed from across London.
- Its services are home care, supported living, live-in care, complex care,
  respite care, and mental health and autism support. It also supports people
  with learning disabilities and ADHD.
- It works in a person-centred way: it listens first and builds a plan around
  the individual, with regular reviews.
- It has a professional referral route for health, social care and housing
  professionals.
{notes_block}
WHO THE POST IS FOR:
Mainly social workers, health professionals and housing professionals who are
considering referring someone for care or support. Families and individuals
may also read it. Write in a professional, clear, respectful tone that a busy
social worker would find useful, not salesy. Use British English.

AREA RULES (important):
- Bromley, Lewisham and Southwark are the boroughs the company CURRENTLY
  operates in.
- For any other London borough or area (for example Croydon, Greenwich,
  Lambeth, Bexley), NEVER say or imply the company currently provides care
  there. Say only that enquiries are welcomed from across London and that
  availability should be confirmed with the team.
- Do NOT invent local details (named council teams, hospitals, panels,
  commissioning arrangements or local services). Keep local references
  general, for example "local authority adult social care teams".

STRICT HONESTY AND COMPLIANCE RULES (this is a regulated care provider, and
readers make decisions about vulnerable people):
- Do NOT state or imply a CQC rating (such as Good or Outstanding), inspection
  outcome, award or accreditation. Only say the company is CQC registered.
- Do NOT invent statistics, outcomes, case studies, testimonials, service-user
  stories, staff numbers, response times, prices, funding eligibility or
  guarantees of availability.
- Do NOT claim the company is on a council framework, is commissioned by a
  named council, or works with a named NHS body.
- Do NOT give clinical, medical, legal or safeguarding advice. Where relevant,
  refer readers to the appropriate professional or statutory route.
- Refer to laws, statutory processes and national bodies only in general,
  well-established terms. If you are not certain a detail is correct, leave it
  out. Do not state thresholds, timescales or eligibility rules.
- Never include any personal information about real people.
- Today's date is {today_str}. If you mention a year, use the correct one.

Keyword pattern: "{pattern}"
Specific keyword/topic: "{keyword}"

Write a complete, genuinely useful blog post (not thin or generic) of roughly
700-900 words, with a clear structure, short paragraphs and practical points
a professional can use. The post must make sense and read naturally on its own.
Do NOT include a call to action, contact details or a list of services: a call
to action is added to every post automatically after your text.

Existing posts you may link to naturally if relevant (use at most 2-3, only
if genuinely relevant, using proper <a href="URL">anchor text</a> HTML):
{links_text}

Respond with ONLY a JSON object (no markdown fences, no commentary before or
after), with exactly these keys:
{{
  "title": "the post title",
  "content_html": "the full post body as WordPress-ready HTML (use <p>, <h2>, <ul>/<li>, <strong> as appropriate; no <h1>, WordPress adds the title separately)",
  "excerpt": "a 1-2 sentence excerpt/summary, plain text, no HTML"
}}"""


def generate_post(pattern, keyword, notes=""):
    link_candidates = fetch_link_candidates()
    prompt = build_prompt(pattern, keyword, link_candidates, notes)

    last_problem = None
    for attempt in range(1, AI_ATTEMPTS + 1):
        raw_response = ""
        try:
            raw_response = call_ai(prompt)
            parsed = parse_ai_json(raw_response)
        except AIReplyProblem as problem:
            last_problem = problem
            print(f"  Attempt {attempt} of {AI_ATTEMPTS} failed: {problem}")
            if raw_response:
                print("  The reply ended with: ..." + raw_response[-300:])
            continue
        parsed["content_html"] = clean_content(parsed["content_html"]) + cta_html()
        return parsed

    raise SystemExit(
        f"Could not get a usable post from the AI after {AI_ATTEMPTS} attempt(s). "
        f"Last problem: {last_problem} Nothing was created in WordPress and the "
        "keyword was NOT marked as done, so the next run will try it again."
    )


def check_setup():
    """Stop early with a plain-English message if something is not set up yet."""
    problems = []
    if "PASTE_BHS" in SHEET_CSV_URL:
        problems.append("SHEET_CSV_URL is still the placeholder. Paste your Best Homes Support keyword sheet link at the top of the script.")
    if not OPENCODE_API_KEY:
        problems.append("OPENCODE_API_KEY is not set, or is not granted to this script, in PyRunner.")
    if not DRY_RUN and not (WP_USERNAME and WP_APP_PASSWORD):
        problems.append("WP_USERNAME_BHS and/or WP_APP_PASSWORD_BHS are not set, or are not granted to this script, on the PyRunner Secrets page.")
    if problems:
        print("SETUP PROBLEM(S) - nothing was done:")
        for p in problems:
            print(f"  - {p}")
        raise SystemExit(1)


def main():
    check_setup()

    if DRY_RUN:
        print("MODE: DRY RUN - preview only, nothing will be created in WordPress.")
    else:
        print(f"MODE: LIVE - a '{POST_STATUS}' post will be created in WordPress.")

    report("bhs-blog-poster", "started", "DRY RUN" if DRY_RUN else f"live ({POST_STATUS})")

    store = DataStore(DATASTORE_NAME)
    processed = load_processed(store)

    rows = fetch_sheet_rows()
    print(f"Fetched {len(rows)} row(s) from the Google Sheet.")
    if not rows:
        print("Nothing to do - no keywords could be read from the sheet (see any PROBLEM line above).")
        report("bhs-blog-poster", "failed", "no keywords readable from the Google Sheet")
        return

    pending = [r for r in rows if row_key(r) not in processed]
    if not pending:
        print("No new topics found - every keyword in the sheet has already been generated.")
        print(f"({len(processed)} keyword(s) marked done so far.)")
        report("bhs-blog-poster", "idle", f"no new keywords ({len(processed)} done so far)")
        return

    row = pending[0]
    print(f"{len(pending)} keyword(s) still to do.")
    print(f'Generating post for keyword: "{row["keyword"]}" (pattern: {row["pattern"]})')
    if row["notes"]:
        print(f"Using notes: {row['notes']}")
    print()

    result = generate_post(row["pattern"], row["keyword"], row["notes"])

    print(f"Title: {result['title']}")
    print(f"Excerpt: {result['excerpt']}")
    print(f"Length: about {len(re.sub(r'<[^>]+>', ' ', result['content_html']).split())} words")
    print()
    print("--- Content preview (first 500 chars) ---")
    print(result["content_html"][:500] + "...")
    print()
    print("--- Call to action added to the end of the post ---")
    print(cta_html().strip())
    print()

    if DRY_RUN:
        print("[DRY RUN] Nothing created or changed yet. To go live, set the DRY_RUN")
        print("environment variable to false (or remove it) in this script's PyRunner settings.")
        report("bhs-blog-poster", "ok", f"DRY RUN preview generated: {result['title']}")
        return

    category_id = get_category_id(DEFAULT_CATEGORY_NAME)
    post_data = {
        "title": result["title"],
        "content": result["content_html"],
        "excerpt": result["excerpt"],
        "status": POST_STATUS,
    }
    if category_id:
        post_data["categories"] = [category_id]
    elif DEFAULT_CATEGORY_NAME:
        print(f"  Warning: couldn't find a '{DEFAULT_CATEGORY_NAME}' category, leaving WordPress default.")

    new_post = wp_post(f"{WP_BASE_URL}/wp-json/wp/v2/posts", post_data)
    print(f"-> Created {POST_STATUS} post {new_post['id']}: {new_post['link']}")

    processed.add(row_key(row))
    save_processed(store, processed)
    print("-> Marked as processed (won't be regenerated on future runs).")
    report("bhs-blog-poster", "ok", f"Created {POST_STATUS} post {new_post['id']}: {row['keyword']}")


if __name__ == "__main__":
    try:
        main()
    except (Exception, SystemExit) as e:
        report("bhs-blog-poster", "failed", str(e))
        raise
