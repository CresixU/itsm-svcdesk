<!-- ai-generated: 0% - written by the course team -->
# Lab 4 - what is in this folder

| file | what it is |
|---|---|
| [HANDOUT.md](HANDOUT.md) | start here: the two paths, the pre-work, the minute budget, the incident step by step, specs, AI usage, deliverables, submission |
| [INCIDENT-SPEC.md](INCIDENT-SPEC.md) | the whole rulebook, I-01 to I-32: the injector and its fault pool, the recording each login works, the pager, alerting and routing, the four timestamps, the ticket, the postmortem, the AI ledger, the Stretch options, every threshold |
| [CHECKS.md](CHECKS.md) | every published Tier A check, generated from the checker itself |
| [playground/](playground/README.md) | the course overlay for the OpenTelemetry Demo 3.1.0: `compose.itsm.yaml`, the course Prometheus configuration, and the commands to start, reset and snapshot the playground |
| [agent/](agent/) | the course's Prometheus MCP server (`prom_mcp.py`, read-only) and a minimal agent loop for any OpenAI-compatible model (`agent.py`), with their pinned `requirements.txt` |
| [recorded/](recorded/README.md) | the recorded incident: the path for machines with less than 12 GB of RAM, the three recordings and which one your login works (`itsmlab recording 4`), how to serve a snapshot, and the recorded investigator's transcript for the path without AI |
| [demo-alerts-template.yml](demo-alerts-template.yml) | the shape of `prometheus/demo-alerts.yml`, with one commented example rule |
| [alertmanager-template.yml](alertmanager-template.yml) | the shape of `alertmanager/alertmanager.yml`: the two receivers, a routing skeleton, a commented inhibit rule |
| [routing-tests-template.yml](routing-tests-template.yml) | the shape of `alertmanager/routing-tests.yml` |
| [postmortem-template.md](postmortem-template.md) | the shape of `postmortem.md`: the front matter, the thirteen fields, the problem record |
| [ai-rca-eval-template.json](ai-rca-eval-template.json) | the shape of `ai-rca-eval.json`, one example entry per verdict |
| [comms-log-template.md](comms-log-template.md) | Stretch 2: the shape of `comms-log.md` |

## What goes where

| from this folder | where it goes |
|---|---|
| `playground/` | into your clone of the demo, as `itsm/` - not into your repository ([playground/README.md](playground/README.md)) |
| `demo-alerts-template.yml` | `prometheus/demo-alerts.yml`, next to Lab 3's `alerts.yml` |
| `alertmanager-template.yml` | `alertmanager/alertmanager.yml` - before you first start the playground, whose Alertmanager needs it |
| `routing-tests-template.yml` | `alertmanager/routing-tests.yml` |
| `postmortem-template.md` | `postmortem.md` |
| `ai-rca-eval-template.json` | `ai-rca-eval.json` (and `ai-rca-eval-2.json` for Stretch 1) |
| `comms-log-template.md` | `comms-log.md` (Stretch 2 only) |
| `agent/` | stays here: you run it from your repository root, and it writes its transcript there |

Nothing here is a solution. The templates show shapes and placeholders (`TODO`), and an unedited template fails its
checks. The example rule, route and ledger entries illustrate the syntax on the shop's real metrics; your alerts,
your routes, your predictions and your verdicts are yours to design, and the fault that tests them is drawn only
when you arm the injector.

Everything about the checker, receipts, attempts and deadlines is in the course [README](../README.md).
