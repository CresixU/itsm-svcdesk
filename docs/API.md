<!-- ai-generated: 0% - written by the course team -->
# svcdesk - interface contract (Lab 1)

This is the contract the checker enforces, section by section; `report.json` cites these sections in its `rule`
field (for example `API.md §4`). [REQUIREMENTS.md](REQUIREMENTS.md) says what the desk wants and why; this file
says exactly what the HTTP interface does. Implement it in any language: the checker speaks only HTTP.

Conventions: an "instant" is an RFC 3339 timestamp compared as a point in time, never as a string; the "clock" is
the per-request test clock of section 8. Where a behaviour depends on one of the three decisions you record in
`DECISIONS.md` (C1, C2, C3; see [HANDOUT.md](HANDOUT.md)), this file lists both admissible behaviours, and
[CHECKS.md](CHECKS.md) shows what the checker accepts for each.

## 1. Endpoints

| method and path | success | notes |
|---|---|---|
| `GET /health` | 200 `{"status":"ok","service":"svcdesk"}` | extra fields allowed |
| `POST /tickets` | 201 Ticket | validation error: 400 or 422 with `{"error": {...}}` (section 7) |
| `GET /tickets` | 200 `[Ticket]` | optional filters `?state=` and `?priority=` (exact match); all matching tickets in one array, no pagination, any order (the checker never creates more than 100 tickets per run) |
| `GET /tickets/{id}` | 200 Ticket | 404 `{"error": {...}}` if unknown |
| `GET /tickets/{id}/sla` | 200 (section 5) | 404 if unknown |
| `POST /tickets/{id}/ack`, `/start`, `/resolve`, `/close`, `/reopen` | 200 Ticket | 409 on an invalid transition (section 6), 404 if unknown |
| unknown path | 404 with a JSON body | a wrong method on a known path may answer 404 or 405 |

All responses are `application/json`. Successful actions return 200 with the full ticket.

## 2. Ticket model

```
Ticket {
  id: string            opaque, unique, non-empty (UUID recommended)
  title: string         1..200 characters
  description: string   0..4000 characters, optional (default "")
  reporter: { name: string (1..100), email: string | null (optional, default null), vip: boolean (optional, default false) }
  impact: 1 | 2 | 3     1 = high (whole organisation), 2 = medium (a team), 3 = low (one person)
  urgency: 1 | 2 | 3    1 = high (work stopped), 2 = medium (work degraded), 3 = low (cosmetic)
  priority: "P1" | "P2" | "P3" | "P4"        computed by the service, never accepted from the client
  state: "new" | "acknowledged" | "in_progress" | "resolved" | "closed"
  created_at, acknowledged_at, resolved_at, closed_at: instants; absent or null until the event happened
  related_to: string | null     optional on create; id of an earlier ticket; not validated in Lab 1
  sla: { ack_due_at: instant, resolve_due_at: instant }
}
```

Server-owned fields sent by a client (`id`, `priority`, `state`, `created_at`, `acknowledged_at`, `resolved_at`,
`closed_at`, `sla`) and any unknown fields are silently ignored, never an error. The service SHOULD return UTC
instants with a `Z` suffix; the checker parses any RFC 3339 offset and compares instants, and the checker itself
always sends whole-second `Z` instants.

## 3. Priority matrix

| impact \ urgency | 1 | 2 | 3 |
|---|---|---|---|
| **1** | P1 | P2 | P3 |
| **2** | P2 | P3 | P4 |
| **3** | P3 | P4 | P4 |

The matrix is the starting point under every decision. What happens next for a VIP reporter is decision C3:

| C3 | behaviour |
|---|---|
| `matrix` | the matrix decides; `reporter.vip` is stored but does not affect priority (impact 3, urgency 3, vip true is `P4`) |
| `vip` | after the matrix, a VIP ticket at P3 or P4 is raised to P2; P1 and P2 are unchanged (the same ticket is `P2`) |

Under both, a VIP ticket at impact 1, urgency 1 is `P1`, and a `priority` field in the request body is ignored.

## 4. SLA targets and clocks

