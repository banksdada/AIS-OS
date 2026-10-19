import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime

import requests

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
        req = urllib.request.Request(AIOS_WEBHOOK_URL, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("AIOS report sent:", resp.status)
        return True
    except Exception as e:
        print("AIOS report failed:", e)
        return False


ROTAMATE_URL = os.environ.get("ROTAMATE_URL", "").rstrip("/")
ROTAMATE_TOKEN = os.environ.get("ROTAMATE_AUTOMATION_TOKEN", "")
HTTP_TIMEOUT = int(os.environ.get("ROTAMATE_HTTP_TIMEOUT", "30"))


def fail(message):
    print(f"ERROR: {message}")
    report("rota-health-check", "failed", message)
    sys.exit(1)


def headers():
    return {
        "Authorization": f"Bearer {ROTAMATE_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def api_get(path):
    response = requests.get(
        f"{ROTAMATE_URL}{path}",
        headers=headers(),
        timeout=HTTP_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def api_post(path, payload):
    response = requests.post(
        f"{ROTAMATE_URL}{path}",
        headers=headers(),
        json=payload,
        timeout=HTTP_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def parse_datetime(date_value, time_value):
    date_text = str(date_value).split("T")[0]

    time_text = str(time_value)

    if "T" in time_text:
        return datetime.fromisoformat(
            time_text.replace("Z", "+00:00")
        )

    time_text = time_text.split("+")[0]

    if len(time_text) == 5:
        time_text += ":00"

    return datetime.fromisoformat(
        f"{date_text}T{time_text}"
    )


def hours_between(start, end):
    seconds = (end - start).total_seconds()

    return seconds / 3600


def experience_rank(level):
    ranks = {
        "junior": 1,
        "intermediate": 2,
        "senior": 3,
        "specialist": 4,
    }

    return ranks.get(
        (level or "").lower(),
        0,
    )


def analyse_rota(data):
    shifts = data.get("shifts", [])

    issues = []

    required_positions = 0
    assigned_positions = 0

    staff_shifts = defaultdict(list)
    staff_hours = defaultdict(float)
    staff_limits = {}

    for shift in shifts:
        required = int(
            shift.get("required_staff_count") or 1
        )

        assignments = shift.get("assignments") or []

        assigned = len(assignments)

        required_positions += required
        assigned_positions += min(assigned, required)

        unfilled = max(required - assigned, 0)
        extra = max(assigned - required, 0)

        if unfilled > 0:
            issues.append({
                "type": "unfilled_shift",
                "severity": "critical",
                "shift_id": shift.get("shift_id"),
                "message": (
                    f"Shift requires {required} staff "
                    f"but only {assigned} are assigned."
                ),
            })

        if extra > 0:
            issues.append({
                "type": "overstaffed_shift",
                "severity": "warning",
                "shift_id": shift.get("shift_id"),
                "message": (
                    f"Shift has {extra} more staff "
                    f"than required."
                ),
            })

        try:
            start = parse_datetime(
                shift.get("date"),
                shift.get("start_time"),
            )

            end = parse_datetime(
                shift.get("date"),
                shift.get("end_time"),
            )

            if end <= start:
                from datetime import timedelta
                end += timedelta(days=1)

        except Exception as exc:
            issues.append({
                "type": "invalid_shift_time",
                "severity": "critical",
                "shift_id": shift.get("shift_id"),
                "message": (
                    f"Unable to parse shift time: {exc}"
                ),
            })

            continue

        duration = hours_between(start, end)

        required_experience = (
            shift.get("required_experience_level")
        )

        for assignment in assignments:
            staff_id = assignment.get("staff_id")

            if not staff_id:
                continue

            staff_shifts[staff_id].append({
                "shift_id": shift.get("shift_id"),
                "start": start,
                "end": end,
                "can_do_back_to_back": bool(
                    assignment.get(
                        "can_do_back_to_back",
                        False,
                    )
                ),
            })

            staff_hours[staff_id] += duration

            max_hours = assignment.get(
                "max_hours_per_week"
            )

            if max_hours not in (None, ""):
                try:
                    staff_limits[staff_id] = float(
                        max_hours
                    )
                except (TypeError, ValueError):
                    pass

            staff_experience = assignment.get(
                "experience_level"
            )

            if required_experience:
                if (
                    experience_rank(staff_experience)
                    < experience_rank(
                        required_experience
                    )
                ):
                    issues.append({
                        "type": "experience_mismatch",
                        "severity": "critical",
                        "staff_id": staff_id,
                        "shift_id": shift.get(
                            "shift_id"
                        ),
                        "message": (
                            "Assigned staff experience "
                            f"'{staff_experience}' does "
                            "not meet required level "
                            f"'{required_experience}'."
                        ),
                    })

    overlap_count = 0
    short_gap_count = 0

    for staff_id, assignments in staff_shifts.items():
        assignments.sort(
            key=lambda item: item["start"]
        )

        for index in range(
            len(assignments) - 1
        ):
            current = assignments[index]
            following = assignments[index + 1]

            if following["start"] < current["end"]:
                overlap_count += 1

                issues.append({
                    "type": "overlap",
                    "severity": "critical",
                    "staff_id": staff_id,
                    "shift_id": following["shift_id"],
                    "message": (
                        "Staff member has overlapping "
                        "rota assignments."
                    ),
                })

                continue

            gap_hours = hours_between(
                current["end"],
                following["start"],
            )

            if (
                gap_hours < 1
                and not current[
                    "can_do_back_to_back"
                ]
            ):
                short_gap_count += 1

                issues.append({
                    "type": "short_gap",
                    "severity": "warning",
                    "staff_id": staff_id,
                    "shift_id": following["shift_id"],
                    "message": (
                        "Less than one hour between "
                        "consecutive assignments."
                    ),
                })

    weekly_hours_warnings = 0

    for staff_id, hours in staff_hours.items():
        maximum = staff_limits.get(staff_id)

        if maximum is not None and hours > maximum:
            weekly_hours_warnings += 1

            issues.append({
                "type": "weekly_hours",
                "severity": "critical",
                "staff_id": staff_id,
                "message": (
                    f"Projected rota hours are "
                    f"{hours:.1f}, exceeding the "
                    f"configured maximum of "
                    f"{maximum:.1f} hours."
                ),
            })

    if required_positions > 0:
        coverage = (
            assigned_positions
            / required_positions
        ) * 100
    else:
        coverage = 100.0

    critical_count = sum(
        1
        for issue in issues
        if issue["severity"] == "critical"
    )

    warning_count = sum(
        1
        for issue in issues
        if issue["severity"] == "warning"
    )

    score = coverage

    score -= critical_count * 3
    score -= warning_count * 1

    score = max(
        0,
        min(100, round(score, 2)),
    )

    if score >= 90 and critical_count == 0:
        status = "healthy"
    elif score >= 70:
        status = "warning"
    else:
        status = "critical"

    unfilled_positions = max(
        required_positions - assigned_positions,
        0,
    )

    metrics = {
        "shift_count": len(shifts),
        "required_positions": required_positions,
        "assigned_positions": assigned_positions,
        "unfilled_positions": unfilled_positions,
        "coverage_percent": round(
            coverage,
            2,
        ),
        "overlap_count": overlap_count,
        "short_gap_count": short_gap_count,
        "weekly_hours_warnings": (
            weekly_hours_warnings
        ),
        "critical_issue_count": critical_count,
        "warning_issue_count": warning_count,
    }

    summary = (
        f"Coverage {coverage:.1f}%. "
        f"{unfilled_positions} unfilled position(s), "
        f"{overlap_count} overlap(s), "
        f"{short_gap_count} short-gap warning(s), "
        f"{weekly_hours_warnings} workload warning(s)."
    )

    return {
        "score": score,
        "status": status,
        "summary": summary,
        "metrics": metrics,
        "issues": issues,
    }


def main():
    if not ROTAMATE_URL:
        fail(
            "ROTAMATE_URL environment variable "
            "is missing."
        )

    if not ROTAMATE_TOKEN:
        fail(
            "ROTAMATE_AUTOMATION_TOKEN environment "
            "variable is missing."
        )

    report("rota-health-check", "started", ROTAMATE_URL)

    print(
        f"Connecting to RotaMate at "
        f"{ROTAMATE_URL}"
    )

    try:
        data = api_get(
            "/api/automation/rota/next"
        )
    except Exception as exc:
        fail(
            f"Could not fetch pending rota: {exc}"
        )

    if data.get("status") == "idle":
        message = data.get(
            "message",
            "No pending rotas.",
        )
        print(message)
        report("rota-health-check", "idle", message)

        return

    rota_id = data.get(
        "rota_version_id"
    )

    if not rota_id:
        fail(
            "Laravel response did not contain "
            "rota_version_id."
        )

    print(
        f"Analysing rota version {rota_id}"
    )

    try:
        result = analyse_rota(data)

        print(result["summary"])

        print(
            f"Rota health score: "
            f"{result['score']}/100 "
            f"({result['status']})"
        )

        api_post(
            f"/api/automation/rota/"
            f"{rota_id}/result",
            result,
        )

        print(
            "Analysis successfully returned "
            "to RotaMate."
        )

        report(
            "rota-health-check",
            "ok",
            f"Score {result['score']}/100 "
            f"({result['status']}) — {result['summary']}",
        )

    except Exception as exc:
        print(
            f"Analysis failed: {exc}"
        )

        report("rota-health-check", "failed", f"analysis failed: {exc}")

        try:
            api_post(
                f"/api/automation/rota/"
                f"{rota_id}/failed",
                {
                    "error": str(exc)
                },
            )

        except Exception as report_exc:
            print(
                "Could not report failure "
                f"to Laravel: {report_exc}"
            )

        raise


if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        if err.code not in (0, None):
            report("rota-health-check", "failed", "setup or fetch problem — check PyRunner logs")
        raise
    except Exception as err:
        report("rota-health-check", "failed", str(err))
        raise
