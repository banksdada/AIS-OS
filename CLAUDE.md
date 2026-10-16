@ AGENTS.md



TidyCal MCP server
Ask Claude, ChatGPT, or another MCP-capable assistant about your TidyCal schedule — your booking types, your bookings, and when you are free.

TidyCal Pro is required. The MCP server is a Pro feature. On a free plan the connection authenticates but every call returns "TidyCal Pro is required to use the MCP server." See plans.
Server URL
Point your MCP client at:

https://tidycal.com/mcp
It speaks MCP over HTTP. There is nothing to install and no API key to paste.

Connecting
Add https://tidycal.com/mcp as a custom MCP server (sometimes called a connector) in your client:
Claude (web and desktop): Settings → Connectors → Add custom connector.
ChatGPT: Settings → Connectors → Add, then choose a custom connector. Custom connectors need a ChatGPT plan that supports them.
Other MCP clients: follow the client's steps for a remote MCP server over HTTP.
Your client registers itself automatically and sends you to TidyCal to sign in.
Approve the request. You are granting read access to your own scheduling data.
Ask your assistant something like "what does my TidyCal schedule look like this week?"
Authentication
OAuth 2.1 with PKCE and dynamic client registration — the flow MCP clients already implement, so you should not have to configure any of it by hand. The details, for anyone connecting a client that needs them:

Discovery	https://tidycal.com/.well-known/oauth-protected-resource
https://tidycal.com/.well-known/oauth-authorization-server
Registration	https://tidycal.com/oauth/register — dynamic, no pre-registration
Grant type	authorization_code (PKCE, S256) and refresh_token
Scope	mcp:scheduling:read
What it can do
Everything is read-only. This version of the server cannot create, change, or cancel a booking — it can only look at your account.

Tool	What it returns
get-current-user	Get the authenticated TidyCal user's profile: name, email, timezone, language, currency, and Pro status. Call this first when the user asks about themselves or to confirm whose account is connected.
list-teams	List the teams that the authenticated user owns or belongs to. Returns paginated team summaries (id, name, timestamps). Use this when the user mentions teams, group scheduling, or collaborative booking pages.
get-team	Get a single team by ID. Returns the team summary if the authenticated user owns or belongs to that team; otherwise returns a not-found error (does not leak IDs).
list-booking-types	List the authenticated user's booking types — the scheduling pages they offer to their clients (e.g., "30-minute consult", "60-minute interview"). Returns paginated results with full details: title, slug, duration, price, description, and configuration. Use this when the user asks "what booking types do I have" or wants to identify a specific one before calling another tool.
get-booking-type	Get full details for one booking type by ID, including availability windows, questions, reminders, and pricing. Authorization is enforced — returns a not-found error if the booking type does not belong to the authenticated user or a team they're on.
list-booking-type-available-times	List the available time slots for a booking type within a date range — the times a client could actually book. This is the canonical TidyCal availability lookup and accounts for the user's schedule, existing bookings, calendar conflicts, and buffers. Use this when the user asks "when am I available?" or "when can someone book the 30-minute consult next week?".
list-bookings	List the authenticated user's scheduled bookings (meetings on their calendar via TidyCal). Supports an optional date-range filter (starts_at / ends_at) and a cancelled flag. Use this for questions like "what does my schedule look like next week?", "show my upcoming meetings", or "list my cancelled bookings".
get-booking	Get full details for one booking by ID, including the booking type, contact, questions, payment, and hosts. Authorization is enforced via BookingPolicy — returns a not-found error if the user is neither the host nor an authorized team member.
list-busy-times	List external calendar events (non-booking events from the user's connected calendars) that occur in a date range. Covers every connected provider — Google, Microsoft and Apple — for calendars the user has enabled for conflict checking. These are the events that block TidyCal availability. Use this when the user asks "what conflicts are on my calendar?" or "show my external events next week" — for actual TidyCal meetings, use list-bookings instead.
list-locations	List the configured locations for a booking type — physical addresses, phone numbers, video conferencing providers (Zoom, Google Meet, etc.). Each booking type can have multiple locations; the guest picks one when booking.
Troubleshooting
Every call returns a Pro error
The account you connected is not on Pro. Check which account you authorised — asking your assistant who it is connected as will tell you.
The connection fails before the sign-in screen
Check the URL is exactly https://tidycal.com/mcp, with no trailing slash or path after it.
A meeting on my Google, Outlook, or Apple calendar is missing
TidyCal bookings show up straight away. Events from your connected calendars appear once TidyCal next syncs that calendar, so a very recent change can take a little while to show.