| priority | acknowledge within | resolve within |
|---|---|---|
| P1 | 15 min | 4 h |
| P2 | 1 h | 8 h |
| P3 | 4 h | 24 h |
| P4 | 8 h | 72 h |

There are two ways to turn a target into a due instant:

- A **wall-clock** target is `created_at + target`.
- A **business-hours** target counts only time inside business hours: Monday to Friday, the half-open window
  [08:00:00, 16:00:00) in `Europe/Warsaw` (DST-aware; public holidays are business days: Polish holidays are out of
  scope for the whole course). Algorithm: convert `created_at` to Europe/Warsaw; if it is outside a business window,
  move forward to the next opening (08:00:00 of the next business day, or 08:00:00 today if before opening); consume
  the target from consecutive business windows; **a target that ends exactly at closing time is due at 16:00:00 of
  that day, not 08:00:00 of the next** (the tie rule; see T4); convert the due instant back to UTC.

Which clock applies to which priority is decision C1:

| C1 | behaviour |
|---|---|
| `wallclock` | both P1 targets are wall-clock; P2 to P4 use the business-hours clock |
| `business` | every priority uses the business-hours clock |

Under both, P2 to P4 use the business-hours clock, and a P1 created inside business hours (T1) has identical due
instants. A mixed pair for P1 (one target wall-clock, the other business-hours) is not admissible.

Your image needs the IANA time zone database for `Europe/Warsaw`: Debian-based images such as
`python:3.13-slim` have it; Alpine needs `apk add tzdata`; Go needs `import _ "time/tzdata"` (or tzdata in the
image); Node's official images ship full ICU. Without it the first `POST /tickets` fails and every L1-CORE-2
check that creates a ticket errors out.

Test vectors. Your implementation must reproduce every value exactly. Both DST transitions in the semester fall on
Sundays, so no vector spans a transition inside a business window.

| id | priority | created_at | local | ack due (wall-clock) | ack due (business) | resolve due (wall-clock) | resolve due (business) |
|---|---|---|---|---|---|---|---|
| T1 | P1 | 2026-10-14T10:00:00Z | Wed 12:00 CEST | 2026-10-14T10:15:00Z | 2026-10-14T10:15:00Z | 2026-10-14T14:00:00Z | 2026-10-14T14:00:00Z |
| T2 | P3 | 2026-10-16T13:30:00Z | Fri 15:30 CEST | 2026-10-16T17:30:00Z | 2026-10-19T09:30:00Z | 2026-10-17T13:30:00Z | 2026-10-21T13:30:00Z |
| T3 | P1 | 2026-10-16T15:00:00Z | Fri 17:00 CEST | 2026-10-16T15:15:00Z | 2026-10-19T06:15:00Z | 2026-10-16T19:00:00Z | 2026-10-19T10:00:00Z |
| T4 | P2 | 2026-10-17T10:00:00Z | Sat 12:00 CEST | 2026-10-17T11:00:00Z | 2026-10-19T07:00:00Z | 2026-10-17T18:00:00Z | 2026-10-19T14:00:00Z |
| T5 | P4 | 2027-01-14T14:30:00Z | Thu 15:30 CET | 2027-01-14T22:30:00Z | 2027-01-15T14:30:00Z | 2027-01-17T14:30:00Z | 2027-01-27T14:30:00Z |
| T6 | P1 | 2027-01-15T15:50:00Z | Fri 16:50 CET | 2027-01-15T16:05:00Z | 2027-01-18T07:15:00Z | 2027-01-15T19:50:00Z | 2027-01-18T11:00:00Z |
| T7 | P2 | 2026-10-14T10:00:00Z | Wed 12:00 CEST | 2026-10-14T11:00:00Z | 2026-10-14T11:00:00Z | 2026-10-14T18:00:00Z | 2026-10-15T10:00:00Z |
| T8 | P3 | 2026-10-23T13:00:00Z | Fri 15:00 CEST (DST ends Sun 25 Oct) | 2026-10-23T17:00:00Z | 2026-10-26T10:00:00Z | 2026-10-24T13:00:00Z | 2026-10-28T14:00:00Z |

