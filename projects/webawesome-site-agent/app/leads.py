from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .config import Settings


def record_lead(
    settings: Settings,
    *,
    name: str,
    email: str,
    question: str,
    kind: str = "human_handoff",
) -> dict[str, object]:
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "name": name,
        "email": email,
        "question": question,
    }

    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / "leads.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    result: dict[str, object] = {"stored": True, "emailed": False, "crm": False}

    if settings.resend_api_key:
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.from_email,
                    "to": [settings.notify_email],
                    "subject": f"New site-agent lead: {name}",
                    "text": f"{name} <{email}>\n\n{question}\n\nSource: {kind}",
                },
                timeout=20.0,
            )
            result["emailed"] = response.is_success
        except httpx.HTTPError:
            result["emailed"] = False

    if settings.crm_webhook_url:
        try:
            response = httpx.post(settings.crm_webhook_url, json=entry, timeout=20.0)
            result["crm"] = response.is_success
        except httpx.HTTPError:
            result["crm"] = False

    return result
