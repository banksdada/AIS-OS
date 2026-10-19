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


# MentoringBA copy of the WebAwesome blog poster.
WP_BASE_URL = "https://mentoringba.org"
# These are SEPARATE secrets from the WebAwesome script, because mentoringba.org
# is a different WordPress site with its own login. Add them on the PyRunner
# Secrets page and grant them to this script (do not paste them into the code).
# The password must be an application password created on mentoringba.org.
WP_USERNAME = os.environ.get("WP_USERNAME_MENTORINGBA")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD_MENTORINGBA")

OPENCODE_API_KEY = os.environ.get("OPENCODE_API_KEY")
# minimax/deepseek/glm/kimi models go through the OpenAI-compatible
# chat/completions endpoint, NOT the Anthropic-style /v1/messages endpoint.
OPENCODE_URL = "https://opencode.ai/zen/v1/chat/completions"
# Kept the same as your working WebAwesome script. Change this name if you
# want a different model.
OPENCODE_MODEL = "minimax-m2.5"

MAX_OUTPUT_TOKENS = 16000
AI_TIMEOUT_SECONDS = 300
AI_ATTEMPTS = 2  # tries per post before giving up

# CHECK THIS: this is the booking link carried over from your WebAwesome script.
# Make sure it is the link you want MentoringBA readers to use.
TIDYCAL_URL = "https://tidycal.com/mentoringba/discovery-call"

# Keyword Google Sheet for MentoringBA (columns: keyword, pattern, notes).
# It must stay shared as "Anyone with the link" (Viewer), and the keywords must
# stay on the FIRST tab.
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1RRcCef2LDtc4tgfUI5hM8TGNC-LMfQHRlK9X3RqVN08/gviz/tq?tqx=out:csv&gid=0"

# Category new posts get filed under. Must already exist on mentoringba.org.
# If it is not found the post is still created, just without this category.
DEFAULT_CATEGORY_NAME = "Insights"

# Separate store so MentoringBA keywords are tracked independently.
DATASTORE_NAME = "mentoringba_blog_processed"

# Status for new posts. "draft" = you review and publish in WordPress.
# Set the POST_STATUS environment variable to "publish" if you want posts to
# go live automatically (no review step).
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
        "User-Agent": "Mozilla/5.0 (compatible; MentoringBAAutomation/1.0)",
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
        headers={"User-Agent": "Mozilla/5.0 (compatible; MentoringBAAutomation/1.0)"},
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
        "User-Agent": "Mozilla/5.0 (compatible; MentoringBAAutomation/1.0)",
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


def build_prompt(pattern, keyword, link_candidates, notes=""):
    links_text = "\n".join(f"- {c['title']} ({c['url']})" for c in link_candidates) or "(none available)"
    today_str = date.today().strftime("%B %Y")
    notes_block = ""
    if notes and notes.strip():
        notes_block = f"""
Real facts/angles from MentoringBA to ground this post in - use these
specifically rather than inventing your own claims about MentoringBA:
{notes.strip()}
"""
    return f"""You are writing a blog post for MentoringBA (mentoringba.org), which
supports people who are changing career into business analysis, with training,
on-the-job support and mentoring. The readers are career changers, often
anxious about breaking into a new field. The goal of this post is to be
genuinely helpful and encourage readers to book a free discovery call.

Today's actual date is {today_str}. If you reference a year anywhere, use the
correct current year based on that date, not an assumed or outdated one.
{notes_block}
STRICT HONESTY RULES (very important - readers act on career advice):
- Do NOT invent statistics, salaries, job-placement rates, pass rates,
  student results, testimonials, accreditations or guarantees.
- Do NOT claim or imply that MentoringBA guarantees a job or a salary.
- Do NOT make claims about MentoringBA beyond what is stated above. If you are
  unsure of a fact, leave it out or keep the claim general and defensible.
- Only cite a statistic if it is a real, widely known, verifiable figure, and
  prefer general statements over precise-sounding numbers.

Keyword pattern: "{pattern}"
Specific keyword/topic: "{keyword}"

Write a complete, genuinely useful blog post (not thin or generic) of
roughly 700-900 words, in a warm, practical, encouraging tone with short
paragraphs, concrete advice and realistic examples. Use British English.
Write for a complete beginner to business analysis.

Existing posts you may link to naturally if relevant (use at most 2-3, only
if genuinely relevant, using proper <a href="URL">anchor text</a> HTML):
{links_text}

End the post with a clear call to action inviting readers to book a free
discovery call at {TIDYCAL_URL} (use an <a href="{TIDYCAL_URL}">...</a> link,
not the bare URL).

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
        parsed["content_html"] = clean_content(parsed["content_html"])
        return parsed

    raise SystemExit(
        f"Could not get a usable post from the AI after {AI_ATTEMPTS} attempt(s). "
        f"Last problem: {last_problem} Nothing was created in WordPress and the "
        "keyword was NOT marked as done, so the next run will try it again."
    )


def check_setup():
    """Stop early with a plain-English message if something is not set up yet."""
    problems = []
    if "PASTE_MENTORINGBA" in SHEET_CSV_URL:
        problems.append("SHEET_CSV_URL is still the placeholder. Paste your MentoringBA keyword sheet's CSV link at the top of the script.")
    if not OPENCODE_API_KEY:
        problems.append("OPENCODE_API_KEY is not set in this script's PyRunner environment variables.")
    if not DRY_RUN and not (WP_USERNAME and WP_APP_PASSWORD):
        problems.append("WP_USERNAME_MENTORINGBA and/or WP_APP_PASSWORD_MENTORINGBA are not set, or are not granted to this script, on the PyRunner Secrets page.")
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

    report("mentoringba-blog-poster", "started", "DRY RUN" if DRY_RUN else f"live ({POST_STATUS})")

    store = DataStore(DATASTORE_NAME)
    processed = load_processed(store)

    rows = fetch_sheet_rows()
    print(f"Fetched {len(rows)} row(s) from the Google Sheet.")
    if not rows:
        print("Nothing to do - no keywords could be read from the sheet (see any PROBLEM line above).")
        report("mentoringba-blog-poster", "failed", "no keywords readable from the Google Sheet")
        return

    pending = [r for r in rows if row_key(r) not in processed]
    if not pending:
        print("No new topics found - every keyword in the sheet has already been generated.")
        print(f"({len(processed)} keyword(s) marked done so far.)")
        report("mentoringba-blog-poster", "idle", f"no new keywords ({len(processed)} done so far)")
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

    if DRY_RUN:
        print("[DRY RUN] Nothing created or changed yet. To go live, set the DRY_RUN")
        print("environment variable to false (or remove it) in this script's PyRunner settings.")
        report("mentoringba-blog-poster", "ok", f"DRY RUN preview generated: {result['title']}")
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
    else:
        print(f"  Warning: couldn't find a '{DEFAULT_CATEGORY_NAME}' category, leaving WordPress default.")

    new_post = wp_post(f"{WP_BASE_URL}/wp-json/wp/v2/posts", post_data)
    print(f"-> Created {POST_STATUS} post {new_post['id']}: {new_post['link']}")

    processed.add(row_key(row))
    save_processed(store, processed)
    print("-> Marked as processed (won't be regenerated on future runs).")
    report("mentoringba-blog-poster", "ok", f"Created {POST_STATUS} post {new_post['id']}: {row['keyword']}")


if __name__ == "__main__":
    try:
        main()
    except (Exception, SystemExit) as e:
        report("mentoringba-blog-poster", "failed", str(e))
        raise
