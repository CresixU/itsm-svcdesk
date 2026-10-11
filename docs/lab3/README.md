<!-- ai-generated: 0% - written by the course team -->
# Lab 3 - what is in this folder

| file | what it is |
|---|---|
| [HANDOUT.md](HANDOUT.md) | start here: goal, the `kb-index` dependency, how to measure, minute budget, specs, deliverables, submission |
| [MONITORING-SPEC.md](MONITORING-SPEC.md) | the whole rulebook, M-01 to M-31: the endpoint, the histogram, the measurement, the bucket rule, the SLO, the alerts with the checker's probes and mutants, the dashboard, the first draft, the Stretch options, the tolerances |
| [CHECKS.md](CHECKS.md) | every published Tier A check, generated from the checker itself |
| [compose-lab3.yml](compose-lab3.yml) | the three services to add to your `docker-compose.yml` (`kb-index`, and your own `prometheus` and `grafana`), `KB_INDEX_URL` for `svcdesk`, and a commented `toxiproxy` for Stretch 2 |
| [prometheus/prometheus.yml](prometheus/prometheus.yml) | the configuration of your own Prometheus: one scrape job, `svcdesk` |
| [prometheus/alerts.yml](prometheus/alerts.yml) | the skeleton of your alert rules, with one single-window example alert |
| [prometheus/alerts_test.yml](prometheus/alerts_test.yml) | the skeleton of your `promtool` tests, with the example alert's test and what kills each mutant |
| [grafana/provisioning/](grafana/provisioning/) | your own Grafana's datasource (uid `prometheus`) and a dashboard provider for `grafana/dashboards/` |
| [grafana/dashboards/README.md](grafana/dashboards/README.md) | where your dashboard JSON goes, and what the checker wants from it |
| [slo-template.md](slo-template.md) | the shape of `slo.md` |
| [ai-first-draft-template.md](ai-first-draft-template.md) | the shape of `ai-first-draft.md` |
| [buckets-flawed.example.yml](buckets-flawed.example.yml) | the instructor's flawed ladder (M-27) |
| [gap-template.json](gap-template.json) | Stretch 2: the shape of `gap.json` |
| [genai/DIFF-template.md](genai/DIFF-template.md) | Stretch 1: the shape of `genai/DIFF.md` |
| [k8s/values.yaml](k8s/values.yaml) | Stretch 3: the capped Helm values for kube-prometheus-stack |

## What to copy into your repository

At the start of the lab, into your repository root:

| from this folder | into your repository |
|---|---|
| `prometheus/` (all three files) | `prometheus/` |
| `grafana/` (the whole tree) | `grafana/` |
| the services of `compose-lab3.yml`, and `KB_INDEX_URL` | your `docker-compose.yml`, merged by hand |
| `slo-template.md` | `slo.md` |
| `ai-first-draft-template.md` | `ai-first-draft.md` |
| Stretch only: `gap-template.json`, `genai/DIFF-template.md`, `k8s/values.yaml` | `gap.json`, `genai/DIFF.md`, `k8s/values.yaml` |

`buckets-flawed.example.yml` is for reading and need not be in your repository: the checker carries its own copy of
the flawed ladder, and on the no-AI path you copy its fourteen numbers into `ai-first-draft.md`.

Nothing here is a solution. The templates show shapes and placeholders (`TODO`), and the checks refuse the
placeholders in every file they read. The one worked alert in `prometheus/alerts.yml` is a single-window rule that
the checker's reset probe fails on purpose: it is there to show the file formats and the two test edges that kill
mutants, and it goes when your own alerts arrive.

Everything about the checker, receipts, attempts and deadlines is in the course [README](../README.md).
