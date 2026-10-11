<!-- ai-generated: 0% - written by the course team -->
# MONITORING-SPEC.md - the monitoring rules of Lab 3

**This document is the whole rulebook.** Every rule that decides what "correct" means is here: the endpoint and
its dependency, the histogram, the checker's measurement, the bucket rule, the SLO document, the alert rules
together with the checker's own probes and mutants, the dashboard, the first draft, and the Stretch options.
Nothing the checker does is withheld. What is not published is your `kb-index` profile: it is derived from your
GitHub login, it differs from every classmate's, and the only way to know it is to measure it.

Where this document and an assistant disagree, this document wins. And nothing you write down is believed: every
number that decides a grade is measured again by the checker's own instruments - its load generator (oha 1.16.0),
its own Prometheus 3.15.0 scraping your service and evaluating your rules, and `promtool` 3.15.0. Your own
Prometheus and Grafana are never started by the checker.

Rule ids (`M-01` .. `M-31`) are stable. The checker's messages and [CHECKS.md](CHECKS.md) cite them.

**Words used below.** *The ladder* is the list of finite `le` boundaries of your request histogram, as your
service exposes them on `/metrics`. *q* is the p99 the checker measures (M-08); *q_kb* is the p99 of `kb-index`
measured directly (M-09). Durations are Prometheus durations (`5m`, `1h`, `28d`). *Burn rate* is the SRE
Workbook's: the rate at which the error budget is consumed, relative to the rate that exactly exhausts it at the
end of the SLO window. At burn rate b on an SLI with objective O, a share b x (1 - O) of the requests is bad.

---

## 1. The endpoint and the dependency

| id | rule |
|---|---|
| **M-01** | The compose file defines a service `kb-index` with `image: ghcr.io/swasik/seeded-toxic:2026` and `SEEDED_TOXIC_LOGIN` set to your GitHub login. The checker and the grader replace the image and the login with their own (section 1.1). |
| **M-02** | `GET /kb/search?q=<text>`, with `q` of 1 to 200 characters; any other `q` (missing, empty, longer) is answered 400 or 422 with a top-level `error` object. For each valid request `svcdesk` makes **exactly one** `GET {KB_INDEX_URL}/search?q=<q>` (`q` URL-encoded) - no cache, no retry - with a timeout of **at least 2 s**; `KB_INDEX_URL` defaults to `http://kb-index:8080`. Upstream 200: answer 200 `{"query": q, "hits": <the upstream's hits, unchanged>}`. Upstream non-200, timeout or connection error: answer **502** with an `error` object whose `code` is `upstream_unavailable`. |

The dependency's whole interface is in [HANDOUT.md](HANDOUT.md), section "The dependency: `kb-index`". Two facts
matter for M-02: `kb-index` answers a failure with 503 `{"error": {"code": "index_unavailable", ...}}`, and a `q`
that begins with `force-error` always gets that 503, after its latency. The checker's own requests
(L3-CORE-2.01 to 2.03) are `GET /kb/search?q=vpn%20drops`, whose `hits` must equal what `kb-index` itself answers
for the same `q`; no `q` at all, and a `q` of 201 characters; and `q=force-error-itsmlab`, which must come back
502 `upstream_unavailable`. Because `kb-index` also fails a small share of ordinary requests, the checker repeats the
`vpn drops` request, at most three times, while your service answers it 502; one 200 is enough.

### 1.1 What the checker and the grader do to your compose file

They apply this override after your own compose files:

```yaml
services:
  kb-index:
    image: ghcr.io/swasik/seeded-toxic:2026        # the grader: the same image, pinned by digest
    build: !reset null                              # you cannot build your own kb-index
    environment:
      SEEDED_TOXIC_LOGIN: <login>
      SEEDED_TOXIC_ADMIN: "0"                       # no admin endpoints in a checked run
```

`<login>` is, in Tier A, the value of `--login` if you pass one, else `login:` from `itsmlab.yaml`, else the owner
part of `repository:` (lower-cased); in Tier B, the login of your receipt (the account that opened the submission
issue). Every run prints the login it used. After an untimed build, `docker compose up --wait svcdesk kb-index`
starts those two services and nothing else, and must succeed within 120 s. Host-path bind mounts are refused on
those two services only (L3-CORE-1.02); your own `prometheus` and `grafana` are never started.

---

## 2. The histogram

