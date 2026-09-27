<!-- ai-generated: 0% - written by the course team -->
# Lab 2 - what is in this folder

| file | what it is |
|---|---|
| [HANDOUT.md](HANDOUT.md) | start here: goal, minute budget, specs, deliverables, submission |
| [METRIC-SPEC.md](METRIC-SPEC.md) | the whole rulebook: five metrics, six edge cases, the two endpoints, the gaming gates, the tolerances |
| [CHECKS.md](CHECKS.md) | every published Tier A check, generated from the checker itself |
| [EDGE-CASES-template.md](EDGE-CASES-template.md) | the shape of your reasoning artifact |
| [gaming-template.json](gaming-template.json) | the shape of `gaming.json` |
| [fixtures/events-practice.jsonl](fixtures/events-practice.jsonl) | the practice event log, 230 events |
| [fixtures/metrics-practice.json](fixtures/metrics-practice.json) | its **published** expected values - the answer key for the practice set |

The practice fixture's expected values are published on purpose: it is the teaching set, and you should be able
to see every failure before you submit. The **graded** fixture is generated from your own seed, is never
published, and is scored against values the grader computes from `METRIC-SPEC.md` itself.

**Copy `fixtures/` into your repository root** at the start of the lab: you need the log locally to compute
`metrics.json` and to build `gaming/after.jsonl`. The checker carries its own copy of both files inside the
image, so `./itsmlab.sh verify 2` (Windows: `.\itsmlab.ps1 verify 2`) works with no network - and editing your copy
changes nothing it checks.

Everything about the checker, receipts, attempts and deadlines is in the course [README](../README.md).
