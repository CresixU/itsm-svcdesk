---
lab3_first_draft:
  source: ai
  tool: "Claude Code (Claude Sonnet 5.5), in the session that built the rest of this lab, 11 October 2026; the lab documents had already been read in that session, the measurement had not been made"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 2.5, 5.0]
  verdict: refuted
  evidence: {p99_seconds: 0.0947, bucket: [0.075, 0.1], relative_width: 0.264}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.0947, bucket: [0.04, 0.5], relative_width: 4.857}
---
<!-- ai-generated: 90% - the prompt is mine, the answer is Claude's verbatim, the verdicts and arithmetic below are Claude's drafts checked against the checker's own measurement -->

# The assistant's first draft, and two verdicts

## Prompt

I am adding a knowledge-base search endpoint, `GET /kb/search?q=<text>`, to a Python (FastAPI) service. Every request makes one HTTP call to an upstream search index and answers with its hits (200), or with a 502 when the upstream fails or times out. I export a Prometheus histogram called `http_server_request_duration_seconds`, in seconds, with the labels `http_request_method`, `http_route` and `http_response_status_code`. I do not know yet what the latency distribution looks like. Please give me (1) the histogram bucket boundaries you recommend, at most 30 of them, and (2) a Prometheus alert rule for this endpoint.

## Answer

> Since you do not know the distribution yet, I would start with a roughly exponential ladder, about 1.5x to 2.5x per step, that spans a few milliseconds up to a few seconds, with a few extra boundaries in the 100-500 ms range, where the tail of an HTTP call to an upstream search index usually lands:
>
> ```python
> buckets = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 2.5, 5.0]
> ```
>
> That is 14 finite boundaries in seconds; Prometheus adds `+Inf` itself. It is a reasonable starting point rather than a final answer: once you have real traffic, look at where your p50 and p99 fall and move the boundaries so that the buckets around them are narrow.
>
> For the alert, here is a rule that fires when the error ratio of the endpoint stays high, plus one on the latency tail:
>
> ```yaml
> groups:
>   - name: kb-search
>     rules:
>       - alert: KbSearchHighErrorRate
>         expr: |
>           sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search", http_response_status_code=~"5.."}[5m]))
>             /
>           sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search"}[5m]))
>             > 0.05
>         for: 5m
>         labels:
>           severity: page
>         annotations:
>           summary: "More than 5% of /kb/search requests are failing"
>
>       - alert: KbSearchSlowP99
>         expr: |
>           histogram_quantile(0.99,
>             sum by (le) (rate(http_server_request_duration_seconds_bucket{http_route="/kb/search"}[5m]))
>           ) > 0.5
>         for: 10m
>         labels:
>           severity: ticket
>         annotations:
>           summary: "p99 of /kb/search is above 500 ms"
> ```
>
> If you later define an SLO for the endpoint, replace the fixed 5% threshold with a multiwindow burn-rate rule (for example a burn rate of 14.4 over 1h and 5m) so that it pages on budget consumption rather than on a raw percentage.

## Verdict on the draft ladder

**Refuted.** I measured with `itsmlab load 3` (60 s open-loop at 40 requests/s, latency-corrected, login `cresixu`): p50 16.7 ms, p95 29.6 ms, **p99 = 94.7 ms** (q_kb 90.6 ms, so there is no bypass). The latencies are bimodal: a fast mode around 13-40 ms and a narrow slow mode at roughly 70-125 ms that holds about 4-5 % of the requests, and the p99 sits inside the slow mode. (An earlier run of the same command gave 93.7 ms; I use the 0.0947 s of the last one.)

The draft ladder is `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 2.5, 5.0]`. The bucket of it that contains 0.0947 s is **(0.075, 0.1]**: the largest boundary below the p99 is 0.075 and the smallest at or above it is 0.1. Its width relative to the p99 is (0.1 - 0.075) / 0.0947 = 0.025 / 0.0947 = **0.264, i.e. 26.4 %**, above the 20 % that M-11 allows. The same bucket holds 0.95q (0.0900) and 1.05q (0.0994), so the result does not depend on where the grader's q falls, and 26.4 % is outside the "too close to call" band of 16-24 %: the measurement allows only `refuted`.

