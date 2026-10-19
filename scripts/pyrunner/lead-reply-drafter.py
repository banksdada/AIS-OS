import os, re, json, datetime, urllib.request as u
import hashlib, hmac, time
from zoneinfo import ZoneInfo

# ---------- AI OS dashboard reporting ----------
# Inlined: PyRunner runs each script standalone, no extra modules available.

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
        req = u.Request(AIOS_WEBHOOK_URL, data=body, headers=headers, method="POST")
        with u.urlopen(req, timeout=20) as resp:
            print("AIOS report sent:", resp.status)
        return True
    except Exception as e:
        print("AIOS report failed:", e)
        return False


P = """You write a DRAFT reply for webawesome.co.uk (a UK web design and AI automation agency) to a website enquiry. A human reviews it first.
Rules: friendly, concise, human. Use details already given; never re-ask them. Ask at most 2 short questions about unknowns. Offer a free 20-minute discovery call; suggest no specific times, ask for 2-3 that suit them. Never invent prices (say pricing depends on scope and is sorted on the free call). Promise no timelines beyond "most projects start within 1-2 weeks". If unsure, say so in PRIORITY.
Output exactly:
PRIORITY: <Hot|Warm|Cold> - <reason>
SUBJECT: <subject>
BODY:
<email, signed The WebAwesome team>"""


def post(url, data, key=None):
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (compatible; WebAwesomeBot/1.0)"}
    if key:
        h["Authorization"] = "Bearer " + key
    return u.urlopen(u.Request(url, json.dumps(data).encode(), h), timeout=90).read().decode()


try:
    e = os.environ
    L = json.loads(e.get("WEBHOOK_BODY_JSON") or "{}")
    print("LEAD:", L)
    report("lead-reply-drafter", "started", L.get("email") or L.get("name") or "enquiry received")
    pr = sub = ""
    ai_error = None
    try:
        r = post(e["AI_BASE_URL"].rstrip("/") + "/chat/completions",
                 {"model": e["AI_MODEL"], "messages": [{"role": "system", "content": P},
                  {"role": "user", "content": "Enquiry:\n" + json.dumps(L)}]}, e["AI_API_KEY"])
        t = json.loads(r)["choices"][0]["message"]["content"]
        t = re.sub(r"```.*?```", "", t, flags=re.S).strip()
        head, _, body = t.partition("BODY:")
        for x in head.splitlines():
            if x.upper().startswith("PRIORITY:"):
                pr = x.split(":", 1)[1].strip()
            if x.upper().startswith("SUBJECT:"):
                sub = x.split(":", 1)[1].strip()
        body = body.strip() or t
    except Exception as ex:
        ai_error = ex
        pr, body = "Check", "AI DRAFT FAILED: %s. Reply by hand." % ex
        print("AI error:", ex, getattr(ex, "read", lambda: b"")()[:300])

    row = {"received": datetime.datetime.now(ZoneInfo("Europe/London")).strftime("%Y-%m-%d %H:%M"),
           "priority": pr, "subject": sub, "draft": body, "status": "Draft"}
    for k in ("name", "email", "business", "service", "timeline", "budget"):
        row[k] = L.get(k, "")
    print("ROW:", json.dumps(row))

    d = e.get("DRAFTS_WEBHOOK_URL")
    draft_posted = False
    if d:
        try:
            print("Drafts tab:", post(d, row)[:100])
            draft_posted = True
        except Exception as ex:
            print("Drafts post failed:", ex)
            report("lead-reply-drafter", "failed", f"drafts webhook failed: {ex} - reply lost, check logs")
    else:
        print("DRAFTS_WEBHOOK_URL not set")

    if ai_error:
        report("lead-reply-drafter", "failed", f"AI draft failed ({ai_error}) - hand-reply draft queued")
    elif not (d and not draft_posted):
        report("lead-reply-drafter", "ok",
               f"{pr or 'no priority'}: {sub or '(no subject)'} - {L.get('email') or L.get('name') or 'lead'}")
except (Exception, SystemExit) as err:
    report("lead-reply-drafter", "failed", str(err))
    raise
