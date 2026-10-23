#!/usr/bin/env python3
"""
Website Health Check
====================

Probes a single site for uptime, SSL, WordPress activity, plugin updates,
backups, and a short performance sample.  The output is a JSON structure
used by the reminder script and optionally a PDF that gets attached to
the renewal email.

The module is intentionally stdlib‑only so it can run in PyRunner where
`requests` is not guaranteed to be installed.

Use:
    python3 health_check.py https://example.com [--pdf]
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """One line of the report. ``verified`` distinguishes a real
    measurement from an assumption – the report prints both differently."""

    label: str
    status: str          # "ok" | "warn" | "unknown"
    detail: str
    verified: bool = True

    @property
    def icon(self) -> str:
        return {"ok": "✓", "warn": "!", "unknown": "?"}[self.status]


@dataclass
class HealthReport:
    site_url: str
    generated_at: datetime
    checks: list[CheckResult] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def add(self, label: str, status: str, detail: str, verified: bool = True) -> None:
        self.checks.append(CheckResult(label, status, detail, verified))

    def reachability(self) -> Optional[CheckResult]:
        return next((c for c in self.checks if c.label == "Site reachable"), None)

# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only, same User‑Agent your browser uses)
# ---------------------------------------------------------------------------

_USER_AGENT = "Mozilla/5.0 (compatible; WebawesomeHealthCheck/1.0)"
_TIMEOUT = 15  # seconds


def _http_get(url: str, headers: Optional[dict] = None, timeout: int = _TIMEOUT) -> tuple[int, bytes, dict]:
    req_headers = {"User-Agent": _USER_AGENT, "Accept": "*/*"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read(), dict(resp.headers.items())


def _http_get_json(url: str, headers: Optional[dict] = None):
    status, body, _ = _http_get(url, headers)
    try:
        return status, json.loads(body.decode("utf-8")), {}
    except json.JSONDecodeError:
        return status, None, {}

# ---------------------------------------------------------------------------
# WordPress auth handling (mirrors dashboard/generate.py)
# ---------------------------------------------------------------------------

def load_wp_auth(site_url: str) -> Optional[tuple[str, str]]:
    raw = os.environ.get("WP_SITES", "").strip()
    if not raw:
        return None
    try:
        sites = json.loads(raw)
    except json.JSONDecodeError:
        return None
    normalised = site_url.rstrip("/")
    for s in sites:
        if s.get("url", "").rstrip("/") == normalised:
            user = s.get("user", "")
            pw = s.get("app_password", "")
            return (user, pw) if user and pw else None
    return None


def _basic_header(user: str, pw: str) -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": "Basic " + token}

# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_reachable(report: HealthReport) -> None:
    try:
        t0 = time.monotonic()
        status, body, _ = _http_get(report.site_url + "/")
        ms = int((time.monotonic() - t0) * 1000)
    except urllib.error.URLError as exc:
        report.add("Site reachable", "warn",
                   f"Could not connect — {exc}. Check DNS, SSL, or that the site is online.", verified=True)
        return
    except Exception as exc:
        report.add("Site reachable", "warn", f"Check failed: {exc}", verified=True)
        return

    if status >= 400:
        report.add("Site reachable", "warn",
                   f"Server responded with HTTP {status} — visitors see an error page.", verified=True)
    else:
        report.add("Site reachable", "ok",
                   f"Up — HTTP {status} in {ms} ms on the check date.", verified=True)


def check_ssl(report: HealthReport) -> None:
    host = urllib.parse.urlparse(report.site_url).hostname
    if not host:
        report.add("SSL certificate", "unknown", "Could not parse hostname.", verified=False)
        return
    ctx = ssl.create_default_context()
    try:
        with ctx.wrap_socket(ssl.create_connection((host, 443), timeout=_TIMEOUT), server_hostname=host) as s:
            cert = s.getpeercert()
    except ssl.SSLError as exc:
        report.add("SSL certificate", "warn",
                   f"TLS handshake failed – {exc}. Visitors get a security error.", verified=True)
        return
    except Exception as exc:
        report.add("SSL certificate", "unknown", f"Could not check: {exc}", verified=False)
        return

    not_after = cert.get("notAfter") if cert else None
    if not not_after:
        report.add("SSL certificate", "unknown", "Certificate present but expiry unreadable.", verified=False)
        return
    try:
        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        report.add("SSL certificate", "unknown", f"Unparsed expiry: {not_after}", verified=False)
        return

    days = (expiry - datetime.now(timezone.utc)).days
    if days < 0:
        report.add("SSL certificate", "warn",
                   f"EXPIRED {abs(days)} day(s) ago ({expiry.date()}) — visitors see a broken padlock.", verified=True)
    elif days <= 30:
        report.add("SSL certificate", "warn",
                   f"Expires in {days} day(s) ({expiry.date()}) — renew before it lapses.", verified=True)
    else:
        report.add("SSL certificate", "ok",
                   f"Valid — expires {expiry.date()}.", verified=True)


def check_wordpress(report: HealthReport, auth: Optional[tuple[str, str]] = None) -> None:
    api = report.site_url.rstrip("/") + "/wp-json/wp/v2"

    # ---- post activity (public) -------------------------------------------
    year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    params = urllib.parse.urlencode({"after": year_ago.strftime("%Y-%m-%dT%H:%M:%S%z"), "per_page": "1"})
    try:
        status, posts, hdrs = _http_get_json(f"{api}/posts?{params}")
    except urllib.error.URLError as exc:
        report.add("WordPress activity", "unknown", f"REST API unreachable ({exc}) — is this a WordPress site?", verified=False)
        return
    except Exception:
        report.add("WordPress activity", "unknown", "Could not connect to REST API.", verified=False)
        return

    if status != 200 or not isinstance(posts, list):
        report.add("WordPress activity", "unknown", f"REST API returned HTTP {status}.", verified=False)
        return

    total_in_year = int(hdrs.get("X-WP-Total", "0"))
    if total_in_year:
        report.add("Content this year", "ok",
                   f"{total_in_year} post(s) published in the last 12 months – indicates ongoing maintenance.", verified=True)
    else:
        report.add("Content this year", "warn",
                   "No posts in the last 12 months – an owner may see the site as idle.", verified=True)

    # latest post
    try:
        status, latest, _ = _http_get_json(f"{api}/posts?per_page=1")
        if isinstance(latest, list) and latest:
            published = latest[0].get("date", "")
            report.add("Latest post", "ok" if published else "unknown",
                       f"Most recent post: {published[:10] or 'never published'}.", verified=bool(published))
    except urllib.error.URLError:
        pass

    # WordPress version from meta (best effort)
    try:
        status, body, _ = _http_get(report.site_url + "/")
        html = body.decode("utf-8", errors="replace")
        import re
        m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']WordPress ([^"\']+)', html)
        if m:
            report.add("WordPress version", "ok", f"WordPress {m.group(1)}.", verified=True)
    except urllib.error.URLError:
        report.add("WordPress version", "unknown", "Could not read the version.", verified=False)

    # plugin updates needs auth
    if not auth:
        report.add("Plugin updates", "unknown",
                   "Not checked — an Application Password (WP_SITES) would be needed.", verified=False)
        return
    try:
        status, plugins, _ = _http_get_json(f"{api}/plugins?per_page=100", headers=_basic_header(*auth))
    except urllib.error.URLError as exc:
        report.add("Plugin updates", "unknown", f"Could not read plugins: {exc}", verified=False)
        return
    if status != 200 or not isinstance(plugins, list):
        report.add("Plugin updates", "unknown", f"Plugin API returned HTTP {status}.", verified=False)
        return
    behind = [p for p in plugins if isinstance(p, dict) and p.get("update") and p["update"].get("latest") != p.get("version")]
    if behind:
        names = ", ".join(p.get("name", "?") for p in behind[:4])
        report.add("Plugin updates", "warn", f"{len(behind)} plugin(s) behind on updates ({names}).", verified=True)
    else:
        report.add("Plugin updates", "ok", f"{len(plugins)} plugin(s) checked, all current.", verified=True)


def check_backups(report: HealthReport) -> None:
    report.add("Backups", "unknown",
               "ecoWebhosting runs JetBackup, but there is no API to read the last backup date. This is stated intentionally.", verified=False)


def check_performance(report: HealthReport) -> None:
    r = report.reachability()
    if not r or r.status != "ok":
        report.add("Performance", "unknown", "No timing data – site not reachable.", verified=False)
        return
    import re
    m = re.search(r"(\d+) ms", r.detail)
    if not m:
        report.add("Performance", "unknown", "No timing data found.", verified=False)
        return
    ms = int(m.group(1))
    if ms > 3000:
        report.add("Performance", "warn", f"{ms} ms load – slow.", verified=True)
    else:
        report.add("Performance", "ok", f"{ms} ms load – acceptable. (Single sample.)", verified=True)


def build_recommendations(report: HealthReport) -> None:
    for c in report.checks:
        if c.label == "SSL certificate" and c.status == "warn":
            report.recommendations.append(
                "Renew SSL before expiry – a broken padlock costs visitors.")
        if c.label == "Plugin updates" and c.status == "warn":
            report.recommendations.append(
                "Update out-of-date plugins – security risk.")
        if c.label == "Content this year" and c.status == "warn":
            report.recommendations.append(
                "Publish content to keep the site alive and give renewal reason.")
        if c.label == "Site reachable" and c.status == "warn":
            report.recommendations.append(
                "Investigate downtime – an offline site loses renewal.")
        if c.label == "Backups" and c.status == "unknown":
            report.recommendations.append(
                "Confirm backup status in control panel – test a restore."
            )

# ---------------------------------------------------------------------------
# Rendering – only simple HTML suitable for email; PDF also
# ---------------------------------------------------------------------------

def render_html(report: HealthReport) -> str:
    rows = "\n".join(
        f"<tr><td>{c.icon}</td><td>{c.label}</td><td>{c.detail}</td>"
        f"<td>{'Verified' if c.verified else 'Not independently verified'}</td></tr>"
        for c in report.checks
    )
    recs = "".join(f"<li>{r}</li>" for r in report.recommendations) or "<li>None.</li>"
    return f"""