What `histogram_quantile` could report from that bucket: it assumes the requests inside a bucket are spread evenly over it, so for a p99 that falls in (0.075, 0.1] it can report any value from 75 ms to 100 ms, that is from 21 % below to 6 % above the true 94.7 ms, and nothing on the dashboard would show which. The assistant's ladder was reasonable as a generic answer - it is denser than the library defaults between 50 and 300 ms - but its nearest boundaries around this particular slow mode are 75 and 100 ms, 25 ms apart, and a p99 that moves by 10 ms never crosses one.

## The draft alert rule

The assistant gave two rules: `KbSearchHighErrorRate` (the 5xx share of `/kb/search` over 5 minutes above 5 % for 5 minutes,
`severity: page`) and `KbSearchSlowP99` (`histogram_quantile(0.99, ...)` over 5 minutes above 0.5 s for 10 minutes,
`severity: ticket`), and it said itself that a fixed threshold should become a multiwindow burn-rate rule once there is an SLO.

What the first one would have done for my SLO (availability 0.99, a budget of 1 %): 5 % is a burn rate of 5, but over one
5-minute window only. A burn of 5 that lasts five minutes spends 5 x 5 / 40,320 = 0.06 % of the 28-day budget and would page
someone; a steady 4 % error rate, a burn of 4, would never fire and would empty the budget in a week. With `kb-index`
failing 0.25 % of the searches by itself, the baseline is far below 5 %, so it would also be silent through the long, small
burns that matter. It selects no `job`, counts 4xx as valid events, and carries `severity: page`, which is none of the P1,
P2, P3 that Lab 4 routes on, and no `service` and `slo` labels.

The second one would not have fired for any degradation I care about: my p99 is 94.7 ms and my latency threshold is 150
ms, but the rule waits for the p99 to reach 500 ms, five times its normal value, and a p99 computed from a 5-minute rate of a
low-traffic endpoint is noisy. A slow mode that got 30 % slower would burn my latency budget at about 4.5 times its rate and
the p99 would stay under 200 ms.

What I kept: the selector idea (`http_route="/kb/search"` and the 5xx statuses), the `for` clause (2 minutes for the fast
alerts and 15 for the slow ones instead of 5 and 10), and its closing advice, which I followed completely: in
`prometheus/alerts.yml` all four alerts are multiwindow, multi-burn-rate rules (14.4 over 1 h and 5 m, 6 over 6 h and 30 m,
for each of the two SLIs), the threshold is a visible constant (`14.4 * (1 - 0.99)`), and each carries `service`, `slo` and
`severity` P1 to P3. I dropped the fixed 5 % and the p99 rule; the latency alert is now a burn of the latency SLI, whose
threshold is a boundary of my ladder (`le="0.15"`).

## Verdict on the instructor's flawed ladder

**Refuted**, as it always is (M-27). The flawed ladder is `[0.001, 0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.02, 0.025, 0.03, 0.04, 0.5, 2.5]`: twelve of its fourteen boundaries are at or below 40 ms and it then jumps to 0.5 s. For my p99 of 0.0947 s the bucket is **(0.04, 0.5]**, and its relative width is (0.5 - 0.04) / 0.0947 = 0.46 / 0.0947 = **4.857, i.e. 486 %** of the p99. `histogram_quantile` could report anything from 40 ms to 500 ms for it.

Where the resolution is spent is the point: that ladder is dense exactly where this service's median lives (p50 16.7 ms, p90 23.4 ms, so about 90 % of the requests fall in the twelve fine buckets between 1 and 40 ms), and blind where the p99 lives, because the whole slow mode (70-125 ms) sits in one bucket. A dashboard built on it would show a healthy median and a p99 that is a guess of the interpolation. My own ladder (in `slo.md`, section "Buckets") takes the opposite decision: 5 ms steps across the slow mode, so q lands in (0.09, 0.095], 5.3 % of q.
