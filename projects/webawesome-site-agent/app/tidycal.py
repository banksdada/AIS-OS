from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

TIDYCAL_BASE = "https://tidycal.com/api"
LONDON = "Europe/London"


class TidyCalError(Exception):
    """Base error for TidyCal calls."""


class SlotUnavailable(TidyCalError):
    """The requested slot was taken or is no longer offered (HTTP 409)."""


class TidyCalClient:
    def __init__(
        self,
        token: str,
        booking_type_id: str,
        user_agent: str,
        *,
        timeout: float = 20.0,
        base_url: str = TIDYCAL_BASE,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not token:
            raise TidyCalError("TIDYCAL_API_TOKEN is not set")
        if not booking_type_id:
            raise TidyCalError("TIDYCAL_BOOKING_TYPE_ID is not set")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": user_agent,
        }
        self.booking_type_id = str(booking_type_id)
        self._timeout = timeout
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    def _client(self) -> httpx.Client:
        return httpx.Client(headers=self._headers, timeout=self._timeout, transport=self._transport)

    def list_booking_types(self) -> list[dict[str, Any]]:
        with self._client() as client:
            response = client.get(f"{self._base_url}/booking-types")
        self._raise(response)
        body = response.json()
        return body.get("data", body if isinstance(body, list) else [])

    def timeslots(self, *, days: int = 14, start: date | None = None) -> list[dict[str, Any]]:
        start = start or date.today()
        end = start + timedelta(days=days)
        params = {"starts_at": start.isoformat(), "ends_at": end.isoformat()}
        with self._client() as client:
            response = client.get(
                f"{self._base_url}/booking-types/{self.booking_type_id}/timeslots",
                params=params,
            )
        self._raise(response)
        body = response.json()
        return body.get("data", body if isinstance(body, list) else [])

    def available_slots(self, *, limit: int = 3, days: int = 14) -> list[dict[str, str]]:
        slots = self.timeslots(days=days)
        return [
            {
                "starts_at": slot["starts_at"],
                "ends_at": slot.get("ends_at", ""),
                "label": display_slot(slot["starts_at"]),
            }
            for slot in slots[:limit]
        ]

    def create_booking(
        self,
        *,
        name: str,
        email: str,
        starts_at: str,
        timezone: str = LONDON,
        questions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "email": email,
            "timezone": timezone,
            "starts_at": starts_at,
        }
        if questions:
            payload["booking_questions"] = questions
        with self._client() as client:
            response = client.post(
                f"{self._base_url}/booking-types/{self.booking_type_id}/bookings",
                json=payload,
            )
        if response.status_code == 409:
            raise SlotUnavailable(response.text[:300])
        self._raise(response)
        body = response.json()
        return body.get("data", body)

    @staticmethod
    def _raise(response: httpx.Response) -> None:
        if response.is_success:
            return
        detail = response.text[:300]
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise TidyCalError(f"rate limited, retry after {retry_after}s: {detail}")
        raise TidyCalError(f"TidyCal HTTP {response.status_code}: {detail}")


def display_slot(iso_utc: str, timezone: str = LONDON) -> str:
    moment = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    return moment.astimezone(ZoneInfo(timezone)).strftime("%a %d %b, %H:%M %Z")
