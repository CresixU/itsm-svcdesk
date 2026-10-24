---
lab4_postmortem:
  ticket: "3ba75e92-1b55-483b-a69e-6097c02b182c"
  detecting_alert: ShopCheckoutSlow
  onset: 2026-10-12T05:01:00Z
  detection: 2026-10-12T05:06:19Z
  acknowledgement: 2026-10-12T05:06:56Z
  recovery: 2026-10-12T05:08:19Z
  mttd_seconds: 319
  mtta_seconds: 37
  mttr_seconds: 439
  identified_flags: [intlShippingSlowdown, adFailure, emailMemoryLeak]
---
<!-- ai-generated: 85% - Claude Code drafted this postmortem from the queries it ran on the recorded snapshot; the author reviews the claims and owns them -->

# Postmortem: checkout orders took 8-9 seconds and the storefront returned errors for nine minutes

## Date

The incident happened on 2026-10-12, from 05:01:00Z to 05:10:10Z. This postmortem was written on 2026-10-24, after the fact, from the Prometheus snapshot and the P1 ticket of the lecturer's recording `lab4-rec-1`.

## Authors

Written in the role of the on-call engineer, with the help of an AI assistant (Claude Code) that ran the queries and drafted the text. I worked the incident only through its metrics, as the recorded path allows: the page, the ticket and its acknowledgement are the recording's, not mine.

## Status

Complete for the incident record, which is the closed P1 ticket. The action items are open and their bug ids are below. The problem record at the end stays open until the causes are gone.

## Summary

For about nine minutes, from 05:01:00Z to 05:10:10Z, three faults ran in the shop at once: international orders waited 8-9 s for shipping, one `GetAds` call in fifteen failed, and the email service leaked memory. Orders that hit the slow shipping path took longer than 5 s, and checkout's p99 was above 8 s in the 5-minute windows that held them.

## Impact

Measured on the snapshot, each number with the query that produced it (instant queries, the evaluation time in brackets).

- Checkout slowness: the p99 of checkout's `PlaceOrder` over 5 minutes was 9,050 ms at 05:06:00Z and 8,450 ms at 05:08:00Z, against 50-90 ms on the baseline: `histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout", span_kind="SPAN_KIND_SERVER"}[5m])))`.
- How many orders: about one order of about 79 (12 minutes to 05:13:00Z) took longer than 5 s: `sum(increase(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout", span_kind="SPAN_KIND_SERVER", le="+Inf"}[12m])) - sum(increase(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout", span_kind="SPAN_KIND_SERVER", le="5000"}[12m]))`. The p99 is high because checkout has only 0.15 requests a second: in a 5-minute window one slow order is the p99.
- Failed ad requests: about 7 of 106 `GetAds` calls failed (7 %), and about 15 of 2,928 storefront requests (0.5 %): `sum(increase(traces_span_metrics_calls_total{service_name="ad", span_name="oteldemo.AdService/GetAds", status_code="STATUS_CODE_ERROR"}[12m]))` and the same with `service_name="frontend", span_kind="SPAN_KIND_SERVER"`.
- Email: its resident memory grew from 55 MB to 96 MB and its p99 from about 40 ms to about 185 ms: `max_over_time(container_memory_usage_total_bytes{container_name="email"}[12m])`. No order failed because of it, but checkout waits for the confirmation e-mail.
- Nobody was refused an order: checkout had no failed spans (`CheckoutErrorRate` never held on this snapshot).

## Root Causes

Three feature flags failed at once, one of each class. The flags are an inference from the metrics: the recorded path has no flag state to read.

- `intlShippingSlowdown` (10 s variant): `POST /ship-order` of `shipping` had a p99 of 9,050 ms at 05:06:00Z against 3.3 ms on the baseline, and the same orders are the slow ones in checkout. Query: `histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="shipping", span_name="POST /ship-order"}[5m])))`.
- `adFailure`: the `ad` service failed `oteldemo.AdService/GetAds` at 0.0083 calls a second out of 0.129 (6.4 %), about one in fifteen, and the storefront inherited it. No other service had failed spans except `flagd` (its event stream), which is the demo's own noise.
- `emailMemoryLeak`: the memory of the `email` container grew by 75 % during the fault and fell back after it, and its latency rose fivefold.

I ruled the others out by what the metrics did not show: no failed spans in `payment` (so not `paymentFailure`) or `product-catalog`, a flat p99 of `GetProduct` near 46 ms (so not `productCatalogLockContention`), the frontend request rate unchanged near 4.2 a second (so not `loadGeneratorFloodHomepage`), flat memory of `recommendation` (so not `recommendationCacheFailure`), and `ad` latency unchanged (so not `adManualGc`).

