<!-- ai-generated: 0% - written by the course team -->
# Lab 3 - Instrument svcdesk: histograms you designed, an SLO you can burn

Saturday 10 October 2026, 150 minutes, fully online. AI Assessment Scale level 3 (AI Collaboration). Peak container
RAM about 1.2 GB (Grafana alone idles near 0.55 GB).

Disclosure: reasoning artifacts are pre-screened by an AI model; all grades are assigned by the lecturer.

## Goal

`svcdesk` gains a knowledge-base search, `GET /kb/search`, which calls an upstream index, `kb-index`, on every
request. `kb-index` is a course image whose latency and error profile is derived from your GitHub login: your
service has a latency distribution that no classmate's has, and its p99 sits in a narrow slow mode that a default
bucket ladder swallows. The seeded latency lives in the dependency behind `svcdesk`, not in a proxy in front of it,
so your service's own histogram observes it.

Instrument the service with a RED histogram whose buckets you design from your own measurement; write an SLO with
two SLIs and their error budgets; write multiwindow, multi-burn-rate alerts with `promtool` tests strong enough to
kill published mutants; and build a Grafana dashboard whose every query runs against real data. The AI step is
the one the lecture announced: before you design anything, ask an assistant for bucket boundaries and an alert
rule, commit its answer verbatim, and give its ladder a verdict with the arithmetic; then show that the
instructor's flawed ladder is wrong for your own distribution.

Nothing you write down is believed. The checker - and the grader, which runs the same checker - measures your p99
itself, runs every panel query, sends 1,000 junk requests and counts your new series (at most 5), mutates your
alert rules and expects your tests to fail, checks your verdict against its own measurement, and drives each alert
with a synthetic burn of its own to see that it fires in time, stays quiet at half the rate, and stops when the
burn stops.

Read, in this order: [MONITORING-SPEC.md](MONITORING-SPEC.md) (the whole rulebook, M-01 to M-31),
[CHECKS.md](CHECKS.md) (every check the checker runs), and the templates listed in [README.md](README.md).
`./itsmlab.sh checks 3` (Windows: `.\itsmlab.ps1 checks 3`) prints the same catalogue from the checker itself; it
runs nothing, so it is safe at any point in the lab. The course [README](../README.md) explains the checker, the
receipts and the deadlines.

## If you have not finished Lab 2

Lab 3 needs only the `svcdesk` you built in Lab 1, running. It adds one endpoint, one dependency and the
instrumentation, and nothing in it calls Lab 2's `/dora/...` endpoints. From Lab 1 it uses `GET /health` and the
route `GET /tickets/{id}`: the checker counts a 404 on that route to see that your route labels are templates
(L3-CORE-2.07).

Lab 2's correction window closes on Saturday 10 October 2026 at 08:00:00 Europe/Warsaw, on the morning of this session.
Whether a `checkpoint/lab-2` tag is published at that moment is announced on Moodle; this lab does not depend on
it. Nothing in Lab 3 reads `baselines:` in `itsmlab.yaml`.

## Before you start

1. Pull the current checker image and check its version:

       docker pull ghcr.io/swasik/itsmlab:2026
       ./itsmlab.sh --version                  # Linux, macOS
       .\itsmlab.ps1 --version                 # Windows PowerShell

   It must print `itsmlab 0.8.0` or newer (the image published on 7 October 2026, the first on the `:2026` tag that knows
   Lab 3). An image pulled before 7 October prints `itsmlab 0.3.2`: it does not know Lab 3, and does not carry the
   instruments Lab 3 needs (its own Prometheus, `promtool`, oha and Toxiproxy).

2. Pull the images of the lab. These tags replace the planned list in PREWORK.md:

       docker pull ghcr.io/swasik/seeded-toxic:2026
       docker pull prom/prometheus:v3.15.0
       docker pull grafana/grafana:13.2.3

3. In `itsmlab.yaml`, set `lab: 3`.

4. **Your login.** The checker derives your `kb-index` profile from your GitHub login: `login:` in `itsmlab.yaml`
   when it is there, else the owner part of `repository:`. `load 3` and `verify 3` print the login they used, and
   stop with a message when neither is set. The grader uses the login of your receipt, the GitHub account that
   opens the submission issue. If your repository's owner is not your own login (an organisation, a second
   account), add `login: <your login>` to `itsmlab.yaml`: with the wrong login you measure somebody else's profile,
   while the grader measures yours and judges your ladder, your verdict and your evidence against that.

