---
lab3_first_draft:
  source: ai                    # ai | instructor  (instructor = the no-AI path: the flawed ladder is your draft)
  tool: ""                      # TODO: the assistant and its model, where you used it, the date (required with ai)
  ladder: []                    # TODO: the assistant's boundaries, in seconds, exactly as it gave them
  verdict: TODO                 # confirmed (it resolves your p99, M-11) | refuted (it does not)
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
lab3_flawed_ladder:
  verdict: refuted              # the only admissible verdict (M-27); the evidence is yours to compute
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
---
<!-- ai-generated: ??% - TODO replace ?? with a number and say in one line how this file was written -->

# The assistant's first draft, and two verdicts

Copy this file to `ai-first-draft.md` at your repository root. The rules are M-25 to M-27 in MONITORING-SPEC.md
(section 9, with a filled-in example for the practice profile); the checks are `L3-CORE-3.07` to `3.09`.

1. **Before you measure or design anything**, ask an assistant for histogram bucket boundaries and an alert rule
   for `GET /kb/search`. Paste your prompt under `## Prompt` and its whole answer under `## Answer`, verbatim. If
   the answer itself contains lines that begin with `## `, put `> ` in front of every line of it: the checker
   reads a section up to the next line that begins with `## `, and each section needs at least 40 characters.
2. Copy its ladder into `ladder`, in seconds, exactly as it gave it.
3. Measure with `./itsmlab.sh load 3` (Windows: `.\itsmlab.ps1 load 3`) and write the p99 it prints as
   `p99_seconds`, in seconds, in both `evidence` blocks. It must be within 30 % of the checker's own q.
4. For each ladder, `bucket` is `[lo, hi]` of the bucket that holds that p99 (lo is 0 below the first boundary; hi
   is `"+Inf"` above the last), and `relative_width` is (hi - lo) / p99_seconds, to three decimals.
5. `verdict`: `confirmed` when hi is finite and hi - lo is at most 0.20 x p99, else `refuted`. The checker applies
   the same rule at its own q; both verdicts score the same, and only a verdict its measurement contradicts fails.

No AI at all: set `source: instructor`, delete `tool`, copy the fourteen boundaries of `buckets-flawed.example.yml`
into `ladder`, and delete `## Prompt` and `## Answer`. Delete these instructions when you write the file.

## Prompt

TODO

## Answer

TODO

## Verdict on the draft ladder

The arithmetic: the p99 you measured, the bucket of the draft ladder that holds it, its width relative to the p99,
and what `histogram_quantile` could report from that bucket. Then the verdict in one sentence.

## The draft alert rule

What the assistant's alert rule would have done for your SLO, and what you kept of it in `prometheus/alerts.yml`.

## Verdict on the instructor's flawed ladder

The same arithmetic for `buckets-flawed.example.yml`: where its resolution is spent, and where your p99 is.
