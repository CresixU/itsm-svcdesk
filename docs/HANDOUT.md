<!-- ai-generated: 0% - written by the course team -->
# Lab 1 - Build `svcdesk` from a contradictory specification

Saturday 19 September 2026, 150 minutes, fully online. AI Assessment Scale level 4 (Full AI). Peak container RAM
about 0.4 GB.

Disclosure: reasoning artifacts are pre-screened by an AI model; all grades are assigned by the lecturer.

## Goal

Build the service-desk API `svcdesk` that the whole semester runs on, from a requirements document that contains
three pairs of requirements that cannot both hold. The service must pass the published conformance checks, and
`DECISIONS.md` must declare and defend the way you resolved each pair, matching what your running service actually
does. A single prompt produces code; it cannot produce a decision about which requirement to break and why. That
decision, defended in writing, is the work of this lab.

Read, in this order: [REQUIREMENTS.md](REQUIREMENTS.md) (what the desk wants), [API.md](API.md) (the exact HTTP
contract), [CHECKS.md](CHECKS.md) (every check the checker runs), [DECISIONS-template.md](DECISIONS-template.md)
(the shape of your reasoning artifact). `./itsmlab.sh checks 1` prints the same catalogue from the checker itself,
and `--markdown` prints exactly `CHECKS.md`; it runs nothing, so it is safe at any point in the lab. The course
[README](../README.md) explains the checker, the receipts and the deadlines.

## Minute budget

Core items sum to 110 minutes; the remaining 40 are slack. If an item overruns by more than its budget, stop, run
the checker, and ask on the forum with the check id.

| # | Core item | minutes | at |
|---|---|---|---|
| 1 | Read REQUIREMENTS.md, API.md and CHECKS.md; write down the three conflicting pairs and what each check accepts | 15 | 15 |
| 2 | Constitution and specification (spec-kit or by hand) under `specs/`; push; obtain the `specs` receipt | 20 | 35 |
| 3 | `DECISIONS.md`: three decisions, five labels each, values matching what you will build | 15 | 50 |
| 4 | Plan and tasks (spec-kit `plan` and `tasks`, or a list by hand) | 10 | 60 |
| 5 | Implement: `/health`, ticket create / get / list, validation, priority | 15 | 75 |
| 6 | Implement: state machine, reopen window, test clock | 10 | 85 |
| 7 | Implement: SLA due instants on both clocks (the eight vectors), `/sla` breach and pause | 15 | 100 |
| 8 | Run the checker until every Core spec passes; tag; obtain the `submission` receipt | 10 | 110 |
| | slack | 40 | 150 |

Item 2 comes before item 5 for a reason: Core spec L1-CORE-5 requires your specs to be receipted before any file
under `src/` is committed. Do not write code first and specs later; the receipts record the order.

## The three conflicts

From the course design, quoted so that there is no ambiguity about the rules:

> The document contains three pairs of requirements that cannot both hold; each conflict is resolved by rejecting
> the minimal conflicting part of one requirement and keeping everything else in the pair, which is why both sides
> of each pair are still tested; the published checks (`CHECKS.md`) show the admissible outcomes, so the pairs are
> discoverable by reading. Each contradiction has exactly two admissible resolutions; the checker accepts any of the
> eight combinations, provided `DECISIONS.md` declares the one the running service exhibits and defends it.

The three decisions are named C1 (SLA clock for P1), C2 (closed tickets and reopening) and C3 (VIP reporters and
the priority matrix). Their admissible values are in the template's front matter and in API.md. Which requirements
form each pair, which part you reject, and why, is yours to work out and to write down. There is no correct
resolution, only defended ones; the grade does not depend on which side you pick.

## Core specs (all must pass; no partial credit inside the bundle)