5. Set `SEEDED_TOXIC_LOGIN` in your compose file to the same login. The checker overrides it, but your own
   `docker compose up`, and everything you measure against it, uses what you wrote.

## Minute budget

Core items sum to 110 minutes; the remaining 40 are slack. If an item overruns by more than its budget, stop, run
the checker, and ask on the forum with the check id.

| # | Core item | minutes | at |
|---|---|---|---|
| 1 | `kb-index` in your compose file, `GET /kb/search` (M-01, M-02) | 15 | 15 |
| 2 | The histogram with route templates, `/metrics`, the cardinality rule (M-03 to M-07) | 20 | 35 |
| 3 | Ask the assistant for a ladder and an alert rule, commit its answer; `./itsmlab.sh load 3`; both verdicts in `ai-first-draft.md` (M-25 to M-27) | 20 | 55 |
| 4 | Design your ladder, measure again (M-11 to M-13) | 10 | 65 |
| 5 | `slo.md` (M-14 to M-16) | 10 | 75 |
| 6 | `alerts.yml` and `alerts_test.yml`, until no mutant survives and the probes pass (M-17 to M-21) | 25 | 100 |
| 7 | The dashboard (M-22 to M-24), `./itsmlab.sh verify 3` (Windows: `.\itsmlab.ps1 verify 3`), tag, submit | 10 | 110 |
| | slack | 40 | 150 |

Item 3 comes before item 4 on purpose: the assistant's ladder is a first draft only while you have not designed
your own. In item 2, instrument with the library's default buckets or with the assistant's ladder; item 4
replaces them.

Item 6 is the one that overruns. While you write the tests, run `promtool` locally - a second per run:

    docker run --rm -v "$PWD/prometheus:/p" -w /p --entrypoint promtool prom/prometheus:v3.15.0 check rules alerts.yml
    docker run --rm -v "$PWD/prometheus:/p" -w /p --entrypoint promtool prom/prometheus:v3.15.0 test rules alerts_test.yml

(Windows PowerShell: `-v "${PWD}/prometheus:/p"`.) When they pass, run `./itsmlab.sh verify 3`: `L3-CORE-5.04`
lists every mutant that survived, and `5.05` to `5.07` print the instants they asserted and what they found.
`verify 3` takes two to three minutes after the build, because it repeats the measurement every time.

## The dependency: `kb-index`

`ghcr.io/swasik/seeded-toxic:2026` is a knowledge-base search service for known errors and workarounds. Its
interface is published, and this is all of it:

| request | answer |
|---|---|
| `GET /search?q=<text>` | after a latency drawn from your profile: 200 `{"query": q, "hits": [{"id", "title", "score"} x3]}`; with your profile's small error probability, 503 `{"error": {"code": "index_unavailable", ...}}` instead. A `q` that **begins with `force-error`** always gets the 503, after its latency: that is how you test your 502 path. |
| `GET /healthz` | 200 at once |
| `GET /stats` | 200 `{"service": "kb-index", "version": ..., "requests": n, "errors": m}`: the `/search` calls since the container started. The checker reads it around its measurement (M-10). |
| `POST /admin/degrade?minutes=M&error_rate=E&latency_factor=F` | for M minutes (1 to 120, default 10), errors at a rate of at least E (0 to 1, default 0.2) and every latency multiplied by F (1 to 20, default 1): for watching your alerts fire on your own Prometheus |
| `POST /admin/restore` | ends a degradation at once |

Environment: `SEEDED_TOXIC_LOGIN` (required: the container exits with code 2 without it; `practice` selects the
published practice profile below), `PORT` (default 8080), `SEEDED_TOXIC_ADMIN` (`0` removes the two admin
endpoints; the checker and the grader set it).

**What it does not tell you: its profile.** Nothing it answers or logs describes the distribution - its log names
only the login the profile was derived from - and the image has no shell to look inside. The only way to know your
p99 is to measure it, which is the lab. The same missing shell means that a compose `healthcheck` that runs a
command inside `kb-index` can never pass: give it none, and `docker compose up --wait` waits for it to be running.

