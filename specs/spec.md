<!-- ai-generated: 90% - Claude Code drafted this specification from REQUIREMENTS.md and API.md; the author chose the C1/C2/C3 resolutions after reviewing the tradeoffs and reviewed the resulting text -->
# svcdesk - specification (Lab 1)

This is our reading of [REQUIREMENTS.md](../docs/REQUIREMENTS.md) and [API.md](../docs/API.md), written before any
code exists under `src/`. It states what the service will do, including which side of each of the three
contradictory pairs it takes. Where this document and API.md differ in precision, API.md is the enforced contract;
this document exists to record the reasoning behind the choices, not to restate the wire format.

## 1. Purpose and shape

A single HTTP service, `svcdesk`, on port 8080, JSON in and out (R-01). It stores tickets, computes their priority
and SLA due instants, drives them through a fixed state machine, and reports breach/pause status on demand. It
persists across a container restart (R-23) and exposes `GET /health` for readiness (R-02, R-24).

## 2. Ticket model

A ticket carries: `id` (opaque, server-assigned, R-18), `title` (1..200, required), `description` (0..4000,
optional), `reporter` (`name` 1..100 required, `email` optional, `vip` optional default false), `impact` and
`urgency` (each 1..3, required), `priority` (server-computed), `state`, four event timestamps (`created_at`,
`acknowledged_at`, `resolved_at`, `closed_at`), an optional `related_to`, and an `sla` block with the two due
instants (R-03, R-17, R-18). Fields the service owns and any field the client does not recognise are accepted and
silently ignored, never rejected (R-20).

## 3. Priority - decision C3 (VIP reporters and the priority matrix)

**The conflict.** R-05 says priority comes from the impact/urgency matrix and from nothing else - not the reporter,
not the agent. R-06 says a VIP reporter's ticket is never lower than P2, whatever the matrix says. A VIP ticket that
the matrix would put at P3 or P4 cannot simultaneously obey both sentences.

**Our resolution: C3 = `vip`.** The matrix (R-04) is always computed first. If the reporter is VIP and the matrix
result is P3 or P4, the ticket is raised to P2; P1 and P2 results are left unchanged, and a P1 stays P1 for a VIP
exactly as for anyone else. We reject the "and from nothing else" clause of R-05 for the VIP case specifically; we
keep everything else in R-05 (the client can never request a priority directly - a `priority` field in the request
body is always ignored, matrix or no VIP override). The reporter's `vip` flag is always stored regardless of which
side of C3 is chosen.

## 4. State machine and reopening - decision C2 (closed tickets and reopening)

States: `new` -> `acknowledged` -> `in_progress` -> `resolved` -> `closed`, one action and endpoint per transition
(`ack`, `start`, `resolve`, `close`), each recording its own timestamp (R-07). Any other transition, or an action on
an unknown id, is refused (409 for a bad transition, 404 for an unknown id; R-08).

**The conflict.** R-09 says a closed ticket is immutable: further work needs a new ticket via `related_to`. R-10
says a reporter may reopen a resolved *or closed* ticket within 7 days if the fix did not hold. A closed ticket
cannot be both permanently sealed and reopenable.

**Our resolution: C2 = `reopen`.** `POST /tickets/{id}/reopen` is accepted from `resolved` (always, within the
7-day window measured from `resolved_at`) and from `closed` (within the 7-day window measured from `closed_at`),
per R-10 and R-11. We reject the immutability clause of R-09 in favour of giving the reporter a working reopen path
for the case that matters most to them - the fix did not hold - and keep the rest of R-09 (a closed ticket cannot be
edited directly; the only way back into work is the reopen endpoint, not a silent state change). A reopen clears
`resolved_at` and `closed_at` and returns the ticket to `in_progress`; it never restarts or extends the resolution
target (R-11, R-16). Outside the 7-day window, from either state, reopen is 409.

## 5. SLA clocks and targets - decision C1 (the SLA clock for P1)

Each priority has an acknowledge and a resolve target measured from `created_at` (R-12). Two ways exist to turn a
target into a due instant: a wall-clock target (`created_at + target`) and a business-hours target that only counts
Monday-Friday 08:00-16:00 Europe/Warsaw, with the tie rule that a target ending exactly at closing is due at
16:00:00 that day (API.md §4).

**The conflict.** R-13 says every SLA clock pauses outside business hours. R-14 says P1 must be acknowledged within
15 minutes and resolved within 4 hours "around the clock", explicitly around a Friday evening. A P1 clock cannot
both pause on Friday at 18:00 and simultaneously be already late by Saturday morning.

**Our resolution: C1 = `wallclock`.** P1's ack and resolve targets both run on the wall-clock: a P1 raised at any
hour is due 15 minutes and 4 hours later, full stop. We reject the general pause rule of R-13 for P1 specifically,
because R-14 states the around-the-clock behaviour in concrete, testable terms (the Friday-evening example) that
only make sense if the P1 clock never pauses; keeping R-13's general clock for P2-P4 (which do pause outside
business hours, unchanged) preserves the rest of R-13. `paused` (section 5 below) is therefore always false for a
P1 ticket, because its resolution target does not run on the business-hours clock.

## 6. Breach and pause

`GET /tickets/{id}/sla` reports, at the instant of the request (the test clock when present, else real time):
`ack_breached` (acknowledged after the due instant, or not yet acknowledged and the due instant has passed),
`resolve_breached` (the equivalent for resolution; a reopened ticket counts as not resolved again, against its
unchanged original target), and `paused` (the ticket is open, its resolution clock is the business-hours one, and
the current instant falls outside a business window) (R-15, R-16).

## 7. Validation, errors and the test clock

`title`, `reporter.name`, `impact` and `urgency` are required; `impact`/`urgency` must be integers 1..3; anything
else is refused with 400 or 422 and a JSON body carrying a top-level `error` object (R-20). Unknown ticket ids and
unknown paths are 404 with the same shape (R-25). When `SVCDESK_TEST_CLOCK` is `1` or `true`, a request may carry
`X-Test-Clock` with an RFC 3339 instant used as "now" for that request only; a header that fails to parse is 400 or
422; without the feature enabled the header is ignored entirely (R-21, API.md §8).

## 8. Compose and persistence

`docker-compose.yml` builds `svcdesk` from this repository (never `image:` alone), listens on 8080, sets
`SVCDESK_TEST_CLOCK`, uses no host-path bind mounts, and needs no network once built (R-22). Tickets are kept in a
SQLite file inside a named volume so they survive a container restart (R-23); `docker compose up` answers
`GET /health` within 120 seconds (R-24).

## 9. Out of scope for Lab 1

`related_to` is stored but not validated against existing ids (API.md §2). Pagination is not implemented; the desk
is small enough that `GET /tickets` returns every matching ticket in one array (R-19).
