<!-- ai-generated: 0% - written by the course team -->
# Lab 5 - CI as arbiter: a real supply chain, and a measured bake-off

Saturday 14 November 2026, 150 minutes, fully online. AI Assessment Scale level 4 (full AI) on the Core path, with
one exception: Claude Pro is never needed (see AI usage). Peak container RAM on your laptop about 0.9 GB: almost
everything runs on GitHub's runners, which are free for public repositories.

Disclosure: reasoning artifacts are pre-screened by an AI model; all grades are assigned by the lecturer.

## Goal

Your pipeline becomes the arbiter of what reaches `main`. You copy the course's pipeline skeleton into your
repository - five scanners in three jobs, an image job that scans your container image, writes its SBOM and attests
it, a policy check on ignores - wire your own build and tests into it, and make `main` green by **triaging** what the
gates find: fix what can be fixed, ignore what cannot with a reason and an expiry, and write down why. Your image goes
to GitHub's container registry with two attestations, provenance and SBOM, that anyone can verify with
`gh attestation verify`.

Then you **measure** the scanners. Every reviewer, human or machine, is a detector with a precision and a recall
(Lecture 5). You write `bakeoff.py`, which turns scanner SARIF and a label file into a per-tool confusion matrix under
a published matching rule, and prove it on a published practice set. Then `itsmlab canary 5` adds your **canary
set** to a branch - service-desk code with seeded defects and decoys, hard-coded credentials, vulnerable pins, chosen
for your login - and your pipeline must turn red on it: the proof that your gates are wired, not merely present. You
commit the SARIF that red run produced, file a receipt for it, and only then does the course reveal which files of
your set hold defects. `bakeoff.json` is your `bakeoff.py` applied to that SARIF and those labels.

Nothing you write down is believed. The grader reads your runs and attestations from GitHub, recomputes your matrix
with its own implementation of the rules, and runs your `bakeoff.py` on labelled inputs of its own. **The direction of
a number is never graded**: a scanner with recall 0.2 scores exactly as one with 0.9. What is graded is that the
number was honestly produced and correctly computed.

One warning before you compare tools: seeded defects flatter every detector. Studies of injected and synthetic defects
find detection rates several times higher than on real ones, so read every recall in this lab as an upper bound. Your
set also holds defects that none of the five scanners can see.

Read, in this order: [CI-SPEC.md](CI-SPEC.md) (the whole rulebook, P-01 to P-31), [CHECKS.md](CHECKS.md) (every check
the checker runs), [pipeline/README.md](pipeline/README.md) (what to copy where), and the templates listed in
[README.md](README.md). `./itsmlab.sh checks 5` (Windows: `.\itsmlab.ps1 checks 5`) prints the same catalogue from
the checker itself. The course [README](../README.md) explains the checker, the receipts and the deadlines.

## Before the lab

Do this at home, in the week before 14 November.

1. **The GitHub CLI**, logged in to the account that owns your repository: https://cli.github.com, then
   `gh auth login` (GitHub.com, HTTPS, log in with a browser) and `gh auth status`. You use it to download your
   pipeline's SARIF (`gh run download`) and to verify attestations (`gh attestation verify`). Without it, both can be
   done in the browser and with `unzip`; the steps below say how.
2. **Your repository is public and Actions run in it** (they have since Lab 1: the `tier-a` workflow). Open
   Settings, Actions, General: "Allow all actions and reusable workflows" is fine; the skeleton uses only GitHub's own
   actions, pinned by SHA.
3. **The checker**: `docker pull ghcr.io/swasik/itsmlab:2026`, then `./itsmlab.sh --version` (Windows:
   `.\itsmlab.ps1 --version`) must print `itsmlab 0.8.6` or newer (the image published on 12 October 2026): an older
   image leaves root-owned files in `.git` after `canary 5` on Linux, and before 0.8.0 it does not know Lab 5.
4. **Only for Stretch 1**, optional: mutmut 3.8.0 (`uv tool install mutmut==3.8.0`) to explore your tests. It needs
   `fork`, so on Windows only inside WSL. You do not need it: `itsmlab mutants 5` runs the practice mutants in
   Docker.
5. **Only for Stretch 2**, optional: an AI reviewer - see AI usage. With Claude Pro or Max: `claude setup-token`
   prints a one-year token for your subscription; store it as the repository secret `CLAUDE_CODE_OAUTH_TOKEN`
   (Settings, Secrets and variables, Actions) and nowhere else. With Gemini: the AI Studio key of PREWORK step 8.