| spec | what it checks |
|---|---|
| L1-CORE-1 `compose-up` | the compose contract: a service `svcdesk` built from your repository (`build:`, never `image:` alone), no bind mounts in the resolved configuration, `docker compose up --wait` and `/health` within 120 s |
| L1-CORE-2 `conformance` | 49 HTTP checks: health, validation, the priority matrix, the state machine, the reopen window, the SLA vectors, breach and pause, the test clock |
| L1-CORE-3 `decisions-structure` | `DECISIONS.md` has the front matter, admissible values, three sections, five labels with at least 20 characters each |
| L1-CORE-4 `decisions-consistency` | the values declared in `DECISIONS.md` equal the ones the checker observed on your running service (checks 2.41, 2.35, 2.46) |
| L1-CORE-5 `spec-first` | grader-only: a `specs` receipt exists whose commit is an ancestor of the submission, and every commit adding a file under `src/` (other than `src/README.md`) descends from it. Tier A reports it as `skip`; Tier B checks it from the receipts |

## Stretch (any two of three; each lifts the grade band equally)

| option | what it checks |
|---|---|
| S1 `converge-report` | a file `specs/**/converge*.md` or `CONVERGE.md` of at least 400 characters that mentions at least three distinct requirement ids `R-nn`, all within R-01..R-25: the comparison the spec-kit `converge` step prints, saved by you to that file (the step does not write it, see "AI usage"), or your own written comparison of the specification with what was built |
| S2 `agent-config` | `CLAUDE.md`; at least one `.claude/agents/*.md` sub-agent whose front matter has a `disallowedTools` list of at least three entries; `AGENT-POLICY.md` with one line per entry, `- <entry verbatim>: <justification of at least 20 characters>`, each a blast-radius decision. The course calls this a narrow allowlist; technically `disallowedTools` is a denylist: you name what the agent may never do |
| S3 `own-tests` | a compose service `tests` under `profiles: ["tests"]`; `docker compose --profile tests run --rm --build tests` exits 0 within 300 s (both tiers; killed after that) and its last stdout line is `ITSMLAB-TESTS: passed=<n> failed=0` with n at least 10: your own suite against your own service, read from `SVCDESK_URL`; the tests image is built before the grader blocks egress, so it too installs everything at build time |

An example for S2, from the reference layout: `disallowedTools: [Bash(rm *), Bash(git push *), Bash(docker *), WebFetch]`
in `.claude/agents/reviewer.md`, and in `AGENT-POLICY.md` a line `- Bash(rm *): the reviewer reads and comments; deleting files is the author's decision, not the reviewer's`.

## AI usage

| Core AI step | default | free alternative (no card) | without AI |
|---|---|---|---|
| the spec-kit chain (constitution, specify, plan, tasks, implement) | Claude Code | Gemini CLI, GitHub Copilot Free | specs and code written by hand |

Claude Pro is never required. All three columns reach the same grade bands; the checks do not know which you used.
Claude Code on the web solves hardware, not quota: it draws on the same account's limits. If your quota is low at
the start of the session (run `/usage` in Claude Code), switch to the free alternative now, not at minute 100.
Quota exhaustion is never a reason for a deadline extension.

This is the lab where AI does the most work, on purpose: it sets the baseline the rest of the semester measures
against. AIAS level 4 means you may use AI for any part of the work; you must disclose it (the header below), and
you remain responsible for every line and every decision.

spec-kit, if you use it (the `--integration` value is `claude`, `gemini` or `copilot`; run it in your repository):

    uvx --from git+https://github.com/github/spec-kit.git@v1.0.6 specify init --here --integration claude

It asks `Do you want to continue? [y/N]` because the repository is not empty: answer `y` (or add `--force`). It
only adds `.claude/` (or `.gemini/`, `.github/` for the other integrations) and `.specify/`; nothing from the
template is overwritten. Commit those directories.

On Windows it also asks `Choose script type (or press Enter)`: press Enter to keep `ps`, the PowerShell scripts
that run in the Windows PowerShell you already have. They run only after the execution policy of PREWORK.md
step 2 (`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`). If `init` stops with `claude not found` because
you use Claude Code through the Desktop app or an editor extension rather than the `claude` command, add
`--ignore-agent-tools`.

The command names depend on the integration: Claude Code and Copilot get skills named with a hyphen, Gemini CLI
gets commands named with a dot (`.gemini/commands/speckit.*.toml`, as its `init` output says):