**The practice profile** (`SEEDED_TOXIC_LOGIN: practice`) is published, for trying things out: computed from the
profile, its p50 is 26.7 ms, p95 46.9 ms, p99 218.0 ms and p99.9 243.3 ms, and 0.17 % of its searches fail. A
60-second measurement comes close to these numbers, not exactly onto them: one such run, open-loop at 40 requests
per second straight at `kb-index` (27 September 2026), gave a p50 of 27.4 ms, p95 46.8 ms, p99 214.4 ms and p99.9
240.5 ms.
`./itsmlab.sh load 3 --login practice` measures it with the checker. Your own profile is different, and the checker
and the grader never use `practice` for you.

Add `kb-index` to your compose file, and `KB_INDEX_URL: http://kb-index:8080` to the environment of `svcdesk`:
[compose-lab3.yml](compose-lab3.yml) has both.

## How to measure

The measurement that decides your grade is M-08, after a 5-second warm-up at the same rate:

    oha --no-tui --output-format json -z 60s -q 40 -c 64 --latency-correction '<svcdesk>/kb/search?q=itsmlab'

It is **open-loop**. `-q 40` schedules 40 requests per second whatever the service does; `--latency-correction`
measures each latency from the instant the request was scheduled, not from the moment a connection was free; and
64 connections keep the schedule from waiting behind slow answers. A closed-loop run - no `-q` - sends the next
request only when the last one returned, so a slow answer delays the requests behind it and their waiting is never
recorded: coordinated omission, Lecture 3 slide 19. q is oha's p99 over all the responses of the 60 seconds, about
2,400 of them.

Run it yourself with the checker:

    ./itsmlab.sh load 3                                    # Linux, macOS
    .\itsmlab.ps1 load 3                                   # Windows PowerShell
    ./itsmlab.sh load 3 --ladder 0.1,0.2,0.21,0.22,0.25    # also judge a ladder you are considering

(In PowerShell quote the ladder: `--ladder "0.1,0.2,0.21,0.22,0.25"`.) `load 3` builds and starts `svcdesk` and
`kb-index` exactly as `verify 3` does - your login's profile forced in, the admin endpoints off - runs the warm-up,
M-08, and M-09 (30 seconds straight at `kb-index`), and prints the login it used, oha's percentiles, q, q_kb, the
status codes, oha's own latency histogram, whether your service's ladder, the flawed ladder and your `--ladder`
resolve q (M-11), and your histogram's own p99 over the run (M-12). The measurement takes about 100 seconds after
the build and the start; the project is torn down afterwards (`--keep` leaves it running).

If you installed oha 1.16.0, the same measurement against your own `docker compose up` stack (with your own login
in `SEEDED_TOXIC_LOGIN`) is:

    oha --no-tui -z 5s -q 40 -c 64 --latency-correction 'http://localhost:8080/kb/search?q=itsmlab'     # warm-up
    oha --no-tui -z 60s -q 40 -c 64 --latency-correction 'http://localhost:8080/kb/search?q=itsmlab'

Your q is the line `99.00% in ...` of its "Response time distribution". One or two `aborted due to deadline` errors
at the end are normal: they are the requests the 60 seconds cut off, and the checker does not count them.

**Design for a band, not for a point.** Two runs of the same profile differ by a few per cent, and the grader's q
will differ from yours by a few per cent too: another machine, other random draws. A ladder whose one fine bucket
fits your laptop's q exactly fails when the grader's q lands in the coarse bucket next to it. Resolve a band of at
least ±10 % around your q, with every bucket in it at most 20 % as wide as the band's lower end. Spend your
boundaries there (you have at most 30, M-06), and make your latency SLI's threshold one of them (M-13).

## Why the default ladders fail

A histogram created without buckets gets the client library's:

| library | default boundaries (seconds) | finite boundaries |
|---|---|---|
| Go, `client_golang`: `prometheus.DefBuckets` | .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10 | 11 |
| Python, `prometheus_client`: `DEFAULT_BUCKETS` | .005, .01, .025, .05, .075, .1, .25, .5, .75, 1, 2.5, 5, 7.5, 10 | 14 |

