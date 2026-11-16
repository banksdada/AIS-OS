"""Scrape public WordPress content into knowledge/site/ (read-only).

Run from anywhere:
    python3 projects/webawesome-site-agent/tools/scrape_site.py
"""

from __future__ import annotations

import base64
import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "knowledge" / "site"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TAGS = re.compile(r"<[^>]+>")
BLOCK = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
SPACE = re.compile(r"\s+")


def load_site(name: str = "webawesome") -> dict[str, str]:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("WP_SITES="):
            for site in json.loads(line.split("=", 1)[1]):
                if site.get("name") == name:
                    return site
    raise SystemExit(f"{name} not found in WP_SITES")


def clean(raw: str) -> str:
    text = BLOCK.sub(" ", raw)
    text = TAGS.sub(" ", text)
    return SPACE.sub(" ", html.unescape(text)).strip()


def fetch(site: dict[str, str], kind: str, page: int) -> tuple[list[dict], int]:
    url = (
        f"{site['url'].rstrip('/')}/wp-json/wp/v2/{kind}"
        f"?per_page=100&page={page}&_fields=slug,title,content,link,modified"
    )
    user = site.get("user", "")
    password = site.get("app_password", "").replace(" ", "")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()

    def get(auth: bool) -> tuple[list[dict], int]:
        headers = {"User-Agent": UA, "Accept": "application/json"}
        if auth:
            headers["Authorization"] = f"Basic {token}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode()), int(response.headers.get("X-WP-TotalPages", "1"))

    try:
        return get(bool(user and password))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            return get(False)
        raise


def main() -> None:
    site = load_site()
    total = 0
    for kind in ("pages", "posts"):
        page = 1
        while True:
            items, pages = fetch(site, kind, page)
            for item in items:
                body = clean(item.get("content", {}).get("rendered", ""))
                if not body:
                    continue
                title = clean(item.get("title", {}).get("rendered", "")) or item.get("slug", "untitled")
                slug = item.get("slug") or f"item-{total}"
                folder = OUT / kind
                folder.mkdir(parents=True, exist_ok=True)
                doc = (
                    f"# {title}\n\n"
                    f"Source: {item.get('link', '')}\n"
                    f"Updated: {item.get('modified', '')}\n\n"
                    f"{body}\n"
                )
                (folder / f"{slug}.md").write_text(doc, encoding="utf-8")
                total += 1
            if page >= pages:
                break
            page += 1
    print(f"wrote {total} documents to {OUT}")


if __name__ == "__main__":
    main()
