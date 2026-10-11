---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: TODO                  # a duration from 7d to 90d, such as 28d or 30d
  slis:
    availability:
      objective: TODO           # in [0.9, 1), at most five decimals
      good: 'TODO - PromQL: the rate of good /kb/search requests over [5m], as ONE sample'
      valid: 'TODO - PromQL: the rate of all /kb/search requests that count, over [5m], as ONE sample'
      error_budget: {fraction: TODO, minutes: TODO}      # 1 - objective; that fraction x the window in minutes
    latency:
      objective: TODO
      threshold_seconds: TODO   # one of your ladder's finite boundaries (M-13)
      good: 'TODO - PromQL: the rate of /kb/search requests at or below threshold_seconds, as ONE sample'
      valid: 'TODO - PromQL, as ONE sample'
      error_budget: {fraction: TODO, minutes: TODO}
  alerts:                       # two or more on the SAME sli, with DIFFERENT burn rates (M-16)
    - {alert: TODO, sli: TODO, burn_rate: TODO, long_window: TODO, short_window: TODO}
    - {alert: TODO, sli: TODO, burn_rate: TODO, long_window: TODO, short_window: TODO}
---
<!-- ai-generated: ??% - TODO replace ?? with a number and say in one line how this file was written -->

# SLO for `GET /kb/search`

Copy this file to `slo.md` at your repository root and replace every `TODO` above; MONITORING-SPEC.md section 5
has the rules (M-13 to M-16) and a filled-in example with made-up numbers. What the checker does with the front
matter:

- `L3-CORE-4.01` and `4.02`: every field is there, and the error-budget arithmetic holds;
- `4.03`: `threshold_seconds` is one of the boundaries your service exposes;
- `4.04`: the checker's Prometheus runs each `good` and `valid` after its measurement, and each returns exactly one
  sample (aggregate with `sum`), `valid` above 0, good / valid between 0 and 1. Its scrape job is `svcdesk`; never
  select an `instance`; write `le` as Prometheus 3 stores it, which may differ from what your service exposes:
  `le="0.3"`, `le="1.0"` (MONITORING-SPEC.md section 5, "The `le` label is text");
- `4.05` and L3-CORE-5: every alert declared here exists in `prometheus/alerts.yml` under the same name, with the
  label `slo` equal to its `sli` here, and behaves as declared - the checker's probes use exactly the burn rate and
  the windows you write here.

Everything below the front matter is read by the lecturer, not checked. Defend your numbers in plain prose; do not
restate the rules. Delete these instructions when you write the file.

## Availability

The SLI in words, the objective, and the error budget as a fraction and in minutes. Why this objective: what do
`kb-index`'s own failures, which you cannot fix, do to it?

## Latency

The SLI in words, the threshold, the objective, and the error budget. Why this threshold, against the distribution
you measured (your p50, p99 and the slow mode), and why this objective?
(Lab 6, on 28 November, reads this file's window, objectives and threshold - at most 1 s - as a canary gate's
thresholds: an objective your own service does not meet will make that gate roll back an honest release.)

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | TODO | TODO | TODO | TODO |

Which alert pages a person (P1) and which goes to chat (P2, P3), and why: what a page at that burn rate costs the
person woken, and what waiting until the morning would cost the users.

## Buckets

Your ladder, where the p99 you measured falls in it, how wide that bucket is relative to the p99, how wide a band
around it you resolved and why, and where you spent the rest of your (at most 30) boundaries.
