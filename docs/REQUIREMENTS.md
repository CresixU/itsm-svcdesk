<!-- ai-generated: 0% - written by the course team -->
# svcdesk - requirements

Owner: Service Desk product owner, internal IT. Version 1.0, for the first build.

## Purpose

We run a service desk for about four hundred people in three offices. Today tickets live in a spreadsheet and in
people's inboxes, and nobody can say at 09:00 on Monday which tickets are late. We need a small ticketing service
that our desk agents, our monitoring and our future integrations can call over HTTP. It must compute priority for
us, keep the SLA clocks, and refuse things that make our reports wrong.

This document lists what the service must do. Every requirement has an identifier (R-01 to R-25); refer to them in
your specifications and in your decisions. The technical interface (paths, field names, exact status codes, the
test clock) is defined in [API.md](API.md); where this document and API.md differ in precision, API.md is the
contract that is enforced. The checks that will be run against your service are published in
[CHECKS.md](CHECKS.md).

## Requirements

**R-01** The service desk exposes an HTTP API on port 8080. Every request body and every response body is JSON
(`application/json`); there is no other interface.

**R-02** `GET /health` answers 200 with `{"status": "ok", "service": "svcdesk"}`, so that monitoring and our
deployment tooling can tell that the desk is up.

**R-03** A ticket has a title (1 to 200 characters, required), a description (up to 4000 characters, optional), a
reporter with a name (1 to 100 characters, required), an optional e-mail address and an optional VIP flag
(`reporter.vip`, default false), an impact and an urgency. Impact and urgency each take one of three levels:
impact 1 = the whole organisation is affected, 2 = a team, 3 = one person; urgency 1 = work has stopped,
2 = work is degraded, 3 = cosmetic. A ticket may name an earlier ticket it relates to (`related_to`).

**R-04** Priority is computed from impact and urgency with this matrix:

| impact \ urgency | 1 (work stopped) | 2 (degraded) | 3 (cosmetic) |
|---|---|---|---|
| **1** (organisation) | P1 | P2 | P3 |
| **2** (team) | P2 | P3 | P4 |
| **3** (one person) | P3 | P4 | P4 |

**R-05** Priority is derived from the impact and urgency matrix and from nothing else; neither the reporter nor the
agent can request a priority.

**R-06** Tickets raised by VIP reporters (`reporter.vip = true`) are never lower than P2, whatever the matrix says,
so that executive issues are visible to the desk immediately.

**R-07** A ticket moves through the states `new`, `acknowledged`, `in_progress`, `resolved` and `closed`, in that
order: an agent acknowledges a new ticket, starts work on an acknowledged one, resolves the one in progress, and
closes a resolved ticket once the reporter has confirmed the fix. Reopening returns a ticket to `in_progress`. Each
transition is a separate action with its own endpoint, and the service records when the acknowledgement, the
resolution and the closure happened.

**R-08** Any other transition is refused with `409 Conflict` and an error body. There are no shortcuts: a ticket
cannot be resolved before work on it has started, nor closed before it has been resolved, and an action on a
ticket that does not exist is a 404.

**R-09** A closed ticket is immutable. Any further work on the same issue requires a new ticket that references the
closed one via `related_to`.

**R-10** A reporter may reopen a resolved or closed ticket within 7 days of its resolution or closure if the fix
did not work; the ticket returns to `in_progress`.

**R-11** A reopen request outside the 7-day window is refused with 409. Reopening a ticket does not restart or
extend its resolution target.

**R-12** Each priority has an acknowledgement target and a resolution target, both measured from the moment the
ticket was created:

| priority | acknowledge within | resolve within |
|---|---|---|
| P1 | 15 min | 4 h |
| P2 | 1 h | 8 h |
| P3 | 4 h | 24 h |
| P4 | 8 h | 72 h |

**R-13** SLA clocks pause outside business hours (Monday to Friday, 08:00 to 16:00, Europe/Warsaw); time outside
those hours does not count against any SLA target.

**R-14** P1 tickets must be acknowledged within 15 minutes and resolved within 4 hours of creation, around the
clock: a P1 raised on Friday evening is late at 15 minutes past, not on Monday morning.

**R-15** `GET /tickets/{id}/sla` reports the ticket's priority, both due instants, whether each target has been
breached, and whether the ticket's clock is currently paused, so that the Monday report can be produced from one
call per ticket.

**R-16** A target is breached when the corresponding event (acknowledgement, resolution) happened after the due
instant, or has not happened yet and the due instant has passed. Reaching the due instant exactly is not a breach.
A ticket is paused when it is still open (neither resolved nor closed), its resolution target runs on the
business-hours clock, and the current moment is outside business hours. A reopened ticket counts as not resolved
again, against its original resolution target.

**R-17** Every timestamp in the API is an RFC 3339 instant. The service reports instants in UTC with a `Z` suffix.

**R-18** Every ticket has an opaque, unique, non-empty identifier assigned by the service; clients never choose or
predict it.

**R-19** `GET /tickets` lists tickets and accepts optional exact-match filters on `state` and `priority`. The desk
is small: the list returns every matching ticket in one response, in any order, without pagination.

**R-20** A request that does not satisfy R-03 (missing title, title too long, impact or urgency outside 1 to 3 or
not an integer, and so on) is refused with 400 or 422 and a JSON body carrying an `error` object. Fields the
service owns (the id, the priority, the state, the timestamps, the SLA block) and unknown fields in a request are
ignored, never rejected.

**R-21** For testing, when the environment variable `SVCDESK_TEST_CLOCK` is `1` or `true`, a request may carry an
`X-Test-Clock` header with an RFC 3339 instant that the service uses as "now" for that request only. Without the
header the service uses real UTC time. A header that does not parse is a 400 or 422.

**R-22** The service ships as a Docker Compose project: a service named `svcdesk`, built from the repository,
listening on port 8080 inside the container, with `SVCDESK_TEST_CLOCK` set, without host-path bind mounts on any
service, and without any network access once the image has been built.

**R-23** Tickets survive a restart of the service container.

**R-24** From `docker compose up`, the service is running and answers `GET /health` within 120 seconds.

**R-25** An unknown path answers 404 with a JSON body; an unknown ticket id answers 404 with a JSON body carrying
an `error` object.
