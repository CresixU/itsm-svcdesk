---
svcdesk_decisions:
  C1: wallclock      # wallclock | business
  C2: reopen         # reopen | immutable
  C3: vip            # matrix | vip
---
<!-- ai-generated: 90% - Claude Code drafted this text from REQUIREMENTS.md and API.md; the author chose all three resolutions after weighing the tradeoffs and reviewed and edited the text -->

# Decisions

## C1 - SLA clock for P1

**Decision:** P1's acknowledge and resolve targets both run on the wall-clock (`created_at + target`): 15 minutes
to acknowledge, 4 hours to resolve, counted straight through nights and weekends with no pause.

**Rejected alternative:** Running P1 on the same business-hours clock as every other priority, so a P1 raised on
Friday evening would pause at 16:00 and not resume until 08:00 Monday, exactly like a P3 or P4.

**Reason:** R-14 states the around-the-clock behaviour in a concrete, testable example - a P1 raised Friday
evening is late at 15 minutes past, not on Monday morning - and that example only holds if the P1 clock never
pauses. We keep R-13's pausing rule for P2 to P4, where the desk's real capacity to act does follow office hours,
and reject it only for the one priority that exists specifically to bypass office hours.

**Service owner:** The on-call incident manager, because P1 is reserved for outages that stop the whole
organisation working, and that role is accountable for a genuine round-the-clock response regardless of the
calendar, not for a promise that quietly pauses overnight.

**Customer outcome:** A reporter whose P1 goes in on a Friday night gets a real 4-hour resolution promise, instead
of one that silently freezes for 64 hours over the weekend and reappears Monday morning as if nothing had happened.

## C2 - Closed tickets and reopening

**Decision:** `POST /tickets/{id}/reopen` is accepted from a `resolved` ticket and from a `closed` ticket alike,
provided the request falls within 7 days of the instant that closed the case (`resolved_at` or `closed_at`
respectively). Outside that window, from either state, reopen is refused with 409.

**Rejected alternative:** Treating `closed` as permanently immutable, so any ticket the reporter has closed
requires a brand-new ticket referencing it through `related_to`, even one day after closing it.

**Reason:** R-10 gives the reporter a 7-day safety net specifically for the case where the fix did not hold, and
that promise is broken if closing the ticket one step earlier than "resolved" removes it. We give up the strict
half of R-09 that forbids any further transition on a closed ticket, while keeping the rest of R-09: a closed
ticket still cannot be edited directly, and the only way back into work is the reopen endpoint, under the same
7-day rule that already governs a merely resolved ticket.

**Service owner:** The service desk team lead, because the 7-day reopen window is a service-level promise made to
the reporter, and letting the state machine cut that promise short at "closed" instead of "resolved" would be a
silent regression the team lead would have to answer for.

**Customer outcome:** A reporter who confirms a fix, then finds the problem back three days later, reopens the
very same ticket and keeps its full history, instead of re-explaining the issue from scratch on a brand-new one.

## C3 - VIP reporters and the priority matrix

**Decision:** The impact/urgency matrix is always computed first; if the reporter is VIP and the matrix result is
P3 or P4, the ticket is raised to P2. P1 and P2 results are unaffected by the VIP flag, and under either resolution
of this decision a `priority` field sent in the request body is always ignored.

**Rejected alternative:** Computing priority strictly from the matrix and nothing else, storing `reporter.vip` only
as metadata that never changes the priority a ticket receives.

**Reason:** R-06 exists because a VIP reporter's issue can look cosmetic by impact and urgency alone (low impact,
low urgency) while still carrying organisational weight the matrix cannot see, and the desk wants that visible
immediately rather than buried behind the ordinary P4 queue. We reject the "and from nothing else" clause of R-05
only for this one case, and keep the rest of R-05 fully intact: neither the reporter nor the agent can request an
arbitrary priority, and the body's `priority` field is always ignored regardless of VIP status.

**Service owner:** The service desk manager, because deciding whose issues jump the ordinary queue is a staffing
and prioritisation call, not a technical one, and that manager answers for the desk's overall throughput if the
exception is ever used more broadly than intended.

**Customer outcome:** A VIP reporter's low-impact request is answered inside a P2 window instead of waiting up to
72 hours behind ordinary P4 traffic, at the cost of the P4 queue for everyone else moving very slightly slower.