Neither can pass M-11 at all, whatever your p99. M-11 wants the bucket that holds q to be at most 20 % of q wide,
and a bucket (lo, hi] is narrowest relative to a value inside it at q = hi, where it is (hi - lo) / hi. In Python's
ladder that is 25 % at best - (0.075, 0.1], (0.75, 1], (7.5, 10] - and in Go's 50 %. Between 100 and 500 ms both
ladders have just two buckets, (0.1, 0.25] and (0.25, 0.5], each at least 50 % of any p99 inside it.

On the practice profile (q about 0.218 s) both defaults put q in (0.1, 0.25]: 0.15 s wide, 69 % of q. The flawed
ladder puts it in (0.04, 0.5], 211 % of q. A ladder with `..., 0.2, 0.21, 0.22, 0.23, 0.25, ...` puts it in
(0.21, 0.22], 4.6 % of q, and still resolves it if the grader measures 0.205 or 0.235.

What a coarse bucket costs: `histogram_quantile` assumes the requests inside a bucket are spread evenly across it,
so the p99 your dashboard shows can land anywhere in that bucket, and nothing warns you (Lecture 3, slide 18). A
latency SLI whose threshold is not a boundary is the same kind of guess, which is why M-13 requires one. The lecture
predicted that an assistant asked for buckets hands you a ladder like these two. That is a prediction; your verdict
in `ai-first-draft.md` tests it on your own measurement.

## Core specs (all must pass; no partial credit inside the bundle)

| spec | what it checks |
|---|---|
| `L3-CORE-1` `compose-up` | `svcdesk` builds, `kb-index` runs the course image, both come up within 120 s; no host-path bind mount on either |
| `L3-CORE-2` `kb-search-metrics` | `GET /kb/search` with its refusals and its 502; the histogram's name, unit, labels and single ladder; route templates; the cardinality probe |
| `L3-CORE-3` `buckets` | the checker's own measurement: no bypass of `kb-index`, one upstream call per request, every response observed once, **your ladder resolves q**, your histogram's p99 agrees with q; `ai-first-draft.md` and both verdicts |
| `L3-CORE-4` `slo` | `slo.md`: its fields and arithmetic, a latency threshold on a boundary, both SLIs evaluated on real data, the declared multiwindow, multi-burn-rate alerts |
| `L3-CORE-5` `alerts` | `promtool check rules` and your `promtool` tests pass; the declared alerts exist, labelled, with constant thresholds; every mutant fails your tests; each alert fires in time, stays quiet at half its rate, and resets |
| `L3-CORE-6` `dashboard` | a dashboard file without library panels; at least three query panels, one `histogram_quantile`; every query runs and every metric it selects exists |

**Resolution is the heart of the lab** (3.05), as the consistency gate was in Lab 2: the checker measures q itself
and applies M-11 to the ladder your service exposes. Nothing you declare can stand in for it.

## Stretch (any two of three; each lifts the grade band equally)

| spec | what it is |
|---|---|
| `L3-STRETCH-1` `genai-diff` | Instrument one LLM call with the OpenTelemetry GenAI instrumentation and diff what the library emits against the GenAI semantic conventions (M-28, M-29). |
| `L3-STRETCH-2` `latency-gap` | Put Toxiproxy with a latency toxic in front of `svcdesk`, measure the client's p99 and the server's, and explain the gap (M-30). |
| `L3-STRETCH-3` `k8s` | The Kubernetes track: kube-prometheus-stack on kind, with your rules and a capped Prometheus (M-31). Optional, never required. |

**Stretch 1, `genai-diff`.** The instrumentation package is now `opentelemetry-instrumentation-genai-openai`
(1.2b0; import `OpenAIInstrumentor` from `opentelemetry.instrumentation.genai.openai`). The older
`opentelemetry-instrumentation-openai-v2` fails to import with current dependencies. Write the spans as OTLP JSON
with `opentelemetry-exporter-otlp-json-file` (its `FileSpanExporter` writes one batch per line, which the checker
accepts) to `genai/spans.json`; an OTLP receiver such as Grafana Alloy v1.20.0 is optional and not needed, because
the file exporter writes what the checker reads. A set of versions that works together (27 September 2026):
`openai==3.19.2`, `opentelemetry-sdk==1.45.0`, `opentelemetry-instrumentation-genai-openai==1.2b0`,
`opentelemetry-exporter-otlp-json-file==0.66b0`. Any OpenAI-compatible endpoint will do, a local Ollama model
(`http://localhost:11434/v1`) included. `genai/DIFF.md` ([template](genai/DIFF-template.md)) names the
instrumentation and its version, one of the two spec refs the checker knows, and at least five attributes:

