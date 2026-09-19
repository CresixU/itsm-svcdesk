<!-- ai-generated: 90% - Claude Code drafted this comparison after implementing src/; the author reviewed it against the running service -->
# Convergence report - specification vs. implementation

A comparison of [spec.md](spec.md) (written before any code) against what `src/svcdesk` actually does, checked
against the running service with `./itsmlab.ps1 verify 1`.

## Priority (R-04, R-05, R-06)

Spec: the matrix (R-04) decides first; under C3 = `vip` a VIP ticket computed at P3 or P4 is raised to P2, P1/P2
unaffected. Implementation: `priority.compute_priority` applies `MATRIX` then the VIP override exactly this way;
`main.create_ticket` ignores any `priority` field in the request body because `CreateTicketIn` has no such field
(`extra="ignore"`), which is R-05's "and from nothing else" clause, kept everywhere except the VIP case C3
deliberately rejects. Verified live: check 2.46 (VIP at impact 3/urgency 3) observes `P2`, check 2.47 (VIP at
impact 1/urgency 1) observes `P1`, check 2.48 confirms a `priority` field in the body changes nothing.

## State machine and reopening (R-07, R-08, R-09, R-10, R-11)

Spec: five states, one endpoint per transition, closed tickets reachable from `resolved` only via `close`; under
C2 = `reopen`, `reopen` also works from `closed` within 7 days of `closed_at`. Implementation: `main._apply_transition`
enforces exactly this table and raises `ApiError(409, ...)` for every other transition, including resolve-from-new
and close-from-new (R-08). Reopen clears `resolved_at` and `closed_at` without touching `acknowledged_at` or the
stored SLA due instants (R-11). Verified live: check 2.35 (reopen a ticket closed 1 day earlier) observes `200`
with `in_progress`, matching the declared C2.

## SLA clocks (R-12, R-13, R-14, R-15, R-16)

Spec: P2-P4 always use the business-hours clock; under C1 = `wallclock`, P1's ack and resolve targets never pause.
Implementation: `sla.ack_clock_for` / `resolve_clock_for` return `"wallclock"` only for P1 under this decision, and
`sla.due_at` dispatches to either `created_at + timedelta` or `_add_business_minutes`. The business-hours algorithm
was hand-verified against all eight vectors in API.md section 4 (T1-T8) before wiring it into the service, including
the Saturday tie-at-closing case (T4) and the vector that crosses the DST-end weekend (T8); the running service
reproduces every one exactly. `paused` (R-16) is computed from `resolve_clock`, so it is unconditionally `false` for
P1 - checked live at check 2.45 (paused Saturday, not paused Monday, both on a P3 ticket).

## Validation and errors (R-20, R-25)

Spec: 400/422 with a top-level `error` object for anything R-03 forbids; 404 with the same shape for unknown ids
and paths. Implementation: `models.CreateTicketIn` rejects out-of-range `impact`/`urgency` and over-length
`title`/`description` via field validators; three exception handlers (`ApiError`, `RequestValidationError`,
`StarletteHTTPException`) normalise every error response, including framework-generated 404s for unknown routes,
to `{"error": {...}}`. Verified live: checks 2.16-2.19 (validation), 2.02 and 2.21 (404s).

## What did not change

`related_to` is stored and returned but never validated against an existing id, and `GET /tickets` has no
pagination - both exactly as scoped out in spec.md section 9, since the checker never creates more than 100
tickets in a run (R-19).
