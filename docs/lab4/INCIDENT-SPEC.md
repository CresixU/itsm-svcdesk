<!-- ai-generated: 0% - written by the course team -->
# INCIDENT-SPEC.md - the rules of Lab 4

**This document is the whole rulebook.** Every rule that decides what "correct" means is here: what your alerts and
your routing tree must do, how the four instants of your incident are computed from your snapshot and your ticket,
what the postmortem and the AI ledger must hold, and every tolerance and threshold. Nothing the checker does is
withheld. What is not published is **the fault**: three feature flags, drawn at random when you arm the injector, that
start failing at a moment you do not know. The injector writes the fault into your snapshot sealed, so that only the
grader can read it, and the grader opens it for two checks, 4.06 and 5.06. You may be surprised by the fault; you will
never be surprised by the rules.

Where this document and an assistant disagree, this document wins. And nothing you write down is believed: every
instant, every duration and every AI prediction is recomputed from the two artifacts you ship, the Prometheus
snapshot and the ticket, by the checker's own Prometheus 3.15.0, Alertmanager 0.34.1 and `amtool`. `itsmlab incident
4` prints the same recomputation the grader makes.

Rule ids (`I-01` .. `I-32`) are stable. The checker's messages and [CHECKS.md](CHECKS.md) cite them.

**Words used below.** *The playground* is the OpenTelemetry Demo 3.1.0 with the course overlay
([playground/README.md](playground/README.md)). *The snapshot* is your Prometheus snapshot,
`incident/tsdb-snapshot.tar.gz`; *the checker's Prometheus* is the one the checker and the grader start on a copy of
it, with nothing scraping and nothing deleted. An *instant* is an RFC 3339 timestamp with an offset, compared as a
point in time; write yours in UTC (`2026-10-24T10:41:05Z`). *The pool* is the nine flags of section 2.2. A *run* is
one life of the injector, from its start to the end of the stack.

---

## 1. The playground

The demo's own minimal files plus the overlay: six demo services changed, five added. Everything below is how the
course runs it; the commands are in [playground/README.md](playground/README.md).

| what | address | what matters for the rules |
|---|---|---|
| the shop | http://localhost:8080 | ten simulated users (the load generator) shop all the time; no browser traffic |
| Grafana, Jaeger | http://localhost:8080/grafana, http://localhost:8080/jaeger/ui | the demo's dashboards and traces |
| Prometheus | http://localhost:9090 | evaluates your `prometheus/alerts.yml` and `prometheus/demo-alerts.yml` every **10 s**; scrapes the injector, the pager and `svcdesk` every **5 s**; receives the shop's metrics by OTLP push every **60 s**; runs with the admin API that `itsmlab snapshot 4` uses |
| Alertmanager 0.34.1 | http://localhost:9093 | your `alertmanager/alertmanager.yml`, no clustering |
| the pager | http://localhost:18091 | the on-call's phone (section 3) |
| the injector | http://localhost:18090 | the fault (section 2) |
| your `svcdesk` | http://localhost:18080 | built from your repository, with **the test clock off**: the server stamps every instant, and no request header can set one |

The shop's metrics are span metrics: the demo's collector turns every span into `traces_span_metrics_calls_total`
(a counter) and `traces_span_metrics_duration_milliseconds_bucket` (a histogram in **milliseconds**), with the labels
`service_name`, `span_name`, `span_kind` (`SPAN_KIND_SERVER`, `SPAN_KIND_CLIENT`, `SPAN_KIND_INTERNAL`) and
`status_code` (`STATUS_CODE_ERROR` marks a failed span). One sample a minute: a `rate()` needs a window of at least
5 minutes.

---

## 2. The injector (`seeded-flagd`)

The injector serves the demo's feature flags to flagd, which reads it as a second source that overrides the demo's
own file. Until it is armed, every flag of the pool is `off`.

### 2.1 Interface

| request | answer |
|---|---|
| `GET /flags.json` | the flag document flagd polls (every 5 s): the demo's definitions of every pool flag, each `off` unless it is failing |
| `GET /status` | `{"run", "armed", "baseline_so_far", "baseline_required", "controls": [the pool's flag keys]}` - never which flags fail |
| `POST /arm` | **202** `{"armed_at", "onset_window", "run"}` once the injector has run **10 minutes** (the baseline). It draws the fault, and the onset **2 to 6 minutes** later. **409** before the 10 minutes (the message says how long to wait) and **409** when it is already armed: one fault per run |
| `POST /flags/{key}/off` | switches that flag back to `off`: 200 `{"flag", "changed"}`; `changed: false` for a flag that was not failing; **404** for a key outside the pool |
| `GET /metrics` | `seeded_injector_info{version, run} 1`, `seeded_injector_start_timestamp_seconds`, `seeded_fault_armed`; after arming `seeded_fault_sealed{run, box} 1`; and **from the onset** `seeded_fault_active`: 1 while any seeded flag fails, then 0 |
| `GET /healthz` | 200 |

The fault ends when you have switched all three flags off, or by itself **45 minutes** after the onset, so every run
has a recovery. Switching a flag off before the onset changes nothing: all three switch on at the onset. A flag you
switched off stays off. Restarting the injector starts a new run, with a new run id and a new 10-minute baseline; to
start over, stop the stack with `down -v`, which also deletes Prometheus's data.

### 2.2 The fault pool

One choice from each of three classes - a flag of the class uniformly, then one of its variants - among the
combinations that make checkout fail or slow down: of the 5 x 5 x 3 = 75, the injector never draws the six that pair `adFailure` with `adManualGc` or
`loadGeneratorFloodHomepage`, which touch only the ads and the front page. That leaves 69, and every one of them has
a flag that fails orders (`paymentFailure`, `productCatalogFailure`) or slows them (`intlShippingSlowdown`,
`productCatalogLockContention`).

| class | choices (flag: variant) | where it shows |
|---|---|---|
| errors | `paymentFailure`: 10%, 25%, 50%; `adFailure`: on; `productCatalogFailure`: on | payment and checkout errors; ad errors (1 in 10 GetAds); GetProduct errors for one product in ten |
| latency and load | `adManualGc`: on; `intlShippingSlowdown`: 5sec, 10sec; `productCatalogLockContention`: on; `loadGeneratorFloodHomepage`: on | ad latency spikes; ShipOrder 5 or 10 s slower for non-US orders (about 1 in 9); catalog reads stall 30 s at a time; frontend traffic x15 |
| resources | `emailMemoryLeak`: 100x, 1000x; `recommendationCacheFailure`: on | email out-of-memory kills and restarts; recommendation memory and latency growth |

The services each flag affects (I-28 uses this table; the names are the `service_name` values of the span metrics):

| flag | affected services |
|---|---|
| `paymentFailure` | payment, checkout, frontend |
| `adFailure`, `adManualGc` | ad, frontend |
| `productCatalogFailure`, `productCatalogLockContention` | product-catalog, frontend, checkout, recommendation |
| `intlShippingSlowdown` | shipping, checkout |
| `loadGeneratorFloodHomepage` | frontend, frontend-proxy, load-generator |
| `emailMemoryLeak` | email, checkout |
| `recommendationCacheFailure` | recommendation, frontend |

The demo has more flags; the injector never seeds them. `paymentUnreachable` and `paymentFailure` at 75 % or more
would end every checkout before shipping and email and hide the other two faults; `cartFailure` fails only an
EmptyCart call whose error nobody reads; `adHighCpu` would slow your whole laptop (the demo sets no CPU limits);
`imageSlowLoad` needs browser traffic, which the playground turns off; `kafkaQueueProblems`, `aiRunawayAgent`,
`aiSlowResponse` and `failedReadinessProbe` do nothing in minimal mode. Whatever those parts of the demo do on your
machine is noise, not the fault.

### 2.3 What you can see, and what the AI can see

The live flag state is visible to you, as in any real system: the injector's `GET /flags.json` (a failing flag has a
`defaultVariant` other than `off`), and the `feature_flag.evaluation` span events of checkout, product-catalog,
recommendation and cart in Jaeger. "What changed recently?" is the first question of any on-call, and reading the
answer is part of the investigation, not a leak: the lab grades what you do with it. The demo's flag UI
(http://localhost:8080/feature) edits the demo's own file, which the injector overrides: it is not where to look.

What is **not** in the metrics is which flags fail: no metric names a flag of the pool (the cart service's
`feature_flag_evaluation_*` series name only `cartFailure` and `failedReadinessProbe`, which the injector never
switches). An AI investigator reading Prometheus
through the course's MCP server cannot read the answer off a series.

### 2.4 The sealed fault

When you arm the injector, it writes the fault - the run, the arming instant, the onset and the three flags with their
variants - into the label `box` of `seeded_fault_sealed`, encrypted so that only the grader can read it. Nothing on
your machine can open it, not even the injector's own binary. The grader opens it for I-22 and I-28 (checks 4.06 and
5.06), and a sealed fault that does not belong to the run in your snapshot fails 3.02 in Tier B. A course recording's
box also carries the recording's id, so the same opening checks I-32.

---

## 3. The pager

Alertmanager's receivers `pager` and `chat` are webhooks to `http://pager:8080/hook/pager` and
`http://pager:8080/hook/chat`. The pager keeps the last 1,000 notifications and shows them at http://localhost:18091
(the on-call's phone, refreshing every 5 s); `GET /notifications` lists them. It exports, for the snapshot,
`itsm_pager_notifications_total{receiver, status}` and `itsm_pager_alerts_total{receiver, status}` (`receiver` is the
hook, `pager` or `chat`; `status` is `firing` or `resolved`) and `itsm_pager_last_notification_timestamp_seconds{receiver}`.

---

## 4. The rules

### 4.1 Alerting and routing

| id | rule |
|---|---|
| **I-01** | `prometheus/demo-alerts.yml` passes `promtool check rules` and has **at least two** alerting rules on the shop's telemetry, each with the labels `service` and `severity` (`P1`, `P2` or `P3`), at least one of them `P1`. A rule is on the shop's telemetry when it selects a metric that is not `svcdesk`'s (`http_server_request_duration_seconds...`), not the injector's (`seeded_*`) and not the pager's (`itsm_pager_*`). Other alerting rules - a heartbeat such as `Watchdog`, a rule on `svcdesk`'s metrics - may sit in the file and are not counted. |
| **I-02** | No rule in `prometheus/alerts.yml` or `prometheus/demo-alerts.yml`, alerting or recording, selects a `seeded_*` series - by name, or by a selector without a name (a regular expression on `__name__`, or labels alone such as `{job="seeded-flagd"}`) that does not exclude them. The injector's series may define the onset, never the detection. |
| **I-03** | `prometheus/alerts.yml` (Lab 3's) still passes `promtool check rules`, and every alerting rule in it carries `severity` `P1`, `P2` or `P3`: `svcdesk` joins the routing tree. |
| **I-04** | `alertmanager/alertmanager.yml` passes `amtool check-config` (Alertmanager 0.34.1) and defines the receivers `pager`, with a webhook to exactly `http://pager:8080/hook/pager`, and `chat`, with a webhook to exactly `http://pager:8080/hook/chat`. |
| **I-05** | **Published routes.** `amtool config routes test` resolves each label set of the table below to receivers that include `pager` for `severity="P1"`, and that include `chat` and not `pager` for `P2` and `P3`. The same holds for every alerting rule of I-01 and I-03, tested with its static `labels` plus `alertname` set to its name and routed by its own `severity`. |
| **I-06** | **Your routes.** `alertmanager/routing-tests.yml` lists **at least three** `routes` cases, each a label set and the exact receiver list `amtool config routes test` prints for it; they all hold. |
| **I-07** | **Inhibition, proved on a running Alertmanager.** `inhibit_rules` has at least one rule, and every `inhibitions` case of `routing-tests.yml` holds: the checker starts Alertmanager 0.34.1 with your file, posts the case's `source` and `target` together, and reads `GET /api/v2/alerts`. The target is `suppressed` with a non-empty `inhibitedBy` exactly when the case says `inhibited: true`. (`amtool check-config` and `amtool config routes test` never evaluate an inhibition - Lecture 4, slide 11.) |
| **I-08** | Among the cases there is a **pair** with the same source - one `inhibited: true`, one `inhibited: false` - whose targets differ **only** in the value of a label the matching rule lists in `equal`: the equal-labels pitfall, proved in both directions. |

The published label sets of I-05:

| labels | receivers must |
|---|---|
| `alertname="ItsmRouteCheck", service="checkout", severity="P1"` | include `pager` |
| `alertname="ItsmRouteCheck", service="checkout", severity="P2"` | include `chat`, not `pager` |
| `alertname="ItsmRouteCheck", service="frontend", severity="P3"` | include `chat`, not `pager` |

`alertmanager/routing-tests.yml` (this is the published example, with invented alerts; use your own):

```yaml
routes:
  - labels: {alertname: CheckoutErrorRate, service: checkout, severity: P1}
    receivers: [pager]
inhibitions:
  - source: {alertname: PaymentDown, service: payment, severity: P1, cluster: shop}
    target: {alertname: CheckoutErrorRate, service: checkout, severity: P2, cluster: shop}
    inhibited: true
  - source: {alertname: PaymentDown, service: payment, severity: P1, cluster: shop}
    target: {alertname: CheckoutErrorRate, service: checkout, severity: P2, cluster: other}
    inhibited: false
```

How the checker runs these:

- **Routes** (I-05, I-06): `amtool config routes test --config.file=<your file> <label>=<value> ...` with exactly the
  case's labels. Its last line is the receiver list, comma-separated, in the order of the tree: `pager`, or `chat`, or
  `pager,chat` when a matching route has `continue: true` - so a case's `receivers` is `[pager]`, `[chat]` or
  `[pager, chat]`. Labels your expression adds at run time (a `sum by (service_name)`) are not part of I-05's test:
  route on the static labels your rules declare.
- **Inhibitions** (I-07): one fresh Alertmanager per case, so nothing leaks from one case to the next. Both alerts
  are posted as firing, in one request; the checker then polls `/api/v2/alerts` for up to 5 seconds. A target that
  is inhibited carries the source's fingerprint in `inhibitedBy`; a silence does not count.
- **The pair** (I-08): the two cases have the same `source`; their targets have the same label names and differ in
  the value of exactly one label; and that label is in the `equal` list of an inhibit rule whose source matchers
  match the source and whose target matchers match the inhibited target. The checker reads `source_matchers` and
  `target_matchers` (write one matcher per list item: `'severity="P2"'`) and the older `source_match`,
  `source_match_re`, `target_match` and `target_match_re`.

Why the pair. Alertmanager's own reference: "if all the label names listed in equal are missing from both the source
and target alerts, the inhibition rule will apply". Misspell the label in `equal`, and it is missing from both alerts
everywhere: the source then mutes every matching target in every cluster. The `inhibited: true` case passes either
way; only the `inhibited: false` case catches the mistake.

### 4.2 The run

| id | rule |
|---|---|
| **I-09** | **One run.** The snapshot holds exactly one armed run: one `run` among the `seeded_fault_sealed` series, and one `seeded_fault_active` series. (Restarting the injector starts a new run; start the stack again with `down -v`.) An injector started and stopped before arming leaves only its `seeded_injector_info` series and does not count; the baseline of I-10 is measured from the armed run's own start. |
| **I-10** | **Baseline gate.** The injector's first sample (`seeded_injector_info`) is at least **10 minutes** before the onset, and **no alert with `severity="P1"` is firing** at any evaluation in the 10 minutes before the onset: your pages must be quiet on the healthy shop. |
| **I-32** | **Your login's recording.** On the recorded path the snapshot is one of the course's three recordings, `lab4-rec-1`, `lab4-rec-3` or `lab4-rec-4`, and it must be the one your GitHub login assigns: the (1 + (SHA-256 of the login, trimmed and lower-cased, as an integer) mod 3)-th of that list, which `itsmlab recording 4` prints. The recording's id is sealed in the box with the fault, so only the grader checks it, against the login of your receipt: another recording fails 3.02. A live run carries no recording and is not affected. (Added 12 October 2026, after I-31; ids are never renumbered.) |

The injector refuses to arm before its 10 minutes, so the first half of I-10 holds by itself. The second half is
yours, and the injector does not check it - it arms whatever your alerts do: an `ALERTS{alertstate="firing",
severity="P1"}` sample anywhere in `[onset - 10 min, onset)` fails it, whichever file the rule is in. Only the alert
names `Watchdog` and `InfoInhibitor` are exempt. Since the onset comes 2 to 6 minutes after you arm, **arm only when
no P1 is firing or has fired in the last 10 minutes**: right before `POST /arm`,
`max_over_time(ALERTS{alertstate="firing", severity="P1"}[10m])` must return nothing in Prometheus (HANDOUT step 5).
That covers the part of the window before you arm; keep the pages quiet until the onset for the rest. If it returns a
series, do not arm: wait until it returns nothing, and fix a rule that keeps firing on the healthy shop. A P1 that
fires on the healthy shop is yours to fix before the fault, not after: once armed, the only way back is `down -v` and
a new baseline.

Such a P1 also spoils the instants. A firing run that started before the onset is never the detection (I-12), so a
P1 still firing at the onset has paged before the fault: a ticket opened for that page fails I-15, and the detection
is another alert's. If the same alert resolves and fires again after the onset, that run is the detection, and
nothing in the snapshot tells whether the fault or the noise started it. `itsmlab incident 4` prints a `warning:` line
for every P1 firing run in `[onset - 10 min, onset)`, with its alert name, its first and last sample and what it did
to the instants; the warning changes no value it prints.

### 4.3 Four timestamps, three durations

| id | rule |
|---|---|
| **I-11** | **onset** = the timestamp of the first sample of `seeded_fault_active` (the series starts at the onset). |
| **I-12** | **detection** = the earliest start of a firing run of any `ALERTS{alertstate="firing"}` series that starts at or after the onset; a firing run is a sequence of samples of one label set no more than 1.5 evaluation intervals apart. That series is the **detecting alert**; when several runs start at that instant, it is the most severe (`P1`, then `P2`, `P3`, then any other), then the first by `alertname`, then by label set. (Prometheus sends Alertmanager `startsAt` = the moment the alert began firing, so this is the `startsAt` Alertmanager shows, also for an alert your inhibition lists as `suppressed`.) |
| **I-13** | **recovery** = the end of the detecting alert's firing run: its last sample plus its rule group's evaluation interval (10 s unless the group sets `interval`) - the `endsAt` Prometheus sends when the alert resolves. A detecting alert still firing at the end of the snapshot has no recovery: take the snapshot after it resolves. |
| **I-14** | **acknowledgement** = `acknowledged_at` of the P1 ticket in `incident/ticket.json`. **MTTD = detection - onset, MTTA = acknowledgement - detection, MTTR = recovery - onset**, in whole seconds: the differences of the instants as `itsmlab incident 4` prints them. Each is a single difference: one incident has no mean. The postmortem declares the four instants and the three durations, each within **30 s** of the recomputed value, and `detecting_alert`, the recomputed detecting alert's name. `itsmlab incident 4` prints the recomputation - it is the grader's script. |

These are the four timestamps and three clocks of Lecture 4, slide 14, and every one of them is read from the two
artifacts you ship:

| instant | where the grader reads it | in your running playground it is |
|---|---|---|
| onset | the snapshot: the first sample of `seeded_fault_active` | at most 5 s after the flags switched (the injector is scraped every 5 s) |
| detection | the snapshot: the start of the detecting alert's firing run in `ALERTS` | the `startsAt` of that alert in Alertmanager |
| acknowledgement | `incident/ticket.json`: `acknowledged_at` | the server's own time of your `POST /tickets/{id}/ack` |
| recovery | the snapshot: the end of that firing run | the `endsAt` of that alert when it resolves |

What follows from I-12 and I-13, in detail:

- **Any alert can detect**, whatever its severity and whichever file it is in: a P2 that starts firing before your P1
  is the detecting alert. Only `Watchdog` and `InfoInhibitor` are ignored. An alert whose firing run
  started before the onset is not a detection, even while it keeps firing. On equal starts the most severe alert
  wins - a page and a warning that fire together make the page the detecting alert - then the name first in
  alphabetical order, then the label set.
- **Equal starts happen within one rule group, rarely across groups.** Prometheus evaluates each group on its own
  schedule, at its own offset inside the 10 s interval, and the rules of one group share that evaluation's timestamp.
  Two alerts in different groups that see the same symptom therefore start a few seconds apart, and the one whose
  group ran first is the detecting alert - a P3 cause alert can beat your P1 page by one second. Put the alerts you
  want to compete on severity into one group, or expect a cause alert to win the race; either is correct, as long as
  the postmortem names the alert `itsmlab incident 4` prints.
- **An inhibited alert still detects.** Detection is read from `ALERTS` in Prometheus, before Alertmanager routes or
  inhibits anything. An alert your inhibit rule mutes sends no notification, but it still has a firing run, and
  Alertmanager lists it `suppressed` with the same `startsAt`.
- **A firing run** breaks when two consecutive samples of the series are more than 1.5 intervals apart (15 s at the
  course's 10 s): one missed evaluation does not split a run, an alert that resolves and fires again does.
- **The recovery is the end of the detecting alert's first firing run.** If that alert resolves and fires again
  during the incident, its second run is not your recovery. A `for:` clause delays the start of a run (it adds to
  MTTD); `keep_firing_for:` delays its end (it adds to MTTR) and keeps a flapping alert's run in one piece.
- **The recovery is the detecting alert's, not the fault's.** An alert on a symptom all three flags cause resolves a
  few minutes after the last flag goes off, when its window has slid past the fault. An alert on one flag's symptom
  (a cause alert on one service, say) can resolve while the other flags still fail, and then the recovery - and
  MTTR - comes before the fault ended. That is still the rule; the Timeline says when the last flag went off.
- **"Still firing at the end"** means the run's last sample is within 1.5 intervals of the snapshot's newest sample.
  Wait until the detecting alert has resolved - its `resolved` notification reaches the pager if you set
  `send_resolved` - and a minute more, then take the snapshot.
- **The interval** of a rule group is read from your rule files by the alert's name; without `interval:` it is the
  course's 10 s.

`itsmlab incident 4` extracts your snapshot, serves it on the checker's Prometheus, and prints exactly the values the
checks use:

```json
{
  "run": "9f3c2a1b7d4e6f80",
  "onset": "2026-10-24T10:41:05Z",
  "detection": "2026-10-24T10:44:30Z",
  "detecting_alert": "CheckoutErrorRate",
  "acknowledgement": "2026-10-24T10:46:12Z",
  "recovery": "2026-10-24T11:02:40Z",
  "mttd_seconds": 205,
  "mtta_seconds": 102,
  "mttr_seconds": 1295
}
```

Below it, a line for everything it could not compute (for example `recovery: the detecting alert ... is still firing
at the end of the snapshot`); it exits 0 only when there is none. Copy the values into your postmortem.

### 4.4 The ticket

| id | rule |
|---|---|
| **I-15** | `incident/ticket.json` is `svcdesk`'s `GET /tickets/{id}` answer for the incident's ticket: priority `P1`, `created_at` at or after the onset, `acknowledged_at` present and not before the detection. |
| **I-16** | **The acknowledgement is in the telemetry.** `svcdesk`'s request histogram (Lab 3) in the snapshot shows a successful `POST` on the route `/tickets/{...}/ack` between 15 s before and 20 s after `acknowledged_at`, and a successful `POST /tickets` in the same window around `created_at`. The playground runs `svcdesk` with the test clock off, so the server stamps the time. |
| **I-17** | **The page arrived.** `itsm_pager_notifications_total{receiver="pager",status="firing"}` rose after the onset. |

- **P1** is your service's own priority matrix: impact 1 and urgency 1 give P1 under every Lab 1 decision. The ticket
  must be created in the playground's `svcdesk` (port 18080), which Prometheus scrapes; a ticket in any other copy of
  your service leaves no trace in the snapshot.
- **Acknowledge after the page.** An acknowledgement before the detecting alert fired fails I-15 (the checker allows
  1 s). If a dashboard shows you the fault first, open the ticket then, and acknowledge it when the page arrives.
- **I-16 reads** `http_server_request_duration_seconds_count` of the scrape job `svcdesk`, method `POST`, a status
  that begins with `2`, and the route `/tickets` or a route `/tickets/<placeholder>/ack`, in any placeholder syntax
  (`{id}`, `{ticket_id}`, `<id>`, `:id`). "Shows a request" means the counter of that label set rises between two
  consecutive scrapes, and those two scrapes are not both before the window or both after it - or the series first
  appears inside the window with a count: a client library creates a label set on its first request, so your P1's
  own request may be the one that creates it.
- **I-17** holds when the counter rises between two scrapes and the later one is after the onset, or when the series
  first appears after the onset with a count.

### 4.5 The postmortem (`postmortem.md`)

Front matter, first in the file:

```yaml
lab4_postmortem:
  ticket: "3f1c9a52-7d1e-4b8a-9c0e-5a2f6b7d8e90"   # the id in incident/ticket.json
  detecting_alert: CheckoutErrorRate
  onset: 2026-10-24T10:41:05Z
  detection: 2026-10-24T10:44:30Z
  acknowledgement: 2026-10-24T10:46:12Z
  recovery: 2026-10-24T11:02:40Z
  mttd_seconds: 205
  mtta_seconds: 102
  mttr_seconds: 1295
  identified_flags: [paymentFailure, adManualGc]
```

Every field is required (check 4.01): `ticket` a string equal to the `id` in `incident/ticket.json` (quote it: an id
of digits alone would otherwise be read as a number); `detecting_alert` the alert name `itsmlab incident 4` prints;
the four instants with an offset; the three durations as numbers of seconds; `identified_flags` a non-empty list of
flag keys **from the pool** - a key the injector does not control fails 4.01.

| id | rule |
|---|---|
| **I-18** | The **thirteen** fields of the SRE book's example postmortem (Appendix D; Lecture 4 slide 17), as `##` headings in this order: Date, Authors, Status, Summary, Impact, Root Causes, Trigger, Resolution, Detection, Action Items, Lessons Learned, Timeline, Supporting information; each with at least 20 characters of text; Lessons Learned with the three `###` headings What went well, What went wrong, Where we got lucky. |
| **I-19** | **Incident and problem, separated** (ITIL 4; Lecture 4 slide 16): the incident record is the P1 ticket; the postmortem ends with `## Problem record` carrying the labels `Incident record:` (containing the ticket id), `Root cause:`, `Known error:` and `Workaround:`, the last three with at least 20 characters each. |
| **I-20** | Action Items is a table with the columns Action Item, Type, Owner, Bug (as the example), at least two rows, every Type one of mitigate, prevent, process, other. |
| **I-21** | Timeline contains the four instants of the front matter (as `HH:MM:SS` or in full). |
| **I-22** | **Fault identification** (Tier B): `identified_flags` contains **at least 2 of the 3** seeded flags and **at most 1** flag that was not seeded - a published threshold, never set equality, because the demo makes its own noise, and no looser, so that guessing the likeliest flags does not pass. The grade says whether the threshold was met, not how many flags matched. Tier A reports it `skip`. |

How the checker reads them:

- **Headings** (I-18) are matched in lower case with runs of spaces folded, so `## Root causes` counts and
  `## Timeline (UTC)` does not; the singular forms `Root Cause`, `Action Item` and `Lesson Learned` count too. "Text"
  is everything between the heading and the next `##`, less deeper headings - so `## Date` followed by `2026-10-24`
  alone (10 characters) fails. Write a sentence under every field. Lessons Learned is checked for its three `###`
  headings, not for its own length.
- **The problem record** (I-19): each label at the start of a line, optionally after `-` or `*` or in `**bold**`,
  followed by a colon and its text on the same line. `Incident record:` must contain the ticket's id; the other three
  need at least 20 characters. It is the problem as ITIL 4 defines it, "a cause, or potential cause, of one or more
  incidents": the root cause, the known error ("a problem that has been analyzed but has not been resolved") and the
  workaround (it "reduces or eliminates the impact of an incident or problem for which a full resolution is not yet
  available"). The incident record is the ticket; it closes when service is restored, the problem record stays open
  until the cause is gone.
- **Action Items** (I-20): the first table row is the header; it must contain the four columns in this order (others
  may sit between them); the separator row is skipped; each further row's Type is compared in lower case, so
  `Prevent` counts and `` `prevent` `` does not. I-20 does not check the Bug column, but give every row a Bug id - a
  ticket id such as `ITSM-42`, not `none` or `-`: Lab 6 (R-33) and Lab 8 (A-23) refer to one of these action items by
  its Bug id, and a row without one can only be named there by quoting its Action Item text exactly.
- **The timeline** (I-21) must contain each instant of your front matter either in full as the checker writes it
  (`2026-10-24T10:41:05Z`) or as its **UTC** clock time (`10:41:05`). A timeline in Warsaw time (`12:41:05`) fails.
- **Identification** (I-22) compares flag keys, not variants, as a set: at least two of your flags are among the three
  seeded, and at most one of them is not. Listing all nine fails, and so does naming one flag; three flags with one
  wrong pass, and so do the three right ones plus one flag of the demo's own noise.

### 4.6 The AI ledger (`ai-rca-eval.json`)

```json
{"investigator": {"agent": "gemini-cli 0.61.0", "model": "gemini-3.8-flash", "mcp_server": "prom_mcp.py (mcp 2.2.0)",
                  "transcript": "ai-rca/transcript.md"},
 "hypotheses": [
  {"id": "H1", "hypothesis": "<the agent's words, verbatim from the transcript>", "component": "payment",
   "predicts": "sum(rate(traces_span_metrics_calls_total{service_name=\"payment\",status_code=\"STATUS_CODE_ERROR\"}[5m])) > 0.05",
   "at": "2026-10-24T10:52:00Z", "result": true, "verdict": "correct",
   "evidence": "0.21/s at 10:52; nothing at 10:36"},
  {"id": "H2", "hypothesis": "...", "component": null, "predicts": null, "at": null, "result": null,
   "verdict": "unfalsifiable", "why_no_query": "..."}]}
```

| id | rule |
|---|---|
| **I-23** | The file parses with the fields above; the transcript file exists and is at least 200 bytes; at least **three** hypotheses with unique ids; `verdict` is one of `correct`, `partially_correct`, `hallucinated`, `unfalsifiable`. |
| **I-24** | Every `hypothesis` is found **verbatim** in the transcript (after folding runs of whitespace): the ledger scores what the agent said, not a paraphrase. |
| **I-25** | A `correct`, `partially_correct` or `hallucinated` entry has `predicts`: a PromQL expression whose top level is a comparison (`>`, `<`, `>=`, `<=`, `==`, `!=`, without `bool`) or an `and`/`or`/`unless` of comparisons - so that it returns something exactly when the prediction holds - naming every metric it selects (no `__name__` regular expression, no selector of labels alone), selecting no `seeded_*` series and only metrics the snapshot holds (a query on a metric that does not exist is false everywhere and tests nothing), and `at` inside the incident (between the onset and the end of the snapshot). An `unfalsifiable` entry has `predicts`, `at` and `result` null and a `why_no_query` of at least 40 characters. There is no fifth state: a hypothesis nobody tested is not in the ledger (Lecture 4 slide 26). |
| **I-26** | **Re-executed on the snapshot at `at`**: a non-empty result means `result: true`. `correct` and `partially_correct` need true; `hallucinated` needs false - the data must genuinely contradict it. |
| **I-27** | **It tests the fault.** A `correct` or `partially_correct` prediction must be **false** on the healthy baseline, 5 minutes before the onset: a prediction already true before the fault tests nothing about it. |
| **I-28** | **Against ground truth** (Tier B): the `component` of a `correct` or `partially_correct` entry is a service a seeded flag affects (section 2.2's table). Tier A checks that it is one of the table's services (5.01) and reports I-28 itself `skip`. |

The four verdicts (Lecture 4, slide 25):

| verdict | means | your evidence | what the checks require |
|---|---|---|---|
| `correct` | the prediction held against the data | the query, and its result | `result: true`, true at `at`, false 5 minutes before the onset; `component` affected by the fault (Tier B) |
| `partially_correct` | the right component, the wrong mechanism or time | the query that splits the two | the same as `correct` |
| `hallucinated` | the data says otherwise | the query that contradicts it | `result: false`, false at `at` |
| `unfalsifiable` | no query could prove it wrong: "an intermittent issue somewhere in the system" | none: that is the verdict | `predicts`, `at`, `result` null; `why_no_query` of at least 40 characters |

The verdicts are graded for their consistency with the data, never for their direction: a ledger of three
`hallucinated` entries passes exactly as a ledger of three `correct` ones does. Untested is not untestable: "likely
a memory pressure issue in the cart service" names a service and a resource, so it has a query and is not
`unfalsifiable`; until you have run that query it has no verdict, and no place in the ledger.

The fields, as the checker reads them:

| field | rule |
|---|---|
| `investigator.agent`, `investigator.model` | non-empty: the agent and the model that produced the transcript |
| `investigator.mcp_server` | the MCP server and its version (read, not checked) |
| `investigator.transcript` | the transcript's path, relative to the repository root and inside it; at least 200 bytes |
| `id` | unique within the file |
| `hypothesis` | the agent's words, found in the transcript after both are folded (every run of spaces, tabs and line breaks becomes one space). Nothing else may differ: not the case, not the punctuation, not the Markdown (`**payment**` stays `**payment**`). Quote the whole claim, not a word of it |
| `component` | for `correct` and `partially_correct`: one service name exactly as in section 2.2 (`product-catalog`, not `productcatalogservice`); otherwise any string or null |
| `predicts` | the prediction as a PromQL comparison, run as an instant query on the snapshot. It is yours: translate the agent's claim into the query that would prove it wrong, whatever query the agent itself ran |
| `at` | the instant the prediction is evaluated at, with an offset, from the onset to the end of the snapshot |
| `result` | `true` when the query returns anything at `at`, `false` when it returns nothing |
| `verdict` | one of the four |
| `evidence` | what the query returned and why that decides the verdict (read, not checked) |
| `why_no_query` | `unfalsifiable` only: at least 40 characters |

Writing a prediction:

- **A comparison filters**: `sum(rate(...[5m])) > 0.05` returns the series when the value is above 0.05 and nothing
  otherwise, which is what makes "non-empty" mean "true". `> bool 0.05` always returns a value (0 or 1), so it is
  refused; so is a query with no comparison at the top, such as `rate(...)` alone or `absent(...)`.
- **Aggregate** to one series (`sum`, `max`) unless you mean "any of these". Use windows of at least 5 minutes, and
  choose `at` well inside the fault, where the whole window is: a `[5m]` rate evaluated 2 minutes after the onset is
  still mostly baseline.
- **The baseline** instant is exactly the onset minus 300 s, the same `predicts` evaluated there. A prediction that
  also holds on the healthy shop - "checkout has some errors", when checkout always has a few - fails I-27: raise the
  threshold until it tells the fault from the baseline, or it was not a claim about the fault.
- **Splitting the two** (`partially_correct`): `A unless on() B` returns A's result only when B returns nothing. With
  A the part that held and B the mechanism the agent got wrong, it is true exactly when the agent was half right.
- **A contradiction must be real** (`hallucinated`): a query on a metric or label value that does not exist returns
  nothing whatever happened. Build it from series the snapshot really holds (`list_metrics` and `label_values` of the
  MCP server, or Prometheus's own autocomplete), so that "nothing" is the data's answer and not a typo's.
- **A `sum` over series that do not exist is empty, not 0.** A service that has not failed has no
  `status_code="STATUS_CODE_ERROR"` series at all, so `sum(rate(...STATUS_CODE_ERROR...[5m])) == 0` returns nothing
  on the healthy shop as well. To claim "this service had traffic and no errors", write the traffic and subtract the
  errors: `sum(rate(<its calls>[5m])) > 0 unless on() sum(rate(<its error calls>[5m])) > 0`.
- A query that Prometheus refuses fails I-26 with Prometheus's own message.

### 4.7 Stretch

| id | rule |
|---|---|
| **I-29** | **Second investigator.** `ai-rca-eval-2.json` from a different agent or model (HolmesGPT with Gemini or Ollama, Claude Code, or the other free option), scored by I-23 to I-28, and `ai-rca/COMPARISON.md` of at least 600 characters. |
| **I-30** | **The regulators' clocks.** The front matter of `comms-log.md` declares the awareness (NIS2), detection (KSC) and classification (DORA) instants you defend, the submission instants of the reports you would send, and the deadlines: NIS2 early warning +24 h and notification +72 h from awareness, final report one calendar month after the notification; KSC the same from detection; DORA initial report 4 h after classification and no later than 24 h after awareness when classified within those 24 h (else 4 h after classification), intermediate 72 h after the initial notification, final one month after the intermediate report (the weekend relief of the DORA technical standard, Art. 5(4), is ignored). The checker recomputes every deadline (+-1 minute). |
| **I-31** | **Kubernetes track.** `k8s/k8sgpt-analyze.json` (`k8sgpt analyze -o json`, k8sgpt v0.4.39, against the demo's Helm chart `opentelemetry-demo` 0.42.3 on kind, with your incident's three flags set in the chart's flagd) and `k8s/COMPARISON.md` (at least 600 characters) comparing its analyzers with the agentic loop. Structure only: the JSON is an object with a `results` list. |

For I-29, "different" means that the pair (`investigator.agent`, `investigator.model`) differs from the first
ledger's: the course's agent loop with `qwen3:1.7b` and the same loop with a Gemini model are two investigators. The
second ledger passes the same checks as the first, against the same snapshot.

**I-30, the arithmetic.** The law behind each clock: NIS2 Art. 23(4) ("becoming aware" of a significant incident);
KSC art. 11 ust. 1 pkt 4 to 4c ("od momentu jego wykrycia", from the moment of its detection); DORA with its technical
standard, Delegated Regulation (EU) 2025/301, Art. 5 ("has become aware"; the classification as major). Lecture 4,
slide 21, draws them side by side.

| key in `lab4_comms` | the rule |
|---|---|
| `awareness`, `detection`, `classification` | yours to defend (instants) |
| `nis2.notification_sent`, `ksc.notification_sent`, `dora.initial_sent`, `dora.intermediate_sent` | yours: when each report would go out (instants) |
| `nis2.early_warning_due` | awareness + 24 h |
| `nis2.notification_due` | awareness + 72 h |
| `nis2.final_report_due` | one calendar month after `nis2.notification_sent` |
| `ksc.early_warning_due` | detection + 24 h |
| `ksc.notification_due` | detection + 72 h |
| `ksc.final_report_due` | one calendar month after `ksc.notification_sent` |
| `dora.initial_due` | classification + 4 h; when the classification is within 24 h of awareness, the earlier of that and awareness + 24 h |
| `dora.intermediate_due` | `dora.initial_sent` + 72 h |
| `dora.final_due` | one calendar month after `dora.intermediate_sent` |
| `log` | at least three communications, each `{at, to, what}` |

Hours are elapsed hours. "One calendar month after" is the same day and time of the next month **on the UTC
calendar**, or that month's last day when it is shorter: a month after `2026-10-31T09:00:00Z` is
`2026-11-30T09:00:00Z`. Every declared deadline must be within one minute of the rule's.

A worked example. Your detecting alert fired at 10:44:30Z; at 10:50:00Z, with the ticket acknowledged and the impact
on checkout clear, you judge the incident significant; at 11:30:00Z you classify it as major for DORA. You would send
the DORA initial notification at 14:00:00Z, the NIS2 and KSC notifications on Monday at 09:00:00Z, and the DORA
intermediate report on Tuesday at 10:00:00Z.

```yaml
lab4_comms:
  awareness: 2026-10-24T10:50:00Z
  detection: 2026-10-24T10:44:30Z
  classification: 2026-10-24T11:30:00Z
  nis2:
    early_warning_due: 2026-10-25T10:50:00Z      # awareness + 24 h
    notification_due: 2026-10-27T10:50:00Z       # awareness + 72 h
    notification_sent: 2026-10-26T09:00:00Z
    final_report_due: 2026-11-26T09:00:00Z       # a month after notification_sent
  ksc:
    early_warning_due: 2026-10-25T10:44:30Z      # detection + 24 h
    notification_due: 2026-10-27T10:44:30Z       # detection + 72 h
    notification_sent: 2026-10-26T09:00:00Z
    final_report_due: 2026-11-26T09:00:00Z
  dora:
    initial_due: 2026-10-24T15:30:00Z            # classification + 4 h; earlier than awareness + 24 h
    initial_sent: 2026-10-24T14:00:00Z
    intermediate_due: 2026-10-27T14:00:00Z       # initial_sent + 72 h
    intermediate_sent: 2026-10-27T10:00:00Z
    final_due: 2026-11-27T10:00:00Z              # a month after intermediate_sent
  log:
    - {at: 2026-10-24T14:00:00Z, to: the financial supervisor, what: DORA initial notification}
    - {at: 2026-10-26T09:00:00Z, to: the CSIRT, what: NIS2 and KSC incident notification}
    - {at: 2026-10-27T10:00:00Z, to: the financial supervisor, what: DORA intermediate report}
```

DORA's initial deadline in the three cases, with the same awareness (10:50:00Z on Saturday):

| classified as major at | `dora.initial_due` | why |
|---|---|---|
| 2026-10-24T11:30:00Z | 2026-10-24T15:30:00Z | within 24 h of awareness: the earlier of 15:30 and 10:50 on Sunday |
| 2026-10-25T08:00:00Z | 2026-10-25T10:50:00Z | within 24 h, but 4 h later would pass the 24 h: awareness + 24 h binds |
| 2026-10-25T12:00:00Z | 2026-10-25T16:00:00Z | classified after the 24 h: 4 h after the classification (Art. 5(2)) |

The trap of the date. Warsaw leaves summer time in the night after the lab (Sunday 25 October 2026, 03:00 CEST becomes
02:00 CET). Awareness at 12:50 Warsaw time on Saturday is 10:50Z; the early warning is due 24 hours later, at 10:50Z
on Sunday - 11:50 on a Warsaw clock, not 12:50. Write every instant in UTC and the arithmetic cannot slip.

**I-31, what to analyse.** The handout's Stretch 3 has the commands, the versions and the chart values that keep
the chart healthy on kind. The fault injector exists only in the compose playground: you set your incident's flags
in the chart's `flagd-config` ConfigMap by hand. No AI backend is needed (`analyze` without `--explain`). k8sgpt's analyzers read the
state of Kubernetes objects - crashed or OOM-killed pods, failing probes, Services without endpoints, unused
ConfigMaps - and a feature-flag fault leaves every pod running and ready: expect it to report little or nothing of
your fault, and let the comparison say which symptoms each tool could observe at all.

---

## 5. What you add

| path | what |
|---|---|
| `prometheus/demo-alerts.yml` | I-01, I-02 |
| `alertmanager/alertmanager.yml`, `alertmanager/routing-tests.yml` | I-04 to I-08 |
| `incident/tsdb-snapshot.tar.gz`, `incident/ticket.json` | I-09 to I-17, and I-32 on the recorded path; `itsmlab snapshot 4 --ticket <id>` writes both from the running playground, `itsmlab recording 4` names your recording |
| `postmortem.md` | I-18 to I-22, and the narrative the lecturer reads |
| `ai-rca-eval.json`, `ai-rca/transcript.md` | I-23 to I-28 |
| `ai-rca-eval-2.json`, `ai-rca/COMPARISON.md`, `comms-log.md`, `k8s/` | Stretch (I-29 to I-31) |
| `itsmlab.yaml` | `lab: 4`, `baselines: {lab3: student}` or `{lab3: checkpoint}` |

`prometheus/alerts.yml` (Lab 3) stays, and is checked again by I-03 and I-05.

**The snapshot** is what `itsmlab snapshot 4 --ticket <id>` writes: it asks Prometheus's admin API for a snapshot,
copies it out of the `prometheus` container with `docker cp`, packs its blocks into `incident/tsdb-snapshot.tar.gz`,
and saves `svcdesk`'s `GET /tickets/<id>` as `incident/ticket.json`. The archive is at most **50 MB** (GitHub refuses
files over 100 MB; a 60-minute run of the playground is well under) and unpacks to at most 500 MB, with no absolute
paths, no `..`, no links, and at least one Prometheus block (a directory with a `meta.json`). The checker's
Prometheus serves the blocks with a retention of 100 years, so nothing in them is ever deleted.

---

## 6. Numbers at a glance

| what | value | rule |
|---|---|---|
| baseline before the injector arms | 10 min | I-10 |
| onset after arming | 2 to 6 min, at random | section 2.1 |
| the fault ends by itself | 45 min after the onset | section 2.1 |
| no P1 firing | in the 10 min before the onset | I-10 |
| rule evaluation, firing-run gap | 10 s (or the group's `interval`); at most 1.5 intervals | I-12, I-13 |
| declared instants and durations | within 30 s of the recomputation | I-14 |
| the acknowledging and the creating request | 15 s before to 20 s after the ticket's instant | I-16 |
| the baseline of a prediction | the onset minus 5 min | I-27 |
| route cases; inhibition cases | at least 3; at least 1 pair | I-06, I-08 |
| postmortem fields; `Root cause:`, `Known error:`, `Workaround:` | at least 20 characters each | I-18, I-19 |
| action items | at least 2 rows | I-20 |
| hypotheses; transcript; `why_no_query` | at least 3; at least 200 bytes; at least 40 characters | I-23, I-25 |
| fault identification | at least 2 of the 3 seeded flags, at most 1 other | I-22 |
| comparisons (Stretch) | at least 600 characters | I-29, I-31 |
| regulators' deadlines | within 1 min; at least 3 log entries | I-30 |
| snapshot | at most 50 MB packed, 500 MB unpacked | section 5 (3.01) |

---

## 7. What the grader does with all this

Nothing of the playground runs on the grader: the incident happened on your machine, once, and what the grader does
is recompute everything from the two artifacts you ship. It runs the same checker on your receipted tag - your
`svcdesk` built and started in its sandbox for L4-CORE-1, your rule files through `promtool`, your routing tree
through `amtool` and a fresh Alertmanager per case, your snapshot on its own Prometheus, every prediction of your
ledger at its `at` and on the baseline. Then it opens the sealed fault: I-22 (your `identified_flags`) and I-28 (the
components of your correct and partially correct entries) against the three flags that really failed, and 3.02
against the run the fault belongs to and, for a recording, against the recording your login assigns (I-32).

Its messages name the check that failed and the threshold, never a seeded flag: a later attempt is graded against the
same run, and the answer is not in the grade.

The rules are published. The fault is not. Working an incident whose cause you do not know is the lab.