| `spec_ref` | what it is |
|---|---|
| `semantic-conventions-genai@e57c543b4889619eb2a05702471937db5119165d` | the GenAI conventions' own repository at that commit; the repository has no release |
| `semantic-conventions@v1.41.1` | the last release of the main semantic-conventions repository that still held the GenAI conventions |

The `emitted: true` names must be exactly the `gen_ai.*` keys in your spans, and every `in_spec` and `stability`
claim must agree with the checker's snapshot of the ref you name. Direction is never graded: a library that matches
the spec exactly passes.

**Stretch 2, `latency-gap`.** Toxiproxy 2.12.0 is `ghcr.io/shopify/toxiproxy:2.12.0` (the tag has no `v`); the
commented `toxiproxy` service in [compose-lab3.yml](compose-lab3.yml) runs it next to `svcdesk`. Toxics are added
through its HTTP API on port 8474, not through its configuration file:

    curl -X POST localhost:8474/proxies -d '{"name": "svcdesk", "listen": "0.0.0.0:8666", "upstream": "svcdesk:8080", "enabled": true}'
    curl -X POST localhost:8474/proxies/svcdesk/toxics -d '{"type": "latency", "stream": "downstream", "toxicity": 1.0, "attributes": {"latency": 100, "jitter": 10}}'

(Windows: `curl.exe`, with each JSON body in a file: `-d "@proxy.json"`.) Then measure through the proxy's
published port:

    ./itsmlab.sh load 3 --base-url http://172.17.0.1:8666              # Linux
    ./itsmlab.sh load 3 --base-url http://host.docker.internal:8666    # macOS, Windows (Docker Desktop)

Its q is the client's p99 through the toxic, and "your histogram's own p99 over the run" is the server's.
`gap.json` ([template](gap-template.json)) records the toxic and the three numbers, and `gap/README.md` explains the
gap in at least 400 characters. The checker builds its own proxy with your toxic in front of `svcdesk`, runs the
M-08 load through it for 30 seconds, and computes both p99s itself; your `gap_seconds` must be within
max(15 ms, 30 %) of its gap.

**Stretch 3, `k8s`.** The agenda's Kubernetes track: kube-prometheus-stack 89.2.2 on kind v0.33.0. It is optional
and never required, it needs more memory than the rest of the lab together, and it is the least machine-checkable
option: what is checked is consistency, not that the cluster existed. The files: `k8s/values.yaml` with the caps
(retention 2h, a Prometheus memory limit of at most 1Gi; start from [k8s/values.yaml](k8s/values.yaml)),
`k8s/prometheusrule.yaml` (a `PrometheusRule` whose `spec.groups` are your `prometheus/alerts.yml` groups),
`k8s/servicemonitor.yaml` (a `ServiceMonitor` that selects `svcdesk`), and `k8s/evidence.json`, the output of
`kubectl get prometheusrules,servicemonitors,pods -A -o json` from the running cluster.

    kind create cluster
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm install kps prometheus-community/kube-prometheus-stack --version 89.2.2 -f k8s/values.yaml

## AI usage

Free choice of tool; this is AIAS level 3. Claude Pro is **not** required and is never on the Core path.

The lab's AI step: ask an assistant **first** - before you measure and before you design anything - for histogram
bucket boundaries and an alert rule for `GET /kb/search`. Commit its answer verbatim in `ai-first-draft.md`, under
`## Prompt` and `## Answer`. Then measure, and give its ladder a verdict with the arithmetic: `confirmed` if it
resolves your p99 (M-11), `refuted` if it does not. **Both verdicts score identically.** What is checked is that
your verdict agrees with the checker's own measurement (M-26): a verdict the measurement contradicts fails 3.08.
Say in prose what you kept of its alert rule and why; that part is read, not checked. Then do the same arithmetic
for the instructor's flawed ladder (`buckets-flawed.example.yml`), whose verdict is always `refuted`.

Free alternatives: Gemini with an API key from Google AI Studio, or Ollama running `qwen3:1.7b` on your own
machine. No AI at all: the instructor's flawed ladder is your first draft - `source: instructor` - and both
verdicts are about it. Every path reaches the same grade bands.