| step | Claude Code, Copilot | Gemini CLI |
|---|---|---|
| constitution | `/speckit-constitution` | `/speckit.constitution` |
| specify | `/speckit-specify` | `/speckit.specify` |
| plan | `/speckit-plan` | `/speckit.plan` |
| tasks | `/speckit-tasks` | `/speckit.tasks` |
| implement | `/speckit-implement` | `/speckit.implement` |
| converge (S1) | `/speckit-converge` | `/speckit.converge` |

Run the chain in two halves, because the `specs` receipt sits between them (L1-CORE-5):

1. Before any code: constitution and specify. Feed the agent REQUIREMENTS.md and API.md; spec-kit writes
   `specs/<nnn>-<feature>/spec.md`, which is what the `specs` receipt looks for. Then **stop**: commit `specs/`
   (with `.specify/` and `.claude/`, `.gemini/` or `.github/`), push `main`, and obtain the `specs` receipt
   (steps 1 and 2 of "Submission, receipts and attempts" below). Plan and tasks may come before or after the
   receipt: they write under `specs/`, never under `src/`.
2. After the receipt comment has appeared: plan, tasks, implement, and for S1 converge.

S1 needs a file that the converge step does not write. In the pinned spec-kit, `/speckit-converge`
(`/speckit.converge`) prints its comparison of the specification with the implementation in the conversation
and at most appends remediation tasks to `tasks.md`; when everything converges it writes nothing, and S1 fails
with `no file matching specs/**/converge*.md or CONVERGE.md`. So, after it has run, save the comparison: ask the
agent to write it to `specs/converge.md` with at least 400 characters and the ids of at least three
requirements it checked (R-01..R-25), or write that file yourself without spec-kit. The check reads only the
file.

## Rules

- **No network at run time.** Your image installs its dependencies at build time. The grading sandbox has no
  network once the image is built; a service that pulls anything at start fails L1-CORE-1.
- **Build, do not pull.** `svcdesk` must have a `build:` key; a service that only names an `image:` fails 1.01,
  because the Core bundle is earned by the code in your repository (your Dockerfile may start `FROM` any base).
- **No bind mounts.** No `./x:/y`, `/x:/y` or `type: bind` volumes on any service, in override files or through
  `.env` either (the check reads the resolved configuration). The checker runs `docker compose` from inside a
  container, where your host paths do not exist. Named volumes and `tmpfs` are fine.
- **Specs before code.** The `specs` receipt first; only then files under `src/`.
- **Tags never move.** Each attempt is a new tag (`lab1/v1`, `lab1/v2`, `lab1/v3`). A tag that moved after its
  receipt voids the attempt, and the attempt still counts.
- **No personal data in the repository**: no hostnames, no usernames, no `doctor` output. That goes to Moodle.
- **Every source and specification file carries the AI-disclosure header** (the exact set is below).

## Deliverables

A public GitHub repository created from the course template, at the receipted tag, containing:

- `specs/`: the specification written before the code (at least one file of 500 bytes or more);
- `src/`: the implementation, in any language;
- `DECISIONS.md`: the three decisions, in the template's structure;
- `docker-compose.yml`: the compose contract of API.md section 9;
- a passing conformance run: the grader runs the checker itself; your reported result is not used.

## Submission, receipts and attempts

The complete path, in order. Every command runs in your repository root: bash on Linux and macOS, PowerShell
on Windows (`.\itsmlab.ps1` instead of `./itsmlab.sh`; `;` instead of `&&`).

1. **Specs**: write `specs/` (nothing under `src/` yet), commit and push:
   `git add -A && git commit -m "Lab 1 specs" && git push origin main`.
2. **Specs receipt**: `./itsmlab.sh submit 1 --kind specs` (`.\itsmlab.ps1 submit 1 --kind specs`), open the
   printed issue-form URL, submit the issue, wait for the bot's receipt comment (about a minute). Only then
   start on `src/`.
3. **Implement**: `DECISIONS.md`, plan, tasks, code; run `./itsmlab.sh verify 1` as often as you like.
4. **Commit the implementation and push**: `git status` shows nothing to commit, otherwise
   `git add -A && git commit -m "Lab 1 attempt 1"`; then `git push origin main`.