Reading the table: the "wall-clock" columns apply to P1 under C1 = `wallclock`; the "business" columns apply to
every other priority under both decisions and to P1 under C1 = `business`. T4's business resolve target (8 h from
Monday 08:00) ends exactly at 16:00 and is due Monday 16:00 local = 14:00Z: that is the tie rule. T8 shows a P3
whose 24 business hours run across the weekend in which DST ends; the 24 business hours are consumed as 1 h on
Friday (15:00 to 16:00), 8 h on Monday, 8 h on Tuesday and 7 h on Wednesday, so it is due Wednesday 15:00 CET =
14:00Z.

## 5. Breach and pause

`GET /tickets/{id}/sla` returns

```
{ priority, ack_due_at, resolve_due_at,
  ack_breached: boolean, resolve_breached: boolean, paused: boolean }
```

evaluated at `now` (the clock of that request, else real time):

- `ack_breached` = the ticket has not been acknowledged and `now > ack_due_at`, or it was acknowledged and
  `acknowledged_at > ack_due_at`. Equality is not a breach.
- `resolve_breached` = the ticket has not been resolved and `now > resolve_due_at`, or it was resolved and
  `resolved_at > resolve_due_at`. A reopened ticket is "not resolved" again; `resolve_due_at` does not change.
- `paused` = the ticket is not resolved or closed, its resolution target runs on the business-hours clock, and `now`
  is outside a business window. For a ticket whose targets are wall-clock, `paused` is always false.

## 6. State machine and reopen window

| action | endpoint | from | to | side effect |
|---|---|---|---|---|
| acknowledge | `POST /tickets/{id}/ack` | new | acknowledged | `acknowledged_at = now` |
| start | `POST /tickets/{id}/start` | acknowledged | in_progress | - |
| resolve | `POST /tickets/{id}/resolve` | in_progress | resolved | `resolved_at = now` |
| close | `POST /tickets/{id}/close` | resolved | closed | `closed_at = now` |
| reopen | `POST /tickets/{id}/reopen` | resolved (always); closed (only under C2 = `reopen`) | in_progress | clears `resolved_at` and `closed_at` |

Every other transition, including shortcuts such as resolve from `acknowledged` or close from `in_progress`,
returns `409 Conflict` with `{"error": {"code": "invalid_transition", ...}}`. Actions on an unknown id return 404.
Successful actions return 200 with the full ticket.

**Reopen window.** Reopen is allowed while `now <= resolved_at + 7 days` for a resolved ticket, and while
`now <= closed_at + 7 days` for a closed ticket where C2 permits it; otherwise 409. Decision C2:

| C2 | behaviour |
|---|---|
| `reopen` | reopen allowed from `resolved` and from `closed` within the 7-day window |
| `immutable` | reopen allowed from `resolved` only; a closed ticket answers 409 regardless of age, and the client creates a new ticket with `related_to` |

Reopen from `resolved` within 7 days works under both; after 7 days it is 409 under both.

Error `code` strings are recommended (`invalid_transition`, `reopen_window_expired`, `ticket_closed`, `not_found`)
but **not checked in Lab 1**; only the status and the presence of a top-level `error` object are.

## 7. Validation and errors

`title` is required, 1..200 characters; `description` is optional, at most 4000; `reporter.name` is required;
`impact` and `urgency` are required integers in 1..3 (a string such as `"high"` is an error). On error the service
returns 400 or 422 and a JSON body with a top-level `error` object, for example
`{"error": {"code": "validation", "message": "title is required"}}`. Server-owned and unknown fields in the request
are ignored (section 2), never an error. Unknown ids and unknown paths return 404 with a JSON body (section 1).

A worked example. The request `POST /tickets` with the header `X-Test-Clock: 2026-10-14T10:00:00Z` (T1) and
the body

```json
{"title": "Printer on floor 2 is down", "description": "Nobody on the floor can print.",
 "reporter": {"name": "Anna Nowak", "email": "anna.nowak@example.com", "vip": false},
 "impact": 2, "urgency": 1, "related_to": null}
```

answers `201` with the full ticket (a P2 by the matrix; every timestamp of an event that has not happened is
`null`; the `sla` block is computed by the service, here on the business-hours clock):

