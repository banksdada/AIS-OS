from __future__ import annotations

import json
import unittest
from datetime import date

import httpx

from app.tidycal import SlotUnavailable, TidyCalClient, TidyCalError, display_slot


def client_for(handler: httpx.MockTransport) -> TidyCalClient:
    return TidyCalClient("tok-123", "1292586", "test-agent", transport=handler)


class TidyCalClientTests(unittest.TestCase):
    def test_timeslots_sends_auth_ua_and_date_range(self) -> None:
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["auth"] = request.headers.get("Authorization", "")
            seen["ua"] = request.headers.get("User-Agent", "")
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "starts_at": "2026-11-17T19:00:00.000000Z",
                            "ends_at": "2026-11-17T19:15:00.000000Z",
                        }
                    ]
                },
            )

        client = client_for(httpx.MockTransport(handler))
        slots = client.timeslots(days=10, start=date(2026, 11, 16))

        self.assertIn("starts_at=2026-11-16", seen["url"])
        self.assertIn("ends_at=2026-11-26", seen["url"])
        self.assertEqual(seen["auth"], "Bearer tok-123")
        self.assertEqual(seen["ua"], "test-agent")
        self.assertEqual(len(slots), 1)

    def test_create_booking_sends_required_fields(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured.update(json.loads(request.content))
            return httpx.Response(201, json={"data": {"id": 99, "starts_at": "2026-11-17T19:00:00Z"}})

        client = client_for(httpx.MockTransport(handler))
        data = client.create_booking(
            name="Ada", email="ada@example.com", starts_at="2026-11-17T19:00:00Z"
        )

        self.assertEqual(captured["name"], "Ada")
        self.assertEqual(captured["email"], "ada@example.com")
        self.assertEqual(captured["timezone"], "Europe/London")
        self.assertEqual(captured["starts_at"], "2026-11-17T19:00:00Z")
        self.assertEqual(data["id"], 99)

    def test_create_booking_409_raises_slot_unavailable(self) -> None:
        handler = httpx.MockTransport(lambda request: httpx.Response(409, text="slot taken"))
        client = client_for(handler)
        with self.assertRaises(SlotUnavailable):
            client.create_booking(name="Ada", email="ada@example.com", starts_at="2026-11-17T19:00:00Z")

    def test_rate_limit_reports_retry_after(self) -> None:
        handler = httpx.MockTransport(
            lambda request: httpx.Response(429, headers={"Retry-After": "42"}, text="slow down")
        )
        client = client_for(handler)
        with self.assertRaises(TidyCalError) as ctx:
            client.available_slots()
        self.assertIn("42", str(ctx.exception))

    def test_missing_token_is_rejected(self) -> None:
        with self.assertRaises(TidyCalError):
            TidyCalClient("", "1292586", "test-agent")

    def test_display_slot_uses_london_time(self) -> None:
        label = display_slot("2026-11-17T19:00:00.000000Z")
        self.assertIn("17 Nov", label)
        self.assertIn("19:00", label)


if __name__ == "__main__":
    unittest.main()
