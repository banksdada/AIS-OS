#!/usr/bin/env python3
"""Cloud job campaign for Banks and Adenike — standalone, stdlib + google-auth.

Fetches recent listings from Reed's public RSS feed, builds a markdown sweep and
appends it to the existing Google Docs. Runs inside the AIOS Coolify container
or PyRunner; no local CLI, no Mac, no agent runtime.
"""
import argparse
import datetime
import hashlib
import hmac
import json
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BANKS_DOC = "1-4BI6Si7Eu8ZeDhg77330rQ4OGCKQtb8pyNzuwTRAqU"
ADENIKE_DOC = "1rxCmMTAC8yB9spaIY-qDZ7fsZUM1mDxkGibdBzIq-oU"
WEBHOOK = "https://aios.webawesome.co.uk/webhook/pyrunner"
UA = "AI-OS-Dashboard/1.0"
ATOM = "{http://www.w3.org/2005/Atom}updated"

FEEDS = {
    "banks": [
        ("business analyst", "United Kingdom", ("analyst", "business transformation", "product owner", "product manager")),
        ("product owner", "United Kingdom", ("product owner", "product manager", "business analyst")),
        ("business transformation", "United Kingdom", ("transformation", "business analyst", "product owner")),
    ],
    "adenike": [
        ("SEN teacher", "Wigan", ("sen", "send", "teacher")),
        ("SEND teacher", "Wigan", ("sen", "send", "teacher")),
        ("SEMH teacher", "Manchester", ("semh", "sen", "teacher")),
    ],
}

EXCLUDE = {
    "banks": ("contract", "contractor", "consultant hourly", "hourly rate"),
    "adenike": ("assistant", "tutor", "nursery", "cover supervisor", "hod", "head of department"),
}


