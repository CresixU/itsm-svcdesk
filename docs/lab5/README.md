<!-- ai-generated: 0% - written by the course team -->
# Lab 5 - what is in this folder

| file | what it is |
|---|---|
| [HANDOUT.md](HANDOUT.md) | start here: before the lab, the minute budget, the pipeline, triage, the bake-off and the canary step by step, specs, AI usage, deliverables, submission |
| [CI-SPEC.md](CI-SPEC.md) | the whole rulebook, P-01 to P-31: the pipeline and its gates, ignores, the canary, triage, the matching rule from SARIF to a confusion matrix, the order of the bake-off, the Stretch options, every threshold |
| [CHECKS.md](CHECKS.md) | every published Tier A check, generated from the checker itself |
| [pipeline/](pipeline/README.md) | the pipeline skeleton you copy into your repository: `ci.yml`, the course's composite actions, `.trivyignore`, `.gitleaksignore`, `tools/ai-to-sarif.py` and the Stretch 2 example workflow |
| [lab5-practice/](lab5-practice/README.md) | the practice set: a scanned repository, its SARIF, its labels and the expected matrix; keep it outside your repository |
| [bakeoff-skeleton.py](bakeoff-skeleton.py) | the command line and output shape of `bakeoff.py`, and nothing of the rules |
| [TRIAGE-template.md](TRIAGE-template.md) | the shape of `TRIAGE.md`: front matter, the table, `## Bake-off` |
| [mutation/](mutation/README.md) | Stretch 1: the course module `slaclock.py` and how its mutants are run |
| [semgrep-example/](semgrep-example/README.md) | Stretch 3: one rule and its test file, on a toy |

## What goes where

| from this folder | where it goes |
|---|---|
| `pipeline/.github/`, `pipeline/.trivyignore`, `pipeline/.gitleaksignore`, `pipeline/tools/` | your repository root, keeping the paths ([pipeline/README.md](pipeline/README.md)) |
| `bakeoff-skeleton.py` | `bakeoff.py` at your repository root, if you want to start from it |
| `TRIAGE-template.md` | `TRIAGE.md` |
| `mutation/slaclock.py` | `mutation/slaclock.py`, verbatim (Stretch 1); your tests go beside it |
| `semgrep-example/semgrep/` | `semgrep/`, then replace the toy with your rules (Stretch 3) |
| `pipeline/ai-review/`, `pipeline/.github/workflows/ai-review.yml.example` | Stretch 2 only: see HANDOUT.md |
| `lab5-practice/` | stays here: never in your repository |

Nothing here is a solution. The skeleton is the course's pipeline with one step left for you; the templates show
shapes and placeholders (`TODO`, `??`), and an unedited template fails its checks. The practice set's labels are
published so that you can learn the rules; your canary set's labels are revealed only after your SARIF receipt.

Everything about the checker, receipts, attempts and deadlines is in the course [README](../README.md).