## Deliverables

At the repository root, on the tag you submit:

| path | what |
|---|---|
| `src/...` (wherever your code lives) | `GET /kb/search` (M-02); the histogram and `GET /metrics` (M-03 to M-07) |
| `docker-compose.yml` | the `kb-index` service (M-01) and `KB_INDEX_URL` on `svcdesk`; your own `prometheus` and `grafana` under the `observability` profile |
| `prometheus/prometheus.yml` | your own Prometheus's configuration (the checker does not read it) |
| `prometheus/alerts.yml`, `prometheus/alerts_test.yml` | your alerts and their `promtool` tests (M-17 to M-21) |
| `grafana/provisioning/...`, `grafana/dashboards/*.json` | your own Grafana; the checker reads only the dashboards (M-22 to M-24) |
| `slo.md` | front matter (M-13 to M-16) and the defence in prose |
| `ai-first-draft.md` | front matter (M-25 to M-27), the exchange verbatim, both verdicts with their arithmetic |
| `itsmlab.yaml` | `lab: 3`, and `login:` when your repository's owner is not your login |
| `genai/spans.json`, `genai/DIFF.md` | Stretch 1 only |
| `gap.json`, `gap/README.md` | Stretch 2 only |
| `k8s/values.yaml`, `k8s/prometheusrule.yaml`, `k8s/servicemonitor.yaml`, `k8s/evidence.json` | Stretch 3 only |

## When a check fails

| check | the usual cause |
|---|---|
| 1.02 | a bind mount (`./x:/y`) on `svcdesk` or `kb-index`; your `prometheus` and `grafana` may have them |
| 1.04 | a `healthcheck` on `kb-index`: it has no shell, so the check can never pass |
| 2.05 | a label too many: an OpenTelemetry Prometheus exporter adds labels of its own (such as `otel_scope_name`) |
| 2.07, 2.09 | the raw path (`/tickets/<an id>`) or the query string in `http_route`, instead of the template |
| 2.08, 3.06 | milliseconds instead of seconds |
| 3.02, 3.03 | a cache, a retry, or an answer that does not wait for `kb-index` |
| 3.04 | a request observed twice (a middleware and a decorator), or not at all |
| 3.05 | the grader's q next to your one fine bucket: resolve a band |
| 3.07, 3.08 | evidence from a different run or profile than the checker's, or a verdict the measurement contradicts |
| 4.04, 6.03 and 6.04 `error` ("could not scrape svcdesk's /metrics") while CORE-2 passes | `/metrics` answered without a `text/plain` Content-Type: Prometheus 3 refuses to scrape it (M-03) |
| 5.04 | tests that assert only when the alert fires: add that it is not yet firing one evaluation earlier |
| 5.05 to 5.07 | a threshold that is not the declared burn rate, a missing route filter, a missing short window |
| 6.04 | a metric name no one exposes, or a panel on `ALERTS` |

## Submission, receipts and attempts

Same path as Labs 1 and 2; every command runs in your repository root (PowerShell users: `.\itsmlab.ps1`, `;`
instead of `&&`).

1. **Implement**, running `./itsmlab.sh verify 3` (Windows: `.\itsmlab.ps1 verify 3`) as often as you like. Tier A
   runs are unlimited and never count.
2. **Commit and push**: `git add -A && git commit -m "Lab 3 attempt 1" && git push origin main` (Windows:
   `git add -A; git commit -m "Lab 3 attempt 1"; git push origin main`).
3. **Verify the committed tree**: `./itsmlab.sh verify 3` (Windows: `.\itsmlab.ps1 verify 3`) exits 0 and its
   `commit` line does not say `(dirty)`.
4. **Tag and push the tag**: `git tag -a lab3/v1 -m "Lab 3 attempt 1"` and `git push origin lab3/v1`. Tier B
   grades the tag's files, never your working directory.
5. **Submission receipt**: `./itsmlab.sh submit 3 --kind submission --tag lab3/v1` (Windows:
   `.\itsmlab.ps1 submit 3 --kind submission --tag lab3/v1`). Open the URL while logged in to GitHub as the login you
   measured, submit the issue, keep the receipt.