```json
{"id": "6f1c2c1e-3f0a-4b7e-9a51-2a1c6d8e0f11",
 "title": "Printer on floor 2 is down", "description": "Nobody on the floor can print.",
 "reporter": {"name": "Anna Nowak", "email": "anna.nowak@example.com", "vip": false},
 "impact": 2, "urgency": 1, "priority": "P2", "state": "new",
 "created_at": "2026-10-14T10:00:00Z", "acknowledged_at": null, "resolved_at": null, "closed_at": null,
 "related_to": null,
 "sla": {"ack_due_at": "2026-10-14T11:00:00Z", "resolve_due_at": "2026-10-15T10:00:00Z"}}
```

The same request without `title` answers `422` (or `400`) with

```json
{"error": {"code": "validation", "message": "title is required"}}
```

and `GET /tickets/does-not-exist` answers `404` with `{"error": {"code": "not_found", "message": "..."}}`.

## 8. Test clock

When the environment variable `SVCDESK_TEST_CLOCK` is `1` or `true`, every request may carry an `X-Test-Clock`
header with an RFC 3339 instant that includes an offset (`Z` recommended; a naive timestamp is malformed). For that
request, and only for that request, `now` is that instant: it sets `created_at`, `acknowledged_at`, `resolved_at`,
`closed_at`, and it is the reference for breach, pause and the reopen window. **`now` is per request only: the
service never compares one request's clock with another's, never enforces monotonic time, and never rejects an
action because its clock is earlier than a stored timestamp.** `GET /tickets` and `GET /tickets/{id}` contain no
clock-dependent field, so the header is irrelevant there. A header that does not parse returns 400 or 422. Without
the header, `now` is real UTC time. When the variable is unset or `0`, the header is ignored. The template's compose
file sets the variable; the checker sends the header on every request.

## 9. Compose contract

At the repository root, `docker-compose.yml` (or `compose.yaml`; the checker and the grader look for
`compose.yaml`, `compose.yml`, `docker-compose.yml`, `docker-compose.yaml` in that order, the first found wins,
plus the matching `*.override.*` file if present) defines:

- a service named exactly `svcdesk` that **builds from the repository** (`build:` with a context inside the repo;
  a service with `image:` and no `build:` fails check 1.01, while the Dockerfile may of course start `FROM` any
  public base image), listens on port **8080** inside the container, and sets `SVCDESK_TEST_CLOCK: "1"`;
  publishing `8080:8080` to the host is recommended for local development (the checker removes the publication
  in container mode and needs it in native mode; see the course README);
- optionally a service `tests` under `profiles: ["tests"]` (Stretch S3) that reads the service URL from the
  environment variable `SVCDESK_URL` (default `http://svcdesk:8080`);
- **no host-path bind mounts on any service** (named volumes and `tmpfs` are fine; check 1.02 looks at the
  resolved configuration, `docker compose config`, so an override file, a `.env` variable or a named volume with
  bind driver options does not hide one): the checker runs `docker compose` from inside a container, where host
  paths do not resolve;
- images that need **no network at run time** (dependencies are installed at build time): the grading sandbox has no
  egress once the images are built. This holds for the `tests` service too: every image is built up front with
  `docker compose --profile tests build` before egress is blocked (a tests image that does not build costs S3
  and never Core), and the suite itself must reach nothing but `SVCDESK_URL`.

Limits: `docker compose --profile tests build` is untimed in Tier A; Tier B kills it after 300 s (its Stage 1 job
has 15 minutes in total). `docker compose --profile tests run --rm --build tests` is killed after 300 s in both
tiers and S3 then fails.

The checker runs `docker compose --profile tests build` untimed, then `docker compose up --wait svcdesk`; from
that `up` the service must be running and `GET /health` must answer 200 within 120 s. A healthcheck is recommended
but not required (the checker polls `/health` itself).

## 10. Persistence

Tickets survive a restart of the `svcdesk` container (a SQLite file in a named volume is enough). Not checked in
Tier A for Lab 1; it becomes relevant in Lab 2.