| id | rule |
|---|---|
| **M-03** | `GET /metrics` answers the Prometheus text exposition format (version 0.0.4) to `Accept: text/plain`. The checker sends `Accept: text/plain;version=0.0.4`. |
| **M-04** | One histogram, `http_server_request_duration_seconds`, **in seconds**, observes every request the service answers exactly once (`/metrics` itself may be left out). Its labels are exactly `http_request_method`, `http_route` and `http_response_status_code` (plus `le` on the buckets): the OpenTelemetry HTTP semantic conventions in their Prometheus form. |
| **M-05** | `http_route` is the **template** of the matched route (`/tickets/{id}`, in whatever placeholder syntax your framework uses); every request that matches no route gets one constant value (for example `unmatched`); a raw path, an id or a query string never appears in any label of any metric. `http_response_status_code` is the numeric status as a string (`"200"`). |
| **M-06** | Every label set has the same ladder, with **at most 30** finite boundaries. |
| **M-07** | **Cardinality budget.** After its contract requests, the checker sends one warm-up request of each probe kind, scrapes `/metrics`, sends 1,000 probe requests - 250 `GET /itsmlab-probe/<uuid>` (no route), 250 `GET /tickets/<uuid>` (a route; 404), 500 `GET /health?itsmlab-probe=<uuid>` - and scrapes again. The second scrape may contain **at most 5** series the first did not. A series is a metric name with one exact label set, counted over everything `/metrics` exposes, not only the histogram. |

Answer `/metrics` with a `Content-Type` of `text/plain` (the client libraries send
`text/plain; version=0.0.4; charset=utf-8`). The checker reads the body itself in L3-CORE-2 and 3, but its own
Prometheus 3.15.0 refuses to scrape an answer labelled with any other type (`application/json`,
`application/octet-stream`): it then holds no data from your service, and 4.04, 6.03 and 6.04 report `error`
("could not scrape svcdesk's /metrics", with the reason), which fails Core.

What the checker verifies with these (L3-CORE-2.04 to 2.09): `/metrics` has the line
`# TYPE http_server_request_duration_seconds histogram` and `_bucket`, `_sum` and `_count` samples; every sample of
the three carries exactly the three labels (plus `le`); each of its `/kb/search` requests (the 200, the two
refusals, the 502) is counted on `http_route="/kb/search"` under the status it got; its `GET /tickets/<id>` 404 is
counted on a route that begins `/tickets/`; no label value anywhere contains its random ids; the ladder is the same
in every label set; and one `/kb/search` request adds more than 0 and less than 10 to that route's `_sum` - a
histogram in milliseconds adds tens or hundreds.

---

## 3. The measurement

| id | rule |
|---|---|
| **M-08** | After a 5 s warm-up at the same rate, the checker runs `oha --no-tui --output-format json -z 60s -q 40 -c 64 --latency-correction '<svcdesk>/kb/search?q=itsmlab'`. The run is **open-loop**: requests are scheduled at 40 per second whatever the service does, and each latency is measured from the instant the request was scheduled (Lecture 3: coordinated omission). **q** is oha's `latencyPercentiles.p99` over all responses. `itsmlab load 3` runs exactly this and prints the same numbers. |
| **M-09** | Then `oha --no-tui --output-format json -z 30s -q 40 -c 64 --latency-correction '<kb-index>/search?q=itsmlab'`, straight at `kb-index`: **q_kb**, the dependency's own p99. |
| **M-10** | **No bypass.** q >= 0.9 x q_kb, and `kb-index`'s `/stats` request counter rose, during the M-08 run, by the number of responses oha received, within 2 %. |

The checker scrapes `/metrics` and reads `kb-index`'s `/stats` right before and right after the 60-second run; the
increments between the two readings are "the run" in M-10 and M-12. The run must also complete (3.01): at least
95 % of the 2,400 scheduled requests answered, and transport errors - requests that got no HTTP answer at all -
below 1 % of them. The few requests oha reports as `aborted due to deadline` at the end of a run are not counted
as errors.

---

## 4. Buckets