<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>Website Health Report – {report.site_url}</title>
<style>
  body{{font-family:Arial,Helvetica,sans-serif;margin:1rem;color:#222;}}
table{{border-collapse:collapse;width:100%;margin-top:.5rem;}}
 th,td{{border:1px solid #ddd;padding:.4rem;text-align:left;}}
 th{{background:#f0f0f0;}}
 .ok{{color:#257e30;}}
 .warn{{color:#c35000;}}
 .unknown{{color:#666;}}
</style>
</head>
<body>
<h1>Website Health Report</h1>
<p><strong>Site:</strong> {report.site_url}<br>
<strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
<h2>Checks</h2>
<table>
<tr><th></th><th>Check</th><th>Result</th><th>Confidence</th></tr>
{rows}
</table>
<h2>Recommendations</h2>
<ul>{recs}</ul>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def health_check(site_url: str, auth: Optional[tuple[str, str]] = None) -> HealthReport:
    report = HealthReport(site_url=site_url, generated_at=datetime.now(timezone.utc))
    check_reachable(report)
    check_ssl(report)
    check_wordpress(report, auth=auth)
    check_backups(report)
    check_performance(report)
    build_recommendations(report)
    # summary generated by caller – keep neutral
    return report

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: health_check.py <url> [--pdf]", file=sys.stderr)
        return 1
    site = argv[1]
    write_pdf = "--pdf" in argv
    auth = load_wp_auth(site)
    report = health_check(site, auth=auth)
    # Output JSON for the reminder script
    import json; print(json.dumps({
        "site": report.site_url,
        "generated": report.generated_at.isoformat(),
        "checks": [{"label": c.label, "status": c.status, "detail": c.detail,
                     "verified": c.verified} for c in report.checks],
        "recommendations": report.recommendations,
    }, indent=2))
    if write_pdf:
        # Very small PDF with plain text – omitted due to time
        print("PDF generation not implemented in this mode for brevity.")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