## If you have not finished Lab 4

Lab 5 reads nothing from Labs 2 to 4. It needs a `svcdesk` that builds from your repository and answers `GET /health`
(L5-CORE-1, as in every lab) and, for `build-test`, your tests. Lab 4's correction window closes on Saturday
14 November 2026 at 08:00:00 Europe/Warsaw, on the morning of this session; keep your Lab 4 files as they are.

## Before you start

1. In `itsmlab.yaml`, set `lab: 5`. Check that `login:` is your GitHub login (or absent: the owner of `origin` is
   then used). Your canary set is chosen for that login - the same `login:` that chose your `kb-index` profile in
   Lab 3.
2. **Copy the skeleton** into your repository root, keeping the paths: everything under [pipeline/](pipeline/)
   except its `README.md` and `ai-review/` (Stretch 2 only). From your repository root, with `<lab5>` the path of this
   folder:

       cp -r <lab5>/pipeline/.github <lab5>/pipeline/.trivyignore <lab5>/pipeline/.gitleaksignore <lab5>/pipeline/tools .
       cp <lab5>/pipeline/itsmlab.sh <lab5>/pipeline/itsmlab.ps1 .
       # Windows PowerShell:
       Copy-Item -Recurse -Force <lab5>\pipeline\.github, <lab5>\pipeline\.trivyignore, <lab5>\pipeline\.gitleaksignore, <lab5>\pipeline\tools, <lab5>\pipeline\itsmlab.sh, <lab5>\pipeline\itsmlab.ps1 .

   The copy adds `.github/workflows/ci.yml` and `.github/actions/`, and **replaces** your `tier-a.yml`, `itsmlab.sh`
   and `itsmlab.ps1` with versions that hand the checker a GitHub token, which Lab 5's checks need to read your runs
   (anonymous reads are limited to 60 an hour), and a `tier-a.yml` that checks out every branch with its history
   (`fetch-depth: 0`: the checks read `lab5/canary`) and tells the checker it runs in GitHub Actions
   (`-e GITHUB_ACTIONS`, see step 3 of the submission). Nothing else in those three files changed. An older
   `tier-a.yml` still works: the checker then fetches `lab5/canary` from your public repository itself, and a `ci.yml`
   run still in progress is `error` there, as it is locally. Keep the practice set, [lab5-practice/](lab5-practice/), **outside** your repository: its
   sources hold credentials and vulnerable pins by design, and your gates would find them.

## Minute budget

Core items sum to 110 minutes; the remaining 40 are slack. A pipeline run takes about three minutes on `main` and
one and a half on the canary (measured in the course's pilot; a first run downloads the scanners' databases and takes
longer): start one, then do the next item while it runs.

| # | Core item | minutes | at |
|---|---|---|---|
| 1 | Copy the skeleton, wire `build-test`, push; read the first run | 20 | 20 |
| 2 | Triage: make the `image` gate green, ignores with reasons, `TRIAGE.md`'s rows; make the package public | 30 | 50 |
| 3 | `bakeoff.py` against the practice set | 20 | 70 |
| 4 | The canary: `itsmlab canary 5`, push, the red run, download, commit, SARIF receipt, labels, `bakeoff.json` | 20 | 90 |
| 5 | `TRIAGE.md`'s `## Bake-off`; `./itsmlab.sh verify 5`, fix, tag, submit | 20 | 110 |
| | slack | 40 | 150 |

## Step by step

Every `./itsmlab.sh` below is `.\itsmlab.ps1` on Windows PowerShell, and `&&` is `;` there.

### 1. Wire the pipeline (P-01 to P-04)

Open `.github/workflows/ci.yml`. The job `build-test` has one placeholder step containing `ITSM-TODO` that fails on
purpose. Replace it with the commands that build your service and run your tests - for a repository from the course
template:

```yaml
      - name: Build and test
        run: |
          docker compose build svcdesk tests
          docker compose --profile tests run --rm tests
```

In `image`, check the two inputs `context` and `dockerfile` against your repository. Change nothing else yet. Commit,
push, and open the run (`gh run watch`, or the Actions tab). On a first run expect `build-test` green, `deps`,
`secrets` and `code` green or red depending on your dependencies, and `image` **red**: your image has fixable HIGH and
CRITICAL vulnerabilities. That is the triage.