| id | rule |
|---|---|
| **M-11** | **Resolution.** Let (lo, hi] be the bucket of the ladder that contains q: lo is the largest boundary below q (0 if none), hi the smallest boundary at or above q. The ladder **resolves** q when hi is finite and **hi - lo <= 0.20 x q**. |
| **M-12** | **Agreement.** Over the M-08 run, with the increments of the `/kb/search` series summed over methods and status codes: `_count` equals the number of responses within 2 %, and the p99 that `histogram_quantile` computes from the bucket increments (Prometheus's linear interpolation inside a bucket) is within **25 %** of q. This is what catches a histogram in milliseconds, or a timer that does not cover the whole request. |
| **M-13** | The latency SLI's threshold (M-14) is **one of the ladder's finite boundaries**, so that the SLI counts requests instead of interpolating them. |

A q exactly on a boundary belongs to the bucket that ends there: with boundaries 0.2 and 0.25, q = 0.25 is in
(0.2, 0.25]. The *relative width* of the bucket is (hi - lo) / q.

**Worked example**, on the published practice profile (q about 0.218 s):

| ladder | bucket holding q | relative width | resolves |
|---|---|---|---|
| Go's `DefBuckets` or Python's `prometheus_client` default | (0.1, 0.25] | 0.15 / 0.218 = 68.8 % | no |
| the flawed ladder (M-27) | (0.04, 0.5] | 0.46 / 0.218 = 211 % | no |
| `[..., 0.2, 0.21, 0.22, 0.23, 0.25, ...]` | (0.21, 0.22] | 0.01 / 0.218 = 4.6 % | yes |

The last one still resolves a q of 0.205 (4.9 %) or 0.235 (8.5 %). Neither default ladder can resolve any q at
all: relative to a value it contains, a bucket (lo, hi] is narrowest at q = hi, where it is (hi - lo) / hi, and
that is at least 25 % in Python's default ladder and at least 50 % in Go's.

---

## 5. The SLO document (`slo.md`)

YAML front matter first, then prose that the lecturer reads. The shape of the front matter, here with made-up
numbers for a 30-day window - an illustration of the arithmetic, not a recommendation:

```yaml
---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.95
      threshold_seconds: 0.25
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.25"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.05, minutes: 2160}
  alerts:
    - {alert: KbSearchErrorsBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchErrorsBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
```

(30 days are 43,200 minutes: 0.01 x 43,200 = 432 and 0.05 x 43,200 = 2,160.)

| id | rule |
|---|---|
| **M-14** | `service` is `svcdesk` and `route` is `/kb/search`. `window` is a duration from 7d to 90d. Both SLIs are present. Each `objective` is in [0.9, 1) with at most five decimals. `error_budget.fraction` = 1 - objective (±1e-9); `error_budget.minutes` = (1 - objective) x the window in minutes (±1). `threshold_seconds` is a positive number that satisfies M-13. |
| **M-15** | Evaluated by the checker's Prometheus after the M-08 run, `good` and `valid` each return **exactly one** sample (aggregate them, for example with `sum`), `valid` > 0, and 0 <= good / valid <= 1. |
| **M-16** | `alerts` declares at least **two** alerts on the **same** SLI with **different** `burn_rate`s (multi-burn-rate), no name twice. Each has `burn_rate` of at least 1, `long_window` from 30m to 3d, `short_window` above 0 and at most `long_window` / 4 (multiwindow), and burn_rate x (1 - objective) <= 0.5 (so that twice its burn rate can still happen). |

The checker's Prometheus scrapes your service as job `svcdesk`, every 5 s, from just before the warm-up of M-08;
its `instance` is whatever address the checker reached you at, so never select on `instance`. The SRE Workbook's
ticket alert (burn rate 1, long window 3d, short window 6h) can be a declared alert: at a burn rate of exactly 1 the
budget runs out exactly at the end of the window, and M-16 allows it.

**The `le` label is text.** Prometheus 3 stores every `le` value in one normalised float form - the shortest
float, with `.0` appended when it has neither a point nor an exponent: an exposed `0.300` is stored as `0.3`, `1` as
`1.0` and `0.00001` as `1e-05`. Your SLI and dashboard queries run on the checker's Prometheus and see that form, and
the probes of M-19 write their series in the same form, whatever your service exposes. So select `le="0.3"` or
`le="1.0"`: `le="0.300"` and `le="1"` match nothing, on real data and in the probes alike.

---

## 6. Alert rules (`prometheus/alerts.yml`)

| id | rule |
|---|---|
| **M-17** | A Prometheus rule file that passes `promtool check rules`. Each alert `slo.md` declares is exactly one alerting rule of that name. Every alerting rule in the file carries the labels `service: svcdesk`, `slo: availability` or `slo: latency`, and `severity: P1`, `P2` or `P3`; a declared alert's `slo` label is the `sli` that `slo.md` declares for it; at least one declared alert is `P1`. Lab 4 routes on `severity`: P1 to the pager, P2 and P3 to chat, the labels Lecture 4 uses. |
| **M-18** | In each declared alert's `expr` there is at least one comparison, and **every comparison compares against a constant**: a number, or arithmetic of numbers such as `14.4 * (1 - 0.99)`. The threshold must be visible in the alert, not hidden in a recording rule, because M-21 mutates it. |
| **M-19** | **Behaviour probes.** For each declared alert the checker writes its own `promtool` test from the inputs of section 6.1 and requires: **fire** - under a sustained burn at 2 x burn_rate the alert is firing by t0 + L/2 + F + slack, and not before t0 + L/2 + F - slack; **quiet** - under a sustained burn at 0.5 x burn_rate it never fires; **reset** - after a burn at 2 x burn_rate stops at t1, it is no longer firing at t1 + S + slack_r. The last one is the multiwindow property: a long window alone keeps firing for about L/2 after the burn stops. |

L is the declared `long_window`, S the declared `short_window`, B the declared `burn_rate` (all from `slo.md`), and F
the rule's `for` (from `alerts.yml`; 0 when it has none).

### 6.1 The probe inputs

Counters at a 1-minute sample interval (5 minutes when `long_window` is longer than 6h), evaluated with an
`evaluation_interval` equal to the sample interval, with exactly these labels:

```
kb    = {job="svcdesk", instance="svcdesk:8080", http_request_method="GET", http_route="/kb/search"}
noise = {job="svcdesk", instance="svcdesk:8080", http_request_method="GET", http_route="/tickets/{id}", http_response_status_code="200"}
```

`/kb/search` receives 10 requests per second and `/tickets/{id}` another 10: the noise that catches a rule without a
route filter. At burn b on an SLI with objective O, the bad requests per second on `/kb/search` are
b x (1 - O) x 10, and the rest are good:

- **availability probes**: bad requests carry `http_response_status_code="502"`, good ones `"200"`; all of them are
  observed below the smallest boundary, so they are counted in every `le`;
- **latency probes**: every request carries `"200"`; good ones are observed below the smallest boundary, bad ones
  above the largest finite boundary, so they are counted only in `le="+Inf"`.

The series, for every label set: `http_server_request_duration_seconds_count`, `_bucket` for every finite boundary
of your ladder (the boundaries the checker read during its run, written in the normalised form above) and for
`"+Inf"`, and `_sum`. Every counter is 0 at time 0; the requests of one sample interval appear in the next sample.
The noise route counts every request in every `le`.

Timings, with slack = max(3 samples, L/10) and slack_r = max(3 samples, S/5); every instant is rounded to a whole
number of sample intervals:

| probe | burn on `/kb/search` | asserted |
|---|---|---|
| fire | 0 until t0 = L + 10m, then 2B for L + F + 30m | not firing at t0 + L/2 + F - slack (asserted only when that instant is more than one sample after t0); firing at t0 + L/2 + F + slack |
| quiet | 0.5B throughout, for 3L | not firing at L, 2L and 3L |
| reset | 2B from 10m to t1 = 10m + L + F + 10m, then 0 | firing at t1 minus one sample; not firing at t1 + S + slack_r |

"Firing" means `ALERTS{alertname="<alert>", alertstate="firing"}` in promtool's test storage: the checker's test
asserts that `vector(1) and on() count(ALERTS{alertname="<alert>",alertstate="firing"})` is 1 when the alert must be
firing and returns nothing when it must not. The test loads your whole `alerts.yml`, recording rules included, from
a copy of your `prometheus/` directory.

**Worked timings.** They depend on L, S and F only, not on the burn rate. For an alert with `for: 5m`:

| declared windows | sample | fire: not firing at / firing at | quiet: not firing at | reset: firing at / not firing at |
|---|---|---|---|---|
| L = 1h, S = 5m | 1m | 1h39m / 1h51m | 1h, 2h, 3h | 1h24m / 1h33m |
| L = 6h, S = 30m | 1m | 8h39m / 9h51m | 6h, 12h, 18h | 6h24m / 7h1m |

Consequences worth knowing before you write a rule:

- The probes use what `slo.md` declares. A rule whose threshold is above the declared burn rate fails **fire**, one
  whose threshold is below it fails **quiet**, and one whose short window is longer than the declared
  `short_window` can fail **reset**.
- Select `job="svcdesk"` or no job at all, never an `instance`; filter on `http_route="/kb/search"`; for
  availability, count the 5xx statuses as bad.
- Every range in the rule must hold at least two probe samples: longer than one sample interval, so at least 2m
  when `long_window` is at most 6h and at least 10m when it is longer.
- `keep_firing_for` keeps an alert firing after its expression turns false; the reset probe does not wait for it.

---

## 7. Tests and mutation (`prometheus/alerts_test.yml`)

| id | rule |
|---|---|
| **M-20** | `prometheus/alerts_test.yml` is a `promtool` unit-test file with `rule_files: [alerts.yml]`, and `promtool test rules alerts_test.yml` passes. |
| **M-21** | **Mutants.** For each declared alert the checker makes up to four mutants of `alerts.yml`, each changing only that rule: **for + 5m** (`for` plus 5 minutes; a rule without `for` gets `for: 5m`), **for - 5m** (`for` minus 5 minutes, floored at 0, where the `for` is removed; made only when `for` is at least 1m), **threshold x 1.5** and **threshold / 1.5** (the constant side of every comparison in the rule's `expr` multiplied, respectively divided, by 1.5). Your tests must **fail** on every mutant. A suite that passes a mutant is not testing that property of the rule. |

How it runs: the checker copies your `prometheus/` directory (its `.yml` and `.yaml` files), replaces `alerts.yml`
in the copy with the mutant, and runs `promtool test rules alerts_test.yml` there; the mutant is killed when promtool
exits with an error. Mutants are run only once your tests pass on the unmutated file (5.03). A threshold mutant is
rewritten from the parsed expression, so `a > 14.4 * (1 - 0.99)` becomes `a > (14.4 * (1 - 0.99)) * 1.5`. A mutant
that cannot be made (no `for` of at least 1m) is reported as not applicable and does not count against you.

What kills which mutant, for a test that burns above the threshold: `for + 5m` and `threshold x 1.5` make the alert
fire later or not at all, so an assertion that it **is** firing at the first evaluation where the real rule fires
kills them; `for - 5m` and `threshold / 1.5` make it fire earlier, so an assertion that it is **not yet** firing one
evaluation before that kills them, and so does a long burn just below the threshold that must never fire. Find the
first firing evaluation with promtool itself: `rate()` extrapolates at the edges of its range, and the minute you
compute by hand can be off by one.

---

## 8. The dashboard (`grafana/dashboards/`)

| id | rule |
|---|---|
| **M-22** | At least one dashboard file: any `.json` file under `grafana/dashboards/` (subdirectories included) that is a Grafana dashboard JSON - the dashboard object with a `panels` list, or an export `{"dashboard": {...}}`; any other `.json` there is skipped. Library panels are not allowed: their queries are not in the file. The queries are the `expr` of each panel's `targets`, panels inside rows included. |
| **M-23** | Before a query runs, Grafana's variables are replaced as the table below says. `$v`, `${v}`, `${v:format}` (the format is ignored) and `[[v]]` are all recognised. |
| **M-24** | At least three panels have queries, and at least one query is a `histogram_quantile` over `http_server_request_duration_seconds_bucket`. Every query parses, runs on the checker's Prometheus without error, and **every metric it selects by name exists there** - scraped from `svcdesk`, or produced by your recording rules. A panel that would show "No data" because a model invented a metric name fails here. |

| variable | replaced by |
|---|---|
| `$__rate_interval` | `1m` |
| `$__interval` | `15s` |
| `$__range` | `1h` |
| `$__range_s` | `3600` |
| `$__interval_ms` | `15000` |
| `$__range_ms` | `3600000` |
| `$__rate_interval_ms` | `60000` |
| a dashboard variable (`templating.list`) | its `current` value when it has exactly one; otherwise (several, All, empty) `.*` |
| any other variable | `.*` |

What exists on the checker's Prometheus when the queries run: the series it scraped from your `svcdesk` (job
`svcdesk`, every 5 s, from just before the M-08 warm-up), the series Prometheus adds for every target it
scrapes (`up`, `scrape_duration_seconds`, ...), and the results of your recording rules - the checker loads your
`alerts.yml`, when it passes `promtool check rules`, with every group's `interval` set to 5s. A recording rule whose
result is empty on that data produces no series, so a panel that selects it fails 6.04; so does a panel on
`ALERTS`, which exists only while an alert is pending or firing. Queries run as instant queries; an empty result is
not an error.

---

## 9. The first draft and the flawed ladder (`ai-first-draft.md`)

YAML front matter first. The example is the practice profile's, from a student whose assistant answered with Go's
default ladder:

```yaml
---
lab3_first_draft:
  source: ai                       # ai | instructor  (instructor = the no-AI path: the flawed ladder is your draft)
  tool: "Gemini in Google AI Studio (free tier), 10 October 2026"    # required when source is ai
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
  verdict: refuted                 # confirmed | refuted
  evidence: {p99_seconds: 0.218, bucket: [0.1, 0.25], relative_width: 0.688}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.218, bucket: [0.04, 0.5], relative_width: 2.110}
---
```

| id | rule |
|---|---|
| **M-25** | `ladder` is 1 to 40 strictly increasing positive numbers, in seconds. `evidence.bucket` is the ladder's bucket containing `evidence.p99_seconds` as M-11 defines it, written `[lo, hi]` (lo is 0 below the first boundary; hi is `"+Inf"` above the last), and `relative_width` = (hi - lo) / p99_seconds within 0.005. `p99_seconds` is **your** measurement, in seconds, and must be within 30 % of q. With `source: ai`, `tool` names the assistant, and the body has a `## Prompt` and a `## Answer` section, each at least 40 characters: the exchange, verbatim. With `source: instructor`, `ladder` is the flawed ladder of M-27, exactly. |
| **M-26** | **The verdict is checked against the checker's own q.** Apply M-11 to the declared ladder at 0.95q, q and 1.05q: if the three results agree and (hi - lo) / q at q is outside [0.16, 0.24], `confirmed` must mean "resolves" and `refuted` "does not". Otherwise the case is too close to call and either verdict is accepted. Both verdicts score the same; a verdict the measurement contradicts does not. |
| **M-27** | The flawed ladder is `buckets-flawed.example.yml` as shipped: `[0.001, 0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.02, 0.025, 0.03, 0.04, 0.5, 2.5]` - fine where the median lives, blind where the p99 does. Its verdict is `refuted`, with evidence consistent as in M-25, from the same measured p99 as your draft's (to 1 %). It fails M-11 for every profile of this lab. |

Arithmetic of the example: (0.25 - 0.1) / 0.218 = 0.688 and (0.5 - 0.04) / 0.218 = 2.110. With a checker's q near
0.218 s, the draft ladder puts 0.95q, q and 1.05q in the same bucket, (0.1, 0.25], whose relative width is far
outside [0.16, 0.24], so `refuted` is the only verdict the measurement allows.

The body, after the front matter and your AI-disclosure line: `## Prompt` (what you asked, verbatim), `## Answer`
(what the assistant answered, verbatim), then the verdicts in prose with their arithmetic. The checker reads a
section from its `## ` heading to the next line that begins with `## `. If the assistant's answer contains such
lines itself, quote the whole answer (a `> ` before every line): it stays verbatim and stays inside its section.

---

## 10. Stretch

| id | rule |
|---|---|
| **M-28** | **GenAI diff.** `genai/spans.json` holds the spans of one instrumented LLM call - an OTLP JSON export (`{"resourceSpans": [...]}`, one per file or one per line) or a JSON array of OpenTelemetry Python SDK span objects - with at least one `gen_ai.*` attribute. `genai/DIFF.md` starts with front matter `lab3_genai_diff`: `instrumentation` (the library and its version), `spec_ref` (one of the refs below) and `attributes`, one entry per attribute: `name`, `emitted` (true/false), `in_spec` (true/false) and, when in the spec, `stability` as the spec states it. |
| **M-29** | The declared `emitted: true` names equal the set of `gen_ai.*` attribute keys in `genai/spans.json`; every `in_spec` and `stability` claim agrees with the checker's snapshot of that spec ref's attribute registry; at least five attributes are declared, none twice. Direction is never graded: a library that matches the spec exactly passes. |
| **M-30** | **Client-server gap.** `gap.json` declares a Toxiproxy latency toxic - `{"type": "latency", "latency": <ms>, "jitter": <ms>}` with `latency` from 20 to 500 and `jitter` from 0 to `latency` - and the numbers measured through it: `client_p99_seconds`, `server_p99_seconds`, `gap_seconds`. The checker puts Toxiproxy with that toxic (downstream, toxicity 1) in front of `svcdesk`, runs the M-08 load through it for 30 s, and computes the client p99 (oha) and the server p99 (`histogram_quantile(0.99)` over the run's increments of your `/kb/search` histogram). The declared gap must be within max(15 ms, 30 %) of the re-measured one; `gap/README.md` explains it in at least 400 characters. |
| **M-31** | **Kubernetes track.** `k8s/values.yaml` for kube-prometheus-stack 89.2.2 sets `prometheus.prometheusSpec.retention: 2h` and a Prometheus memory limit (`prometheus.prometheusSpec.resources.limits.memory`) of at most 1Gi; `k8s/prometheusrule.yaml` is a `PrometheusRule` whose `spec.groups` equal the groups of `prometheus/alerts.yml` (the same group names; in each, the same rules in the same order, with the same `record` or `alert`, the same `expr` after parsing, the same `for` and the same labels); `k8s/servicemonitor.yaml` is a `ServiceMonitor` whose `spec.selector` names `svcdesk`; `k8s/evidence.json` is the output of `kubectl get prometheusrules,servicemonitors,pods -A -o json` from the running cluster and contains both objects and a Running pod whose name contains `prometheus`. The least machine-checkable option: what is checked is consistency, not that the cluster existed. |

The spec refs the checker knows (M-28, M-29):

| `spec_ref` | what it is |
|---|---|
| `semantic-conventions-genai@e57c543b4889619eb2a05702471937db5119165d` | the GenAI conventions' own repository, `open-telemetry/semantic-conventions-genai`, at that commit; the repository has no release |
| `semantic-conventions@v1.41.1` | the last release of the main `open-telemetry/semantic-conventions` repository that still held the GenAI conventions |

`stability` is the attribute's stability in that ref, lower-case as the spec's model files write it (for example
`development`), or `deprecated` for an attribute the ref marks as deprecated. An attribute the ref does not define
has `in_spec: false` and no `stability`.

---

## 11. Tolerances at a glance

| what | tolerance | rule, check |
|---|---|---|
| responses to the M-08 run | at least 95 % of the 2,400 scheduled; transport errors below 1 % | M-08, 3.01 |
| q against q_kb | q >= 0.9 x q_kb | M-10, 3.02 |
| `kb-index` `/stats` rise against responses | ±2 % | M-10, 3.03 |
| `/kb/search` `_count` rise against responses | ±2 % | M-12, 3.04 |
| width of the bucket that holds q | at most 0.20 x q | M-11, 3.05 |
| your histogram's p99 against q | ±25 % of q | M-12, 3.06 |
| `_sum` rise of one `/kb/search` request | above 0, below 10 | M-04, 2.08 |
| new series in the cardinality probe | at most 5 | M-07, 2.09 |
| `error_budget.fraction` | ±1e-9 | M-14, 4.02 |
| `error_budget.minutes` | ±1 | M-14, 4.02 |
| `evidence.relative_width` | ±0.005 | M-25, 3.07 |
| your draft's `p99_seconds` against q | ±30 % of q | M-25, 3.07 |
| a verdict too close to call | M-11 differs among 0.95q, q and 1.05q, or (hi - lo) / q at q is in [0.16, 0.24] | M-26, 3.08 |
| probe instants | slack = max(3 samples, L/10); slack_r = max(3 samples, S/5) | M-19, 5.05 to 5.07 |
| declared gap against the re-measured one | max(15 ms, 30 % of the re-measured gap) | M-30, L3-STRETCH-2.01 |

---

## 12. What the grader does with all this

Tier B runs the same checker, from the same image pinned by digest, on its own machine, against the files of your
receipted tag, with the `kb-index` profile of your receipt's login. Its run is your grade's measurement. Its q
differs from yours by a few per cent - another machine, another 2,400 random draws from the same profile - and
everything else is exactly as published here. Nothing is withheld, except that its run is the one that counts.

The rules are published, and so is every instrument. Your distribution is not: it is yours, and measuring it is
the work.