5. **Verify the committed tree**: `./itsmlab.sh verify 1` exits 0, and its `commit` line does not say `(dirty)`.
6. **Tag that commit and push the tag**: `git tag -a lab1/v1 -m "Lab 1 attempt 1"` and `git push origin lab1/v1`.
   The tag must identify the same committed files that were verified: Tier B grades the tag's files, not your
   working directory, and an implementation you verified but never committed is absent from the tag.
7. **Submission receipt**: `./itsmlab.sh submit 1 --kind submission --tag lab1/v1` (`.\itsmlab.ps1 submit 1
   --kind submission --tag lab1/v1`). It warns when the working tree has uncommitted changes or HEAD has moved
   past the tag (then back to step 4, with the next tag name). Open the URL, submit the issue, keep the receipt.
8. Three attempts. Attempt 1 is due Sunday 20 September 2026, 23:59:59 (Europe/Warsaw); that deadline is
   advisory: a receipt after it is marked `after_attempt1_due` and still counts. Attempts 2 and 3 are the
   correction window and must be receipted before the next session: the window closes **Saturday 26 September
   2026 at 08:00:00 Europe/Warsaw**, when session 2 starts; a receipt after that instant is `late` and does not
   count. The best attempt counts. Tier A runs are unlimited and never count.
9. The grade arrives as a comment `itsmlab grade` on the same issue, usually within 20 minutes, with `grade.json`
   and its Sigstore bundle; README section 6 says how to verify it.

Details, expected outputs and troubleshooting: the course [README](../README.md).

## The AI-disclosure header

Every file under `src/` and `specs/` with extension `.py .go .ts .js .java .cs .rb .rs .kt .md`, plus
`DECISIONS.md`, carries in its first ten lines a comment matching `ai-generated: <0-100>% - <one line on how>`:

    # ai-generated: 80% - Claude Code drafted, I rewrote the SLA clock          (Python, Ruby)
    // ai-generated: 0% - by hand                                               (Go, TypeScript, Java, ...)
    <!-- ai-generated: 30% - outline by Gemini CLI, text mine -->               (Markdown)

That set (those extensions under `src/` and `specs/`, plus `DECISIONS.md`) is exactly what the checker reads;
YAML, shell, Dockerfiles and `requirements.txt` are not checked and need no header. An otherwise empty
`__init__.py` needs the one comment line too. In `DECISIONS.md` put it on the line right after the closing `---`
of the front matter (the template does); the template's placeholder `ai-generated: ??% - TODO ...` is flagged by
the advisory until you replace `??` with a number. The checker lists the files without it as an advisory; the
course rules require it on every checked file. A single 400-line commit is not a failing artifact; it is an
artifact whose checks will be looked at harder.

## Style of the written artifacts

Plain prose. `DECISIONS.md` is read by the lecturer (after an AI pre-screen, see the disclosure line above) and
graded on whether the reason is sound, the service owner is the right role, and the customer outcome named is the
one the behaviour actually serves. No stories, no personas, no filler: say what you decided, what you gave up, and
who bears the consequence.

## Checklist before you submit

- [ ] `./itsmlab.sh verify 1` exits 0 (every Core spec `pass`, L1-CORE-5 `skip`)
- [ ] `DECISIONS.md` front matter values equal what the checker observed: the line `observations  C1=...  C2=...  C3=...` at the end of `verify 1`, the `observations` object of `report.json` (the Actions step summary calls it "Observed resolutions")
- [ ] each of the five labels in each of the three sections carries real text (not `TODO`)
- [ ] the `specs` receipt exists, and no commit under `src/` predates it
- [ ] no bind mounts; the image needs no network at start
- [ ] every file under `src/` and `specs/`, and `DECISIONS.md`, carries the `ai-generated:` header
- [ ] `itsmlab.yaml` names your repository (`repository:`)
- [ ] the implementation is committed and pushed, `git status` is clean, and the tag points at the commit that
      `verify 1` reported (no `(dirty)`)
- [ ] the tag is pushed, the submission issue is filed, the receipt comment has appeared
- [ ] (Stretch) two of: converge report, agent config with `AGENT-POLICY.md`, `tests` profile with the summary line