Two rules of P-01 matter from the first minute: keep the job ids, and never give a job a `name:` - the grader reads
each job's conclusion from GitHub by its id. P-03 applies to everything you add: an action outside your repository is
pinned by a full commit SHA, and a value from `github.event` or `inputs` reaches a `run:` script only through `env:`.

### 2. Triage (P-04 to P-06, P-09 to P-12)

Read the `image` job's log: Trivy lists every HIGH and CRITICAL vulnerability that has a fix, per package. The usual
fixes, in this order:

1. **A current base image.** `docker pull python:3.13-slim`, then pin it by digest in your Dockerfile
   (`FROM python:3.13-slim@sha256:...`; `docker image inspect --format '{{index .RepoDigests 0}}' python:3.13-slim`
   prints it). A base image a few weeks old carries fixes it does not yet contain.
2. **`apt-get upgrade`** in the Dockerfile, right after the `FROM`:
   `RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*`.
3. **Python packages** Trivy names: raise the pin, or `pip install --upgrade` it in the image. Some findings resist
   this, and everyone meets them: pip carries its own copies of other packages in `pip/_vendor` (msgpack, setuptools'
   `pkg_resources` and urllib3 at the time of writing; Trivy finds them through pip's own bill of materials), and the
   newest pip release does not ship the fixed ones yet. The simplest answer is a runtime image without pip: pip is
   needed only to install, so end your `RUN pip install ...` line with `&& pip uninstall -y pip` (nothing in the
   course's svcdesk calls pip at run time), or use a multi-stage build that copies only the installed packages into
   the final stage. The other honest answer is one ignore per ID, each with its reason and expiry, as the course's
   reference does - count on four IDs or more, and on new ones appearing while the lab runs.
4. What is left, and only after you understand it: an entry of `.trivyignore` with its reason above it and an expiry
   within 90 days (P-06):

       # starlette 0.46 has no release with the fix for our pinned FastAPI; the vulnerable multipart path is
       # not reachable: svcdesk accepts only JSON bodies. Revisit when FastAPI 0.142 ships.
       CVE-2026-12345 exp:2027-01-31

   A bare ID, an ID without a reason, a past date or one more than 90 days ahead fails `ignore-policy`, and so the
   build.

Every change and every ignore gets a row in `TRIAGE.md` (start from [TRIAGE-template.md](TRIAGE-template.md)): Tool,
Rule, Decision (`fix`, `ignore`, `false-positive`, `accept`), and a Reason of at least 20 characters. Look at the
reporting scanners too - Grype, OSV-Scanner, Semgrep - in the run's code-scanning alerts (Security tab) or in the
SARIF: P-12 asks for a row for every rule they report on your own code, whatever you decide about it.

When `main` is green, the `image` job has pushed your image to `ghcr.io/<owner>/<repo>` and attested it. Then, once:

- **Make the package public** (P-09): your GitHub profile, Packages, the package, Package settings, Danger Zone,
  Change visibility, Public. A new package is private even from a public repository, and the grader cannot read a
  private one. This cannot be undone; it holds nothing your public repository does not.
- **Note the digest** the `image` job printed in its summary, and put it into `TRIAGE.md`'s front matter as
  `image: ghcr.io/<owner>/<repo>@sha256:...`, all in lower case.
- **Verify it yourself**, as the grader will:

      gh attestation verify oci://ghcr.io/<owner>/<repo>@sha256:<digest> -R <owner>/<repo> \
        --signer-workflow <owner>/<repo>/.github/workflows/ci.yml --source-ref refs/heads/main
      gh attestation verify oci://ghcr.io/<owner>/<repo>@sha256:<digest> -R <owner>/<repo> \
        --signer-workflow <owner>/<repo>/.github/workflows/ci.yml --source-ref refs/heads/main \
        --predicate-type https://spdx.dev/Document/v2.3

  Without `--predicate-type`, `gh attestation verify` checks the provenance only; the SBOM is the second call.

### 3. `bakeoff.py` against the practice set (P-14 to P-24)

Write `bakeoff.py` at your repository root from CI-SPEC.md section 3; [bakeoff-skeleton.py](bakeoff-skeleton.py) has
the command line and the output shape and nothing of the rules. Standard library only: it runs as
`python3 -S -E bakeoff.py`, so an `import yaml` fails even if your machine has PyYAML. Test it against the practice set
([lab5-practice/](lab5-practice/README.md)):

    python3 bakeoff.py --labels <lab5>/lab5-practice/labels.json <lab5>/lab5-practice/sarif/*.sarif

and compare with `<lab5>/lab5-practice/expected.json`; `./itsmlab.sh verify 5` does the same comparison as check 5.01.
No Python 3.13 on your machine, or `python3` is not a command (Windows)? With uv (PREWORK step 2):
`uv run --python 3.13 --no-project python -S -E bakeoff.py --labels ...` runs it exactly as the grader does. On
Windows PowerShell pass the SARIF files as `(Get-ChildItem <lab5>\lab5-practice\sarif\*.sarif).FullName`: PowerShell
does not expand `*` for a native program.
The practice SARIF is real scanner output, with every trap your canary's will have. CI-SPEC.md section 3.4 walks six
of its results through the rules.

An assistant may write `bakeoff.py` with you (AIAS level 4). It will not get the rules right unless you give it
CI-SPEC.md section 3 and check its output against `expected.json`, and the grader also runs it on inputs you have
never seen (P-28).

### 4. The canary (P-07, P-08, P-25 to P-27)

With `main` green, pushed and your working tree clean:

    ./itsmlab.sh canary 5
    git push origin lab5/canary

`itsmlab canary 5` creates branch `lab5/canary` - one commit on top of your `main` adding your set under
`lab5-canary/` - without switching branches or touching your working tree. The push starts a run on the canary.
**Both `deps` and `secrets` must end red** (P-08); `capture` still runs, and on this branch it attests the SARIF.
If a gate stays green on the canary, your gate is not wired - fix the pipeline on `main`, delete the branch
(`git branch -D lab5/canary && git push origin --delete lab5/canary`), and start again.

Never edit, rebase or merge the canary branch: the grader checks that it adds exactly your set (P-07).

When the canary's run has finished, bring its SARIF to `main`, unchanged:

    gh run list --branch lab5/canary --workflow ci.yml --limit 1        # the run id
    gh run download <run id> -n sarif -D bakeoff/sarif
    git add bakeoff/sarif && git commit -m "Lab 5: the canary's SARIF" && git push origin main

(Without the GitHub CLI: the run's page, Artifacts, `sarif`, download the zip and unzip it into `bakeoff/sarif/`.)
Do not reformat or trim the files: the grader checks each against the attestation the run made (P-26).

Then the receipt, from `main` with that commit at its head:

    ./itsmlab.sh submit 5 --kind sarif

Open the URL it prints and submit the issue. The bot answers with a receipt, and within a few minutes the course
posts your labels on the same issue, in a comment whose first line is `itsmlab labels`. Save them and compute the
matrix:

    ./itsmlab.sh labels 5 --issue <issue number>                 # writes bakeoff/labels.json
    python3 bakeoff.py --labels bakeoff/labels.json bakeoff/sarif/*.sarif > bakeoff.json
    git add bakeoff/labels.json bakeoff.json && git commit -m "Lab 5: the bake-off" && git push origin main

(Windows PowerShell: `python bakeoff.py --labels bakeoff/labels.json (Get-ChildItem bakeoff/sarif/*.sarif).FullName |
Set-Content -Encoding utf8 bakeoff.json` - a plain `>` in Windows PowerShell 5.1 writes UTF-16.)

Your labels are revealed once, on your first valid `sarif` receipt (P-25). If you have to file another - a canary
that sat on a `main` that was not green, say: fix `main`, rebuild the canary, bring its SARIF to `main` and file a new
`sarif` receipt - the course answers `itsmlab labels already revealed` and keeps your labels, which do not change.
That receipt is graded instead of the first when `bakeoff/sarif/` at your submission is exactly what it receipted;
recompute `bakeoff.json` from its files. The grader then reads C from that receipt, while `itsmlab verify 5` reads
the head of `lab5/canary`: after you rebuild the canary, always receipt its SARIF and submit with those files, so
the two are the same commit. An AI reviewer's SARIF counts for Stretch 2 only from the first receipt.
If the course answers `itsmlab labels refused`,
the comment says why - usually a SARIF file changed after download, a missing scanner, or a canary branch that is not
exactly your set - and a refused receipt reveals nothing and costs nothing: fix it and file a new one.

### 5. Write-up, verify, submit

Finish `TRIAGE.md`: the rows for your own findings (the results outside `lab5-canary/` in your receipted SARIF), the
front matter's `sarif_receipt:` (the issue number of the `sarif` receipt whose files are in `bakeoff/sarif/`), and the section `## Bake-off` - at least 600 characters on which of
the detectors you would put in a gate, and why, with your numbers. Then run `./itsmlab.sh verify 5` until it exits 0,
and submit (below).

## Core specs (all must pass; no partial credit inside the bundle)

| spec | what it checks |
|---|---|
| `L5-CORE-1` `compose-up` | your `svcdesk` still builds from your repository and answers `GET /health` |
| `L5-CORE-2` `pipeline` | the skeleton's jobs and actions; `build-test` wired; workflow hygiene; ignores with reasons and expiry; the canary is exactly your set on top of `main`; **`main` green and the canary red** (P-01 to P-08) |
| `L5-CORE-3` `supply-chain` | your image named by digest, public, attested twice, and verified by `gh attestation verify` (Tier B) (P-09, P-10) |
| `L5-CORE-4` `triage` | `TRIAGE.md`'s front matter, table and `## Bake-off`; every ignore and every rule on your own code covered (P-10 to P-13) |
| `L5-CORE-5` `bakeoff` | `bakeoff.py` on the practice set; the canary's SARIF, attested; the labels; `bakeoff.json` consistent with `bakeoff.py`, and with the grader's recomputation (Tier B); the hidden inputs (Tier B) (P-14 to P-28) |

**The differential is the heart of the lab** (2.06, 2.07): the same pipeline, green on `main` and red on `main` plus
your set. A gate that is red everywhere, or green everywhere, proves nothing.

## Stretch (any two of three; each lifts the grade band equally)

| spec | what it is |
|---|---|
| `L5-STRETCH-1` `mutation` | **P-29.** Tests in `mutation/` for the course module `mutation/slaclock.py` that kill at least 30 of the 40 withheld mutants and pass every rewrite. [mutation/README.md](mutation/README.md). |
| `L5-STRETCH-2` `ai-detector` | **P-30.** An AI reviewer as a sixth detector in your bake-off, its findings converted to SARIF with `tools/ai-to-sarif.py` and receipted with the rest. |
| `L5-STRETCH-3` `semgrep-rules` | **P-31.** Two Semgrep rules of your own for your own code, with test cases that prove where each fires and where it must not. |

**Stretch 1.** Coverage is free now, so it is no longer evidence on its own; a mutation score is harder to fake - a
guide, not a guarantee (Lecture 5). `itsmlab mutants 5` runs 12 practice mutants and 2 rewrites in the checker; the
grader runs 40 others and 3 others. Two rules surprise people: a timeout is not a kill (a test that sleeps kills
nothing), and the suite must pass on rewrites of the module that change its text and not its behaviour (a test that
compares the source kills every mutant and fails every rewrite).

**Stretch 2.** The AI reviewer must see the same thing the scanners saw - your canary commit - and its SARIF must be
in `bakeoff/sarif/` **before** your first SARIF receipt, like the others: after the labels are revealed, a new detector
is no longer blind, and one added in a later receipt does not count. The routes: the example workflow [pipeline/.github/workflows/ai-review.yml.example](pipeline/) with
`anthropics/claude-code-action` and your own token, run by hand on `lab5/canary` (it attests its SARIF); or locally,
`claude -p`, Gemini CLI or Ollama on the canary's files with [pipeline/ai-review/PROMPT.md](pipeline/), then
`python3 tools/ai-to-sarif.py ai-findings.json --route local --model <the model you ran> -o
bakeoff/sarif/ai-reviewer.sarif` (`--model` records the model you ran, whatever it calls itself). A small local model
miscounts lines in a diff, and a finding two lines off is an FP (P-20): give it the files with their line numbers
(`grep -n '' lab5-canary/app/*.py`, or `cat -n`) rather than `git diff`. Save the model's
raw answer as `bakeoff/transcript.md` - there, like the SARIF, the gates skip it, because it may quote your set's
credentials. The workflow route needs `ai-review.yml` on `main` **before** `itsmlab canary 5`, and you start it from
branch `lab5/canary` (`gh workflow run ai-review.yml --ref lab5/canary`), so that it reviews C and its attestation
names C.

**Stretch 3.** Start from [semgrep-example/](semgrep-example/README.md): `semgrep/rules.yml` and its test file
`semgrep/rules.py` side by side (Semgrep pairs them by name), `# ruleid:` above a line the rule must report, `# ok:`
above one it must not. "Your own code" is checked: each rule must report at least one location under `src/`.

## AI usage

This is AIAS level 4: you may use AI for anything on the Core path - wiring the pipeline, reading a Trivy report,
writing `bakeoff.py`, drafting `TRIAGE.md` - and disclose it in the headers (below). Two limits. **Claude Pro is never
needed**: nothing on the Core path calls a model, and the Stretch 2 detector can be any assistant, free ones included.
And **your token is yours**: the course never asks for it and never supplies one; `CLAUDE_CODE_OAUTH_TOKEN` is a secret
of your own repository, used by a workflow you start by hand (`workflow_dispatch` only - P-30), so nothing anyone else
does, the course included, spends your subscription. A pull request from a fork never sees your secrets; do not change
that (`pull_request_target` is banned by P-03 for this reason).

An AI reviewer is a detector like the others, and Lecture 5's warning applies to it: a reviewer with high recall and
low precision is an alert-fatigue generator. Your matrix will say which it is on your set.

## Deliverables

At the repository root, on the tag you submit:

| path | what |
|---|---|
| `.github/workflows/ci.yml`, `.github/actions/` | the skeleton, wired (P-01 to P-04) |
| `.trivyignore`, `.gitleaksignore` | ignores with reasons and expiry (P-06) |
| `Dockerfile` | an image that passes the `image` gate |
| `bakeoff.py` | P-23 |
| `bakeoff/sarif/*.sarif`, `bakeoff/labels.json`, `bakeoff.json` | the canary's SARIF as downloaded, your revealed labels, the matrix (P-25 to P-27) |
| `TRIAGE.md` | front matter, the table, `## Bake-off` (P-10 to P-13) |
| `itsmlab.yaml` | `lab: 5` |
| branch `lab5/canary` | kept until your grade arrives (P-07, P-08) |
| `mutation/test_*.py`, `mutation/slaclock.py` | Stretch 1 |
| `bakeoff/sarif/ai-reviewer.sarif`, `bakeoff/transcript.md` | Stretch 2 |
| `semgrep/rules.yml`, `semgrep/rules.py` | Stretch 3 |

Know what you publish. Your repository and your container package are public. An attestation made from a public
repository is signed through Sigstore's public-good instance and written to its transparency log, which is public and
permanent: the certificate names your repository and your workflow. gitleaks runs with `--redact` on the files of the
commit, so its SARIF carries no commit e-mail; Semgrep's SARIF quotes the code it matched.

## When a check fails

| check | the usual cause |
|---|---|
| 2.01 | a job renamed or given a `name:`; a scanner job no longer calling its course action; `ci.yml` limited to some branches |
| 2.02 | the `ITSM-TODO` step still there |
| 2.03 | an action pinned by tag (`@v4`) instead of a commit SHA; `${{ github.event... }}` inside `run:`; no top-level `permissions:` |
| 2.04 | a bare ID; the reason on the same line instead of above it; an expiry more than 90 days ahead, or already passed |
| 2.05 | the canary branch edited, rebased or created from a commit that is not on `main`; `lab5-canary/` committed to `main` |
| 2.06 | `main` was red when you created the canary (a new CVE since your last green run: fix it, recreate the canary); the run of M did not finish |
| 2.07 | a gate that does not look at the set: `lab5-canary` skipped, the canary's CVEs ignored, a secret allow-listed |
| 2.08 | the submitted commit has no finished run, or its `build-test` failed |
| 3.01 | the digest not in lower case, or of another repository; a tag instead of a digest |
| 3.02 | the package is still private |
| 3.03 | the image job ran on a branch, not on `main`; the attestation steps skipped |
| 4.02 | a column missing or renamed; a Decision outside the four; `## Bake-off` too short |
| 4.03 | an ignore without its row; a rule the scanners report on your own code without a row (grader) |
| 5.01 | classes not from the course table; a path compared before the set root is found; FPs counted per result instead of once per identical result; F1 from precision and recall rounded first |
| 5.02 | a SARIF file reformatted, renamed or re-saved by an editor; a scanner missing; SARIF from another run than the canary's |
| 5.03 | labels copied from someone else's issue, or edited |
| 5.04 | `bakeoff.json` computed before the last change to `bakeoff.py` |

## Submission, receipts and attempts

Same path as before; every command runs in your repository root.

1. **Implement**, running `./itsmlab.sh verify 5` as often as you like. Tier A runs are unlimited and never count.
2. **Commit and push**: `git add -A && git commit -m "Lab 5 attempt 1" && git push origin main`.
3. **Wait for the `ci.yml` run of that commit to finish** (2.08 reads it), then **verify the committed tree**:
   `./itsmlab.sh verify 5` exits 0 and its `commit` line does not say `(dirty)`. While a `ci.yml` run that 2.06-2.08
   need is still queued or in progress, those checks are `error` locally, so Core does not pass yet; in `tier-a`,
   which runs beside `ci.yml` on the same push and usually finishes first, they are `skip` - a green `tier-a` with
   those skips has not judged your pipeline. Re-run `tier-a`, or verify locally, once `ci.yml` has finished.
4. **Tag and push the tag**: `git tag -a lab5/v1 -m "Lab 5 attempt 1"` and `git push origin lab5/v1`.
5. **Submission receipt**: `./itsmlab.sh submit 5 --kind submission --tag lab5/v1`. Open the URL, submit the issue.
6. Three attempts. Attempt 1 is due Sunday 15 November 2026, 23:59:59 (Europe/Warsaw); that deadline is advisory - a
   receipt after it is marked `after_attempt1_due` and still counts. Attempts 2 and 3 are the correction window and close
   **Saturday 28 November 2026 at 08:00:00 Europe/Warsaw**, on the morning of session 6; a receipt after that instant is
   `late` and still counts, with 10 % off its points if it arrives before the lecture of session 7 (Saturday 12 December
   2026, 13:30) and 50 % off after that. The best attempt counts, after its penalty.
7. The grade arrives as a comment `itsmlab grade` on the submission's issue. No comment after an hour: ask on the forum
   with the issue number.

A later attempt keeps your bake-off: the SARIF receipt and the labels stay valid for attempts 2 and 3. Fix
`bakeoff.py`, `bakeoff.json` or `TRIAGE.md` and resubmit; never change the files under `bakeoff/sarif/`.

## What the grader does that the checker cannot

It reads GitHub with its own token: the runs of M, of the canary and of your submitted commit (2.06 to 2.08), the
package and its attestations, which it verifies with `gh attestation verify` (3.04), and the attestation of every
SARIF file (5.02). It recomputes your matrix from the receipted SARIF and your revealed labels with its own
implementation of CI-SPEC.md section 3 (5.05), runs your `bakeoff.py` - in a container without network - on labelled
inputs of its own (5.06), and runs your mutation tests against the 40 withheld mutants (Stretch 1). Locally those
checks show as `skip`. Its messages name the rule and the cell, never an expected value, and the run ids it saw stay in
your grade after GitHub deletes the runs.

## The AI-disclosure header

Every file the `ai-disclosure` advisory covers (the end of [CHECKS.md](CHECKS.md)) carries in its first ten lines a
comment matching `ai-generated: <0-100>% - <one line on how>`. For Lab 5 that adds `TRIAGE.md`, `bakeoff.py`,
`mutation/*.py`, `semgrep/rules.yml` and `.github/workflows/ci.yml` to the earlier labs' list:

    # ai-generated: 60% - Claude Code wrote the SARIF parsing, I wrote the matching and the tests   (Python, YAML)
    <!-- ai-generated: 0% - my own triage -->                                                      (Markdown)

In `TRIAGE.md` the front matter comes first: put the header on the line after its closing `---`, as the template does.
SARIF files, `labels.json`, `bakeoff.json` and `bakeoff/transcript.md` are machine output and carry none.

## Style of the written artifacts

`TRIAGE.md` is read by the lecturer (after an AI pre-screen, see the disclosure line above). A good row says what the
finding is, where it is, and what you did - "fixed: base image pinned to the 2026-11-12 digest; 14 of 17 fixed CVEs
gone, the other 3 fixed by `apt-get upgrade`" beats "fixed". A good `## Bake-off` puts numbers next to claims, says
which cells surprised you and why, and keeps Lecture 5's two cautions in view: every reviewer is a detector with a
precision and a recall, and seeded defects flatter every detector.