## Trigger

All three flags switched on together at 05:01:00Z, the first sample of the injector's `seeded_fault_active`. No deployment or change of ours preceded it: the trigger was the injector, and in a real system it would have been a configuration change. Nothing in the metrics distinguishes the three flags at the onset, because their symptoms appear at their own pace: the ad errors, visible from 05:02:30Z, the memory growth of the email service over several minutes, the slow shipping call only when an international order happens to arrive.

## Resolution

The flags were switched off at the injector. The injector's `seeded_fault_active` fell to 0 at 05:10:10Z, so all three were off by then; the metrics do not say in which order they were switched off, and I do not claim an order. The detecting alert had already resolved at 05:08:19Z, before the faults ended, because its 5-minute window had moved past the slow orders: checkout's p99 fell from 8,450 ms at 05:08:00Z to 334 ms at 05:10:00Z. The recovery of the incident record is therefore earlier than the end of the fault, as the rules of the laboratory define it; the problem is not solved until the flags are off, and the problem record says so.

## Detection

`ShopCheckoutSlow` (P1, on the p99 of checkout) started firing at 05:06:19Z, 5 minutes 19 seconds after the onset (MTTD 319 s). `ShopServiceErrors` and `ShopServiceSlow` (P2) started in the same second. The first notification reached the pager at about 05:06:35Z (the first sample of `itsm_pager_notifications_total{receiver="pager", status="firing"}`), a few seconds after the alert plus the 10-second group wait; the ticket was created at 05:06:36Z and acknowledged at 05:06:56Z, 37 seconds after the detection (MTTA). The two P2 alerts reached chat only at 05:08:35Z (`itsm_pager_notifications_total{receiver="chat", status="firing"}`), after the P1 had resolved: the routing tree mutes P2 while a P1 of the same system is firing, so chat did not hear about the failing ad service during the page.

Without that alert nobody would have noticed: the ad errors were 0.5 % of the storefront's requests and the shop stayed up. The shop's metrics arrive once a minute and the alerts use 5-minute windows, so an alert on them is slow to move, and the p99 of a service with 0.15 requests a second needs a slow order to arrive first.

What my own alerts would have done on the same data (evaluated on the snapshot, not run during the incident): `CheckoutLatencyHigh` (p99 of checkout above 2 s, `for: 1m`) is true from 05:04:30Z, so it would have paged at about 05:05:30Z, 49 seconds before the recording's page; `FrontendErrorRate` (P2) is true from 05:04:00Z and would have gone to chat; `CheckoutErrorRate` and `FrontendLatencyHigh` would have stayed quiet, as they did on the 15-minute baseline.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a P2 alert on the p99 of `POST /ship-order` in shipping, so that the page names the slow dependency and not only the slow checkout | mitigate | shop platform team | ITSM-101 |
| Give checkout a 2-second timeout and a fallback shipping quote for the call to shipping, so that one slow dependency cannot hold an order for ten seconds | prevent | checkout service owner | ITSM-102 |
| Alert on the memory growth of the `email` container (rate of change over 10 minutes), before it is killed | prevent | shop platform team | ITSM-103 |
| Put "what changed recently: read the flags first" at the top of the on-call runbook, with the command that lists the failing flags | process | on-call lead | ITSM-104 |
| Replace the p99 of 0.15 requests a second in the checkout page by a count of orders slower than a threshold, so that one slow order is not the whole signal | other | service desk manager | ITSM-105 |

## Lessons Learned

### What went well

The page reached the pager a few seconds after the alert, the P1 ticket was acknowledged 37 seconds after the detection, and the three alerts that fired together were routed by severity: the P1 to the pager, the two P2 held back from chat while the page was firing, without a second page for the same incident.

### What went wrong

Detection took 5 minutes 19 seconds because the shop's metrics arrive once a minute and every alert has a 5-minute window. Three faults ran at once and one alert named only the symptom (checkout slow), so the causes had to be found by hand. The detecting alert resolved at 05:08:19Z while the faults were still on until 05:10:10Z, which made the incident look over early, and the inhibition kept the ad errors out of chat until 05:08:35Z.

### Where we got lucky

Only about one order in 79 hit the slow shipping path, and the ad failure touched an optional part of the page, so no customer was refused an order. The email service gained 41 MB in nine minutes and its memory fell back afterwards; a faster variant of the same leak could have taken it down in the middle of an order.

## Timeline

All instants in UTC, on 2026-10-12.

