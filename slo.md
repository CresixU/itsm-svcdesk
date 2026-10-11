---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 28d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"2.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"4.."}[5m]))'
      error_budget: {fraction: 0.01, minutes: 403.2}
    latency:
      objective: 0.99
      threshold_seconds: 0.15
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", http_response_status_code=~"2..", le="0.15"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code=~"2.."}[5m]))'
      error_budget: {fraction: 0.01, minutes: 403.2}
  alerts:
    - {alert: KbSearchAvailabilityBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchAvailabilityBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
    - {alert: KbSearchLatencyBurnFast, sli: latency, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchLatencyBurnSlow, sli: latency, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 90% - Claude Code wrote the queries and the prose from the checker's own measurements of my profile (login cresixu); the objectives are Claude's proposal, which I review and own -->

# SLO for `GET /kb/search`

What I measured, with `itsmlab load 3` (60 s open-loop at 40 requests/s, latency-corrected, two runs): the latency of
`/kb/search` is bimodal. A fast mode holds about 95 % of the requests (p50 16.7 ms, p90 23.4 ms, p95 29.6 ms); a narrow
slow mode at roughly 70-125 ms holds the other 4-5 %, and the p99 sits inside it (q = 94.7 ms in the last run, 93.7 ms in
the first; p99.9 104-112 ms, p99.99 112-125 ms). `kb-index` itself fails 6 of 2,400 searches (0.25 %) in both runs, and it
fails after its latency, so a failed request is as slow as a successful one. `svcdesk` answers such a request 502 without
a retry, as M-02 requires, so whatever `kb-index` fails, `svcdesk` fails.

Both SLIs are the proportion of valid events that were good, over the 28-day window. A request that the caller got
wrong (a 4xx, for example a missing `q`) is not a valid event for either: it says nothing about the service.

## Availability

*SLI:* valid events are `/kb/search` requests that did not get a 4xx; good events are those answered 2xx. *Objective:*
0.99, so the error budget is 1 % of the valid requests, which is 0.01 x 40,320 minutes = 403.2 minutes of a 28-day window.

Why 0.99 and not more. The share of searches `kb-index` fails by itself is about 0.25 % (0.17 % on the published
practice profile), and `svcdesk` has no retry and no cache to hide it, so the availability `svcdesk` can offer is that
of its dependency, about 99.75 %. An objective of 0.999 would be one the service cannot meet: `kb-index` alone would burn
that budget 2.5 times as fast as it accrues, and the slow-burn alert would fire permanently. At 0.99 the dependency's
ordinary failures consume about a quarter of the budget (a baseline burn rate of 0.25), which leaves three quarters for
what I control - my own releases and incidents - and none of the alerts below fires on a normal day. 0.995 would also be
defensible on paper, but its baseline burn rate of 0.5 would leave a single bad hour of `kb-index` with little room before
the ticket-level burn rate of 1, and Lab 6 will use this objective as a canary gate: I would rather the gate roll back a
release that really doubles the failure rate than one that met an objective the dependency was already half using.

## Latency

*SLI:* valid events are the `/kb/search` requests answered 2xx (the failures are the availability SLI's business, and
counting them here would count them twice); good events are those answered within **0.15 s**. *Objective:* 0.99, an error
budget of 1 % and 403.2 minutes.

Why 0.15 s. It is not the p99. The p99 (94.7 ms) sits inside the slow mode, which is normal behaviour of this dependency
and holds 4-5 % of the requests: a threshold inside the mode, say 0.1 s, would make that normal 4-5 % partly "bad" (about
0.3 % of the requests are above 0.1 s in my runs) and would burn a third of the budget every day with nothing wrong. 0.15 s
is above the whole healthy distribution - the slowest one in ten thousand requests took 112-125 ms - and 20-30 % above it,
so an answer slower than 0.15 s means that something changed: `kb-index` degraded, or `svcdesk` is queueing. It is also a
boundary of the ladder (M-13), so the SLI counts requests and does not interpolate them. If the slow mode got 30 % slower,
all of its 4-5 % would cross the threshold and the SLI would drop to about 95-96 %, which is far inside the alert range.

Why 0.99. In the healthy state about 99.99 % of the requests are good, so 0.99 is deliberately loose compared with today's
performance: it leaves the budget to releases, and 150 ms is already a latency that the service desk agent does not notice
in a search box. A tighter objective would also be met today, but Lab 6 will use this threshold and objective as the gate
of a canary: I want that gate to react to a real regression of the slow mode and not to the noise of a few hundred requests.

## Alerts

All four alerts are multiwindow, multi-burn-rate (SRE Workbook, chapter 5): each fires only when both the long and the short
window burn the budget faster than the burn rate, so that it fires after a real burn and stops soon after the burn stops. The
budget spent when an alert fires is burn rate x long window / 28 days (672 h).

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---|---|---|---|
| KbSearchAvailabilityBurnFast | availability | 14.4 | 1h / 5m | 14.4 x 1 h / 672 h = 2.1 % | P1: page |
| KbSearchAvailabilityBurnSlow | availability | 6 | 6h / 30m | 6 x 6 h / 672 h = 5.4 % | P2: chat |
| KbSearchLatencyBurnFast | latency | 14.4 | 1h / 5m | 2.1 % | P2: chat |
| KbSearchLatencyBurnSlow | latency | 6 | 6h / 30m | 5.4 % | P3: chat |

**What pages a person.** Only `KbSearchAvailabilityBurnFast`. At a burn rate of 14.4 one search in seven fails (14.4 % bad
against a 1 % budget), the whole 28-day budget would be gone in about 47 hours, and users are being refused answers right
now: an agent who cannot find the known error for a ticket is working that ticket blind. A page at that rate costs the
person woken an interrupted night and a decision they can mostly act on only partly - the cause is often `kb-index`,
which is not ours to repair - so the page is justified only because of what waiting costs the other side: until morning (8
hours) the alert would have spent 14.4 x 8 / 672 = 17 % of the month's budget, and about 14 % of every search in those hours
would have failed. The same burn rate on latency does not page: the searches still come back, just slower than 150 ms, so
the desk can work, and the same eight hours would spend the same 17 % of a budget that a person can read in chat when the
day starts. That is P2.

**What goes to chat.** The slow burns - 6x over six hours, which empties the budget in 4.7 days - are exactly the kind of
problem that does not get worse faster than somebody can read a message: waiting until morning costs 6 x 8 / 672 = 7 % of
the budget, which a person woken at 3 a.m. could not usefully give back. Availability's slow burn is P2 because failures
are users' failures; latency's slow burn is P3, a ticket to look at during the day.

## Buckets

My ladder has 28 finite boundaries (the limit is 30), in seconds: 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06,
then 5 ms steps from 0.07 to 0.12 (0.07, 0.075, 0.08, 0.085, 0.09, 0.095, 0.1, 0.105, 0.11, 0.115, 0.12), then 0.13, 0.14,
0.15, and 0.2, 0.3, 0.5, 1.0, 2.5.

My q is 94.7 ms and it falls in **(0.09, 0.095]**, a bucket 5 ms wide, **5.3 % of q** (M-11 allows 20 %). The grader's q will
differ from mine by a few per cent - another machine, other 2,400 random draws, and in my two runs the p99 already moved
from 93.7 to 94.7 ms while the p99.99 moved from 112 to 125 ms, which shows how much the top of the slow mode shifts - so I
did not fine-tune one bucket around 94.7 ms. I resolved a band: every bucket from 0.05 to 0.15 s is at most 10 ms wide, and
every bucket across the slow mode, 0.07 to 0.12 s, is 5 ms wide. A q anywhere in 0.05-0.15 s, from 47 % below mine to 58 %
above it, lands in a bucket of at most 20 % of that q (for the ±10 % band of the handout, 85-104 ms, the requirement is
17 ms at most and mine are 5 ms). The remaining boundaries went where the other things I read live: nine in the fast mode
(5-60 ms, so that the median of 17 ms and the p95 of 30 ms are resolved on the dashboard too), the 10 ms steps up to the
latency threshold at 0.15 s, which is a boundary as M-13 requires, and a coarse tail (0.2 to 2.5 s) because a request
there is a fault whatever its exact duration; the timeout towards `kb-index` is 3 s, so slower answers land in `+Inf`.
