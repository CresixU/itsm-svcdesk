---
lab2_edge_cases:
  E1: {rule: R-08, count: 3}
  E2: {rule: R-06, count: 2}
  E3: {rule: R-09, count: 4}
  E4: {rule: R-10, count: 4}
  E5: {rule: R-12, count: 1}
  E6: {rule: R-13, count: 11}
---
<!-- ai-generated: 90% - Claude Code drafted this from METRIC-SPEC.md and the running service's own answers; the author chose the gaming demonstration's target metric and reviewed every count against fixtures/metrics-practice.json -->

# Edge cases in the practice event log

## E1 - clock skew produces a negative lead time

- What the log contains: three (commit, deployment) pairs in the practice log where the commit's `at` is later than the deployment that shipped it, because the two systems that stamped the events disagreed about the time.
- What a default definition would have done: an assistant's first-draft `deployment.at - commit.at` formula would return a negative number of seconds for these three pairs, which is nonsensical as a lead time and would either crash a naive implementation's duration parser or silently corrupt the median with negative outliers.
- Why the rule is defensible: R-08 clamps the pair to zero and still counts it, rather than discarding it. Throwing the pair away would understate the sample size and hide that clock skew happened at all; clamping keeps the pair honest about "at least this fast" while `anomalies.negative_lead_time_pairs` makes the skew visible on the dashboard instead of burying it inside the median.

## E2 - a revert of a revert

- What the log contains: a commit that reverts an earlier commit, and a second commit that reverts that revert - two hops of `reverts` chaining back to one original change (`sha-0070` reverts `sha-0069`, `sha-0071` reverts `sha-0070`).
- What a default definition would have done: a definition that treats every non-null `change_id` as its own change, and falls back to "no change" for every commit whose `change_id` is null, would count this as zero or two extra changes depending on how it handles nulls, when the correct answer is that all three commits belong to exactly one change.
- Why the rule is defensible: R-06 resolves `reverts` transitively so a revert of a revert collapses back to the original change, matching what actually happened to the codebase: the change landed, was reverted, and the revert was itself reverted, so the original change is back in effect and R-11's frequency and R-08's lead time are computed against one unit of work, not three.

## E3 - a hotfix that never touched `main`

- What the log contains: four commits on branches named `hotfix/*` that were each deployed straight to production without ever being merged to `main`, because the incident that needed them could not wait for the normal branch.
- What a default definition would have done: an assistant asked to compute "lead time from commit to deploy" nearly always writes it as "time from merge to main until deployment," which would silently exclude every one of these four commits from the metric entirely, understating both deployment frequency and true lead time for real, shipped work.
- Why the rule is defensible: R-09 makes `branch` irrelevant to whether a commit counts; a customer whose outage was fixed by a hotfix does not care which git ref carried the fix. `anomalies.commits_never_on_main` keeps the process signal (how often the team bypasses its own branch policy) visible as a separate, auditable number instead of quietly deleting the evidence.

## E4 - a deployment with zero linked commits

- What the log contains: four production deployments in the window whose `commits` array is empty - a re-deploy of the existing image, a rollback, or a configuration-only release with nothing new to trace back to a commit.
- What a default definition would have done: a naive implementation iterating "for each deployment, for each commit" would simply skip these deployments when computing lead time, then quietly also drop them from the denominators of deployment frequency and the failure rate, because nothing downstream ever touched them.
- Why the rule is defensible: R-10 keeps these deployments in every count that is about the act of deploying (frequency, the change-fail-rate denominator, the rework-rate denominator) while correctly excluding them from a metric about commit-to-production time, since there is no commit to measure from. A deployment is still an operational event even when it ships no new code.

## E5 - a deployment that failed and never recovered

- What the log contains: one failed production deployment in the window whose incident was opened but never resolved by the time the window's data was captured - the recovery is still in progress.
- What a default definition would have done: an assistant's formula for recovery time, `resolved_at - deployment.at`, throws a null-arithmetic error or, worse, silently substitutes "now" for the missing `resolved_at`, which invents a recovery time for an incident nobody has actually closed.
- Why the rule is defensible: R-12 excludes an unresolved (or uncovered) failure from the recovery-time median entirely rather than inventing a number, and instead counts it in `counts.open_failures`, so the dashboard shows "one incident is still open" as its own fact rather than folding a fabricated duration into a metric that is supposed to describe completed recoveries.

## E6 - overlapping incidents

- What the log contains: eleven unordered pairs of incidents in the log whose opened/resolved intervals overlap in time - the team was fighting more than one fire in the same stretch of the month.
- What a default definition would have done: a definition that merges overlapping incidents into one, or sums their durations, would either undercount how many separate things went wrong at once or double-count the same wall-clock time as multiple hours of "being in an incident," inflating any aggregate built on top of it.
- Why the rule is defensible: R-13 computes failed-deployment recovery time per failed deployment, never per incident, and never merges or sums overlapping intervals; `anomalies.overlapping_incident_pairs` reports the overlap as a fact about how the team's time was actually spent, which is a capacity signal a retrospective needs, not a number a formula should try to net out on its own.

## Gaming demonstration

I improved `change_lead_time_seconds_p50` by exploiting R-08: the rule pairs a successful production commit with the *first* successful production deployment that carried it, and clamps but still counts every pair, with no floor on how small a genuine gap between commit and deploy is allowed to be. `gaming/after.jsonl` adds 150 trivial commits, each wrapped in its own throwaway change and deployed roughly two seconds after it is written, alongside the real 230-event log; none of the real events are touched, deleted, re-timed, or flipped, which is exactly what R-19 permits. Flooding the log with near-instant commit-to-deploy pairs pulls the median from 375,643 seconds (about 4.3 days) down to 2 seconds - a 99.9994% improvement, far past the 25% margin - without a single line of real, shipped work moving any faster. At the same time, I moved the ten latest real successful deployments in the window out past the observation window entirely (permitted: R-19 only forbids moving a deployment *earlier*). Filtered down to the base work alone, that drops `ground_truth.changes_delivered` from 65 to 48 - 73.8% of the base count, comfortably past the 90% harm threshold - because real changes that used to ship inside the window now ship after it, or never show up in this window's data at all.

The incentive this rewards in a real team is the oldest one in the book: once "lead time" is the number a dashboard shows to management, the fastest way to move it is to ship a flood of trivial, low-risk commits (a comment fix, a version bump, a config toggle) on a hair-trigger pipeline, while the actual feature work - the multi-day change that needed review, testing and a real release window - quietly slips to next sprint or gets held back until "the metrics look better this week." The engineers who batch-ship trivial commits look like the fastest team in the org chart; the engineer still working the hard ticket looks slow by comparison, even though delivery of real customer value got strictly worse. Whoever is compensated or promoted on the dashboard's headline number - not on what actually reached the customer - is the one this gaming move rewards, and it is exactly the trap DORA's own pitfall list warns about: never let the metric become the target.