- 04:46:00 the injector starts, and the 15-minute baseline begins; every rule of mine is quiet on it.
- 05:01:00 onset (2026-10-12T05:01:00Z): `seeded_fault_active` becomes 1; three flags are failing from this instant.
- 05:02:30 the storefront error ratio is above 0.2 % for the first time (ad failures; my `FrontendErrorRate` would be pending).
- 05:04:30 the p99 of checkout is above 2 s for the first time (my `CheckoutLatencyHigh` would be pending).
- 05:06:19 detection (2026-10-12T05:06:19Z): `ShopCheckoutSlow` (P1) starts firing; `ShopServiceErrors` and `ShopServiceSlow` (P2) start a second later.
- 05:06:35 the first firing notification reaches the pager (counter `itsm_pager_notifications_total{receiver="pager"}`).
- 05:06:36 the P1 ticket `3ba75e92-1b55-483b-a69e-6097c02b182c` is created in svcdesk.
- 05:06:56 acknowledgement (2026-10-12T05:06:56Z): the ticket is acknowledged, 37 seconds after the detection.
- 05:08:19 recovery (2026-10-12T05:08:19Z): `ShopCheckoutSlow` stops firing, because its window has moved past the slow orders; `ShopServiceSlow` stops at the same time.
- 05:08:35 the two P2 alerts are notified to chat for the first time, after the P1 has resolved; the pager gets the resolved notification.
- 05:10:10 all three flags are off: `seeded_fault_active` becomes 0.
- 05:13:15 `ShopServiceErrors` (P2) stops firing.

The AI investigator (the course agent loop with `gemini-3.8-flash`, `ai-rca/transcript.md`) worked the snapshot after the fact, so its hypotheses sit outside the clock above. The ones I acted on, each with its ledger id (`ai-rca-eval.json`) and the query that tested it, all evaluated at 2026-10-12T05:08:00Z, in the middle of the fault, with the baseline five minutes before the onset:

- **H1**, verdict correct: "shipping is slow". I took it as the lead for `intlShippingSlowdown`. Query: `histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="shipping", span_name="POST /ship-order"}[5m]))) > 5000` returned 8,450 ms at 05:08:00 and nothing at 04:56:00. The agent had read the service from the labels of `ShopServiceSlow`, so this one is the alert's, not its own discovery.
- **H4**, verdict partially correct: "the ad service fails". I took the failures for `adFailure` and discarded its "timeout latency". Query: the `GetAds` error share `> 0.02 unless on()` the p99 of `GetAds` `> 1000` returned 10.5 % at 05:08:00 and nothing on the baseline; the p99 itself was 7.7 ms.
- H5 (the ad failures caused by flag-stream timeouts, hallucinated) I did not act on.

No investigator mentioned the email service, so `emailMemoryLeak` is not in the ledger: I found it myself, from `max_over_time(container_memory_usage_total_bytes{container_name="email"}[12m])` (55 MB before, 96 MB at the peak) and the p99 of the email service rising from about 40 ms to about 185 ms.

## Supporting information

The four instants and the three durations are what `itsmlab incident 4` prints for this snapshot (run `65125b2a3e80aecf`): onset 05:01:00Z, detection 05:06:19Z, acknowledgement 05:06:56Z, recovery 05:08:19Z; MTTD 319 s, MTTA 37 s, MTTR 439 s. The snapshot is `incident/tsdb-snapshot.tar.gz` and the ticket `incident/ticket.json`, both the recording's own, unchanged. The queries of the Impact and Root Causes sections run on the snapshot served at http://localhost:19090 (`prom/prometheus:v3.15.0` on the unpacked blocks). The AI investigator's transcript is `ai-rca/transcript.md` and its scored hypotheses are in `ai-rca-eval.json`.

## Problem record

- Incident record: the P1 ticket 3ba75e92-1b55-483b-a69e-6097c02b182c in svcdesk, acknowledged at 2026-10-12T05:06:56Z; the incident is closed when service is restored.
- Root cause: three feature flags failing together - a 10-second shipping slowdown for international orders, a failing ad service on one call in fifteen, and a memory leak in the email service - with checkout waiting synchronously for shipping and for the e-mail.
- Known error: checkout has no timeout or fallback on the shipping and e-mail calls, so any slowdown of either becomes a slow order; the symptom is seen first by checkout's p99, which is dominated by single slow orders at this traffic.
- Workaround: switch the failing flags off at the injector (`POST /flags/<flag>/off`); until the causes are fixed, watch the p99 of `POST /ship-order` and the memory of the email container as well as checkout.
