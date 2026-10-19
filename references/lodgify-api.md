# Lodgify API

Lodgify Public API v2 — vacation-rental PMS used for guest bookings and
messaging. The AI OS panel is **read-only**: it polls for upcoming arrivals
and guest messages that need a reply. The owner replies inside Lodgify, so
guests never get an unreviewed automated message.

## Auth

Every request needs the account API key in a header (not OAuth):

```
X-ApiKey: <your key>
```

Key source: Lodgify dashboard → Integrations → API. Stored as
`LODGIFY_API_KEY` in `.env` (local) and Coolify's Environment tab (server —
the live server ignores `.env`). Rate limit: 750 requests/minute on v2
(HTTP 429 when exceeded). The panel caches for 5 minutes
(`scripts/dashboard/lodgify.py`, `CACHE_SECONDS`).

## Endpoints used (Step 1 — polling panel)

### List bookings

```
GET https://api.lodgify.com/v2/reservations/bookings
    ?stayFilter=Upcoming|Current&page=1&size=50&includeCount=true
```

Returns `{count, items: [BookingDto]}`. Booking fields the panel keeps:
`id`, `arrival`, `departure`, `property_id`, `guest{name,email,phone}`,
`status` (Open/Tentative/Booked/Declined), `source` (Manual/Airbnb/
BookingCom/…), `is_new`, `thread_uid`, `check_in.time`, `check_out.time`.
Rooms may carry a `key_code` — never sent to the browser by the panel.

Useful extra params: `updatedSince=<ISO datetime>` (incremental polling),
`stayFilterDate`, `trash`, `includeTransactions`.

### Property names

```
GET https://api.lodgify.com/v2/properties
```

Returns `{count, items: [{id, name, internal_name, …}]}`. Maps
`property_id` → display name. The panel tolerates failure and falls back
to "Property <id>".

### Message thread

```
GET https://api.lodgify.com/v2/messaging/{threadGuid}
```

`threadGuid` is the booking's `thread_uid`. Returns an array of
`ThreadItemListDetailDto`: `thread_uid`, `guest_name`, `guest_email`,
`last_message_date`, `is_read`, `is_closed`, and `messages[]` where each
message has `id`, `subject`, `message` (HTML body), `type` (**Owner** or
**Renter**), `date_created`, `is_read`, `route` (Email/Airbnb/BookingCom/
Vrbo/Sms).

## Panel logic (scripts/dashboard/lodgify.py)

- **Arrivals**: Upcoming + Current bookings; kept when arrival is within
  `LODGIFY_ARRIVAL_HOURS` (default 48). Date-only arrivals compare by
  calendar day so same-day check-ins are never dropped.
- **Needs reply**: newest message in the thread is from the guest (Renter)
  with no Owner message after it.
- **Unanswered flag**: needs-reply and waiting ≥
  `LODGIFY_UNANSWERED_MINUTES` (default 120).
- **Urgent tags** (only on unreplied threads): `check-in` (check in/out,
  arrival, late/early), `access` (access/key/pin/door/gate code, lockbox,
  can't get in), `problem` (broken, not working, emergency, leak, no hot
  water, wifi down, locked out…).
- **No automatic replies.** The dashboard shows what needs attention; the
  owner replies in Lodgify.

## Step 2 — webhooks (deferred, not built)

Goal: Lodgify POSTs new guest messages to the dashboard for instant
updates instead of polling. Findings from the official surface:

- `POST /webhooks/v1/subscribe` body: `{"event": "<name>", "target_url":
  "<https url>"}`. Example event name in the spec: `booking_change`.
  Also `GET /webhooks/v1/list`, `DELETE /webhooks/v1/unsubscribe` and
  `DELETE /webhooks/v1/{id}`.
- **The public OpenAPI spec defines no request-signature scheme** — no
  HMAC header, no signing secret field. The docs only say the target URL
  "should return a 200 OK response".
- Before building the endpoint, confirm from the account's webhook settings
  (or a test subscription) whether Lodgify signs requests, and how. If it
  does not, the endpoint must still be safe: require an unguessable path
  secret (`/webhook/lodgify/<random>`), validate payload shape, rate-limit,
  and reconcile with the API (fetch the thread by `thread_uid` on receipt
  rather than trusting the POST body).

Build plan when confirmed: `POST /webhook/lodgify` on the dashboard server
(same HMAC pattern as `/webhook/pyrunner` if signing exists), store events
in `data/lodgify-events.json`, panel shows "live" badge when webhooks are
flowing; polling stays as fallback.

## References

- API index: https://docs.lodgify.com/reference (v1 + v2)
- Bookings list: https://docs.lodgify.com/reference/getallasync
- Thread details: https://docs.lodgify.com/reference/get_v2-messaging-threadguid
- Rate limits: https://docs.lodgify.com/reference/rate-limits