def token_for_docs():
    path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "/app/scripts/credentials.json")
    if not pathlib.Path(path).exists():
        path = str(pathlib.Path(__file__).resolve().parents[1] / "credentials.json")
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(
            path, scopes=["https://www.googleapis.com/auth/documents"])
        creds.refresh(Request())
        return creds.token
    except ImportError:
        import base64
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        sa = json.load(open(path))

        def b64(data):
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
        now = int(time.time())
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {"iss": sa["client_email"], "scope": "https://www.googleapis.com/auth/documents",
                   "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600}
        signing_input = b64(json.dumps(header, separators=(",", ":")).encode()) + "." + b64(
            json.dumps(payload, separators=(",", ":")).encode())
        key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
        signature = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
        body = urllib.parse.urlencode({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signing_input + "." + b64(signature)}).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["access_token"]


def docs_api(token, doc_id, body=None):
    url = f"https://docs.googleapis.com/v1/documents/{doc_id}" + (":batchUpdate" if body else "")
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method="POST" if body else "GET", headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def append_doc(doc_id, text):
    token = token_for_docs()
    doc = docs_api(token, doc_id)
    end = max((b.get("endIndex", 0) for b in doc.get("body", {}).get("content", [])), default=0)
    if end <= 1:
        requests = [
            {"insertText": {"location": {"index": 0}, "text": "\n"}},
            {"insertText": {"location": {"index": 1}, "text": text}}]
    else:
        requests = [
            {"insertText": {"location": {"index": end - 1}, "text": "\n"}},
            {"insertText": {"location": {"index": end}, "text": text}}]
    docs_api(token, doc_id, {"requests": requests})


def report(agent, status, message):
    secret = os.environ.get("PYRUNNER_WEBHOOK_SECRET", "")
    if not secret:
        return
    try:
        body = json.dumps({"agent": agent, "status": status, "message": str(message)[:400]}).encode()
        ts = str(int(time.time()))
        sig = "sha256=" + hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        req = urllib.request.Request(WEBHOOK, data=body, method="POST", headers={
            "Content-Type": "application/json", "X-AIOS-Timestamp": ts, "X-AIOS-Signature": sig})
        urllib.request.urlopen(req, timeout=20).close()
    except Exception as exc:
        print("webhook report failed:", exc, file=sys.stderr)


def fetch_feed(keywords, location):
    url = "https://www.reed.co.uk/jobs/rss?" + urllib.parse.urlencode(
        {"keywords": keywords, "location": location})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
    out = []
    for item in root.findall(".//item"):
        def text(tag):
            node = item.find(tag)
            return (node.text or "").strip() if node is not None else ""
        desc = text("description")
        salary = ""
        m = re.search(r"(?:£|\$)\s?[\d,]+(?:\.\d+)?\s?(?:-|to|–)\s?(?:£|\$)?\s?[\d,]+(?:\s?(?:per|p\.?a\.?|a year|annum))?", desc, re.I)
        if m:
            salary = m.group(0)
        updated = text(ATOM) or text("pubDate")
        out.append({
            "guid": text("guid"), "title": text("title"), "link": text("link"),
            "description": re.sub(r"<[^>]+>", " ", desc)[:240], "salary": salary or "Not stated",
            "updated": updated[:10], "location": location,
        })
    return out


def sweep(who, days=7):
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    seen, jobs = set(), []
    for keywords, location, _ in FEEDS[who]:
        try:
            items = fetch_feed(keywords, location)
        except Exception as exc:
            print(f"feed failed ({keywords}): {exc}", file=sys.stderr)
            continue
        for job in items:
            if job["guid"] in seen:
                continue
            seen.add(job["guid"])
            low = (job["title"] + " " + job["description"]).lower()
            if any(word in low for word in EXCLUDE[who]):
                continue
            try:
                if datetime.date.fromisoformat(job["updated"]) < cutoff:
                    continue
            except ValueError:
                pass
            jobs.append(job)
    return jobs[:12]


def fit_note(who, job):
    low = job["description"].lower()
    if who == "banks":
        hits = [name for word, name in [
            ("discovery", "discovery"), ("stakeholder", "stakeholder work"),
            ("agile", "agile delivery"), ("azure", "Azure"), ("salesforce", "Salesforce"),
            ("dynamics", "Dynamics 365"), ("ai", "AI/automation")] if word in low]
        return "Matches: " + ", ".join(hits[:3]) + "." if hits else "Role fits the BA/Product profile; check the ad for specifics."
    hits = [name for word, name in [
        ("autism", "autism provision"), ("semh", "SEMH"), ("behaviour", "behaviour"),
        ("sensory", "sensory"), ("qts", "QTS"), ("sen", "SEN")] if word in low]
    return "Matches: " + ", ".join(hits[:3]) + "." if hits else "SEN/SEND setting; confirm phase and travel."


def markdown(who, jobs):
    title = "Banks job sweep" if who == "banks" else "Adenike SEN job sweep"
    lines = [f"# {title} — {datetime.datetime.now():%Y-%m-%d %H:%M}", "",
             f"{len(jobs)} recent listings from Reed's public feed. Salary and dates are as stated in the ad.", "",
             "| Title | Company/location | Salary | Posted | URL | Fit note | Verdict |",
             "|---|---|---|---|---|---|---|"]
    for job in jobs:
        company = "Reed listing"
        verdict = "Consider"
        if who == "adenike":
            verdict = "Verify travel"
        elif job["salary"] != "Not stated":
            verdict = "Apply"
        lines.append("| " + " | ".join([
            job["title"].replace("|", "-"), company + " / " + job["location"], job["salary"],
            job["updated"], job["link"], fit_note(who, job).replace("|", "-"), verdict]) + " |")
    lines += ["", "## Notes", "",
              "Deduped by listing ID; excluded obvious mismatches (contract roles for Banks, "
              "assistant/tutor roles for Adenike). Adenike's public-transport journey from WN3 6NQ "
              "must still be checked against the 45-minute cap before applying."]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--who", choices=["banks", "adenike", "both"], default="both")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    agent = "job-campaign"
    report(agent, "started", f"who={args.who}")
    try:
        for who in (["banks", "adenike"] if args.who == "both" else [args.who]):
            jobs = sweep(who)
            text = markdown(who, jobs)
            if args.dry_run:
                print(text)
                continue
            append_doc(BANKS_DOC if who == "banks" else ADENIKE_DOC,
                       f"\n\n---\n**{'Banks job sweep' if who == 'banks' else 'Adenike SEN job sweep'} — "
                       f"{datetime.datetime.now():%Y-%m-%d %H:%M}**\n\n{text}\n")
            print(f"{who}: {len(jobs)} roles appended to Google Doc")
        report(agent, "ok", f"who={args.who}")
    except Exception as exc:
        report(agent, "failed", str(exc))
        raise


if __name__ == "__main__":
    main()