6. Three attempts. Attempt 1 is due Sunday 11 October 2026, 23:59:59 (Europe/Warsaw); that deadline is advisory - a
   receipt after it is marked `after_attempt1_due` and still counts. Attempts 2 and 3 are the correction window and
   close **Saturday 24 October 2026 at 08:00:00 Europe/Warsaw**, on the morning of session 4; a receipt after that
   instant is `late` and still counts, with 10 % off its points if it arrives before the lecture of session 5
   (Saturday 14 November 2026, 13:30) and 50 % off after that. The best attempt counts, after its penalty.
7. The grade arrives as a comment `itsmlab grade` on the same issue. No comment after an hour: ask on the forum
   with the issue number.

## What the grader does that the checker cannot

Nothing in Lab 3 is withheld: the rules, the instruments and every check are published, and the practice profile
shows you a distribution of the same kind as yours. The grader runs the same checker, from the same image pinned by
digest, on its own machine, against your receipted tag, with the `kb-index` profile of **your receipt's login**. The
only difference is that its run is the one that counts.

Two things follow. The q it measures differs from yours by a few per cent - another machine, another 2,400 random
draws - so resolve a band around your q, not your laptop's number (3.05), and measure your evidence with the
published command, so that it stays within 30 % of the grader's q (3.07). And the login decides the profile: if you
measured another one (a wrong `login:`, an organisation as the owner in `repository:`), your ladder was designed
for somebody else's distribution.

A classmate's ladder is worthless to you: their profile is not yours.

## The AI-disclosure header

Every file the `ai-disclosure` advisory covers (see the end of [CHECKS.md](CHECKS.md)) carries in its first ten
lines - or in the ten lines after a leading YAML front matter - a comment matching `ai-generated: <0-100>% - <one line
on how>`. For Lab 3 that is every file under `src/`, `specs/`, `metrics/`, `genai/` and `gap/` with extension
`.py .go .ts .js .java .cs .rb .rs .kt .md`, every `prometheus/*.yml`, every `k8s/*.yaml` and `k8s/*.yml`, and
`DECISIONS.md`, `EDGE-CASES.md`, `slo.md`, `ai-first-draft.md`:

    # ai-generated: 60% - an assistant wrote the recording rules, I wrote the tests        (YAML, Python)
    // ai-generated: 0% - by hand                                                          (Go, TypeScript, Java, ...)
    <!-- ai-generated: 30% - outline by an assistant, text mine -->                        (Markdown)

In a file with YAML front matter (`slo.md`, `ai-first-draft.md`, `genai/DIFF.md`) the front matter must come first:
put the header on the line right after its closing `---`, as the templates do. In `prometheus/*.yml` it is a `#`
comment. The dashboards are JSON and carry no header. The templates' lines read `ai-generated: ??% - TODO ...` and
are flagged by the advisory until you replace `??` with a number. In `ai-first-draft.md` the answer is the
assistant's by construction; the header says how the rest of the file - the verdicts - was written. The checker
lists files without the header as an advisory; the course rules require it on every checked file.

## Style of the written artifacts

Plain prose. `slo.md` and `ai-first-draft.md` are read by the lecturer (after an AI pre-screen, see the disclosure
line above) and graded on whether you can defend your numbers, not on whether you can restate the rules:

- **the objectives**: why this availability objective and this latency objective, given what `kb-index`'s own
  failures and its slow mode do to them;
- **the threshold**: why this latency threshold, against the distribution you measured;
- **the ladder**: where your q falls, how wide its bucket is, how wide a band you resolved and why, and where you
  spent the rest of your (at most 30) boundaries;
- **page or chat**: which alert pages a person (P1) and which goes to chat (P2, P3) - what a page at that burn rate
  costs the person woken, and what waiting until morning would cost the users.

**Lab 6 reads this `slo.md`.** On 28 November a canary gate takes its window, its two objectives and its latency
threshold - which must then be at most 1 s - as the gate's thresholds, from the `slo.md` of your accepted Lab 3
submission. An objective your own service does not meet will make that gate roll back an honest release: choose the
objectives for the service and the `kb-index` you measured, not for the number you would like to see.

In `ai-first-draft.md` each verdict carries its arithmetic: the p99 you measured, the bucket of the ladder that holds
it, the bucket's width relative to the p99, and what `histogram_quantile` could report from that bucket.
