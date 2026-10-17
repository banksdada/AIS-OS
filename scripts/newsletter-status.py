#!/usr/bin/env python3
"""
Newsletter project status probe for AI OS.

Scans /Users/banksdada/Desktop/newsletter-project for:
- Rendered email builds in .tmp/newsletter/
- Content JSON files
- Recipient lists and send logs
- SMTP / environment configuration status

Outputs JSON for the AI OS dashboard pipeline.
"""
import json
import os
import sys
from glob import glob
from pathlib import Path

NEWSLETTER_DIR = Path("/Users/banksdada/Desktop/newsletter-project")


def get_newsletter_status():
    if not NEWSLETTER_DIR.exists():
        return {
            "configured": False,
            "detail": f"newsletter-project directory not found at {NEWSLETTER_DIR}"
        }

    tmp_dir = NEWSLETTER_DIR / ".tmp" / "newsletter"
    html_files = sorted(glob(str(tmp_dir / "*.html")), key=os.path.getmtime, reverse=True)
    content_files = sorted(glob(str(tmp_dir / "content-*.json")), key=os.path.getmtime, reverse=True)
    log_files = sorted(glob(str(tmp_dir / "send-log-*.csv")), key=os.path.getmtime, reverse=True)
    recipients_file = tmp_dir / "recipients.txt"

    # Check env config
    env_file = NEWSLETTER_DIR / ".env"
    env_configured = False
    if env_file.exists():
        text = env_file.read_text(encoding="utf-8")
        if any(line.strip() and not line.strip().startswith("#") for line in text.splitlines()):
            env_configured = True

    latest_build = None
    if html_files:
        path = Path(html_files[0])
        stat = path.stat()
        latest_build = {
            "file": path.name,
            "path": str(path),
            "sizeKb": stat.st_size // 1024,
            "modified": __import__("datetime").datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        }

    latest_campaign = None
    if content_files:
        try:
            with open(content_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
                meta = data.get("meta", {})
                latest_campaign = {
                    "campaign": meta.get("campaign", "unknown"),
                    "subject": meta.get("subject", "(no subject)"),
                    "preheader": meta.get("preheader", "")
                }
        except Exception:
            pass

    recipient_count = 0
    if recipients_file.exists():
        try:
            lines = [l.strip() for l in recipients_file.read_text(encoding="utf-8").splitlines()]
            recipient_count = len([l for l in lines if l and not l.startswith("#")])
        except Exception:
            pass

    return {
        "configured": True,
        "envConfigured": env_configured,
        "latestBuild": latest_build,
        "latestCampaign": latest_campaign,
        "buildCount": len(html_files),
        "recipientCount": recipient_count,
        "lastSendLog": Path(log_files[0]).name if log_files else None,
        "projectPath": str(NEWSLETTER_DIR)
    }


if __name__ == "__main__":
    print(json.dumps(get_newsletter_status(), indent=2))
