# TidyCal Booking Prep

## Problem Statement
How might we help WebAwesome and MentoringBA clients book the right call and arrive prepared, while keeping private business data out of the client experience?

## Recommended Direction
Start with the preparation content built into the existing separate TidyCal booking types. Add a clear description of who each call is for, what it covers, and what the client should bring. Use TidyCal's existing confirmation and reminder options for any follow-up guidance.

This is the quickest test and does not depend on the dashboard's TidyCal integration. That integration is connected locally and read-only, but it is not required for clients to book. If clients need a more branded or guided experience later, add a small page for each business that links to its TidyCal booking type.

## Key Assumptions to Validate
- [ ] Clients read the booking description and arrive better prepared; check this in the first few calls.
- [ ] Each business's existing booking type clearly maps to a distinct client need; review both descriptions.
- [ ] TidyCal's confirmation and reminder settings can carry the preparation details you need; test a booking end-to-end.

## MVP Scope
Update the existing WebAwesome and MentoringBA booking types with a concise purpose, expected outcome, and preparation checklist. Test each booking flow from selection through confirmation.

## Not Doing
- **Public access to the AI OS dashboard:** it contains internal business data.
- **A client portal or custom scheduler:** unnecessary while TidyCal already handles booking.
- **Dashboard OAuth as a dependency:** the client booking experience should work without it.

## Open Questions
- What should clients bring or do before each of the two call types?
- Can TidyCal's current confirmation and reminder messages carry that guidance clearly?
