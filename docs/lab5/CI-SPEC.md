<!-- ai-generated: 0% - written by the course team -->
# CI-SPEC.md - the rules of Lab 5

**This document is the whole rulebook.** Every rule that decides what "correct" means is here: what your pipeline
must do and must not do, what your ignores must say, how a scanner's SARIF becomes a confusion matrix, what
`bakeoff.py` must print, the order in which things must happen, and every threshold and tolerance. Nothing the
checker does is withheld. What is not published is **the key**: which files of your canary set hold a defect, at
which lines, of which class. The course reveals your part of it after your SARIF receipt, and the grader keeps a few
labelled inputs of its own to run your `bakeoff.py` on. You may be surprised by the data; you will never be
surprised by the rules.

Where this document and an assistant disagree, this document wins. And nothing you write down is believed: the grader
reads your pipeline's runs and attestations from GitHub, recomputes your matrix with its own implementation of
section 3, and runs your `bakeoff.py` itself.

Rule ids (`P-01` .. `P-31`) are stable. The checker's messages and [CHECKS.md](CHECKS.md) cite them.

**Words used below.** *The skeleton* is the pipeline in [pipeline/](pipeline/README.md). *The set* is your canary
set: the files `itsmlab canary 5` writes under `lab5-canary/` on branch `lab5/canary` (section 2). **M** is the
commit of `main` that `lab5/canary` starts from, **C** the canary commit on top of it, **S** the commit you submit.
*The run of a commit* is the run of `.github/workflows/ci.yml` that GitHub started for the push of that commit.
A *finding* or *result* is one entry of a SARIF file's `results`; a *defect* is one entry of a labels file.

---

## 1. The pipeline

| job | runs | fails the build when |
|---|---|---|
| `build-test` | your build and your tests (you wire it: P-02) | your build or your tests fail |
| `deps` | Trivy (dependency files and secrets), Grype, OSV-Scanner, over the whole repository | Trivy finds a HIGH or CRITICAL vulnerability in a dependency file |
| `secrets` | gitleaks over the files of the commit (not the history) | gitleaks finds a secret |
| `code` | Semgrep CE with the registry's `p/default` rules | never |
| `image` | builds your image, Trivy scans it, Syft writes its SBOM; on `main` pushes it to GHCR and attests it | Trivy finds a HIGH or CRITICAL vulnerability **that has a fix** in the image |
| `ignore-policy` | the course's check of `.trivyignore` and `.gitleaksignore` (P-06) | an ignore breaks P-06 |
| `capture` | collects the five SARIF files into the artifact `sarif`; on `lab5/canary` attests them | never |

The scanners run as their official container images, pinned by digest, with `docker run`: no third-party action
touches your repository. Grype, OSV-Scanner and Semgrep only report; the three gates are Trivy twice and gitleaks.
The scanners skip exactly your committed evidence, `bakeoff/sarif/*.sarif` and `bakeoff/transcript.md`: Semgrep copies what
it matched into its SARIF, secrets included, and that evidence must not turn your own `secrets` gate red. The gates
read their configuration from the course's actions only: a `trivy.yaml` in your repository and inline
`gitleaks:allow` comments are ignored, so the one way to silence a gate is P-06's.

| id | rule |
|---|---|
| P-01 | `.github/workflows/ci.yml` runs on `push` of every branch and holds the skeleton's jobs `build-test`, `deps`, `secrets`, `code`, `image`, `ignore-policy`, `capture` - with those ids, no `name:` and no matrix, because the grader reads their conclusions from GitHub by name. The scanner jobs keep using the course's composite actions (`./.github/actions/scan-deps`, `scan-secrets`, `scan-code`), the image job `./.github/actions/image`, the policy job `./.github/actions/ignore-policy`, the capture job `./.github/actions/capture`. You may change what is inside them; the jobs and the SARIF files they produce stay. |
| P-02 | `build-test` builds your `svcdesk` and runs your tests; the placeholder step containing `ITSM-TODO` is gone from every workflow. |
| P-03 | **Workflow hygiene**, in every file under `.github/workflows/` and `.github/actions/`: every `uses:` of an action outside the repository pins a full 40-character commit SHA; no workflow is triggered by `pull_request_target` or `workflow_run`; no `run:` script contains a `${{ }}` expression that reads `github.event`, `github.head_ref` or `inputs` (pass such a value through `env:` and use `"$VAR"`); every workflow sets top-level `permissions:` and none grants `write-all`. |
| P-04 | **The gates.** `deps` fails when Trivy finds a HIGH or CRITICAL vulnerability in the repository's dependency files; `secrets` fails when gitleaks finds a secret in the tree; `image` fails when Trivy finds a HIGH or CRITICAL vulnerability that has a fix in the built image. What P-06 ignores does not count. Grype, OSV-Scanner and Semgrep never fail the build. |
| P-05 | **Green main.** The run of M has `build-test`, `deps`, `secrets`, `image` and `ignore-policy` concluded `success`. |
| P-06 | **Ignores expire and say why.** Every line of `.trivyignore` that is neither empty nor a comment is `<ID> exp:<YYYY-MM-DD>`, with ID a `CVE-YYYY-N...` or a `GHSA-xxxx-xxxx-xxxx`; immediately above it, one or more `#` comment lines whose text totals at least 20 characters - the justification; the date is after the check date and at most 90 days after it; no ID appears twice. Every line of `.gitleaksignore` that is neither empty nor a comment has the same justification above it. The check date is a calendar date in UTC: the UTC day the pipeline runs, the UTC day of your submission receipt for the grader, today's UTC date for the checker (in Poland that is still yesterday until 01:00 in winter and 02:00 in summer). A bare ignore fails `ignore-policy`, and so the build. `.trivyignore.yaml` must not exist (the skeleton passes `--ignorefile .trivyignore`; Trivy's experimental YAML form would bypass the policy). |
| P-07 | **The canary.** Branch `lab5/canary` exists on GitHub; its head C has exactly one parent M; M is on `main` (an ancestor of the commit you submit); C adds exactly the files `itsmlab canary 5` writes for your login under `lab5-canary/`, byte for byte, and changes nothing else. |
| P-08 | **Red canary.** The run of C has `deps` and `secrets` concluded `failure`. With P-05 and P-07 the failure is the set's doing: the same pipeline passed on M, and C differs from M only by the set. That is the proof that your gates are wired, not merely present. |
| P-09 | **Attested image.** On `main` the image job pushes `ghcr.io/<owner>/<repo>` (lower case) and attests it twice, provenance and SBOM. The package is **public** (a new package starts private, and making it public cannot be undone - README step "Make the package public"). For the digest named in `TRIAGE.md`, `gh attestation verify oci://ghcr.io/<owner>/<repo>@sha256:<digest> -R <owner>/<repo> --signer-workflow <owner>/<repo>/.github/workflows/ci.yml --source-ref refs/heads/main` passes, once as it is (the default predicate type is provenance) and once with `--predicate-type https://spdx.dev/Document/v2.3` (the SBOM). |

## 2. The canary set

`itsmlab canary 5`, run on `main` with a clean tree and `main` pushed, creates branch `lab5/canary` locally: one commit
on top of your `main` that adds your set under `lab5-canary/`. It does not switch branches or touch your working tree;
you push it with `git push origin lab5/canary`. The set is chosen for your GitHub login (the `login:` of
`itsmlab.yaml`, else the owner of `origin`) from the course's public pool, the same way every time:

| group | the pool | in your set |
|---|---|---|
| `app/` | 16 small Python modules of service-desk code | 6 |
| `config/` | 7 files, each with a hard-coded credential | 3 |
| `requirements.txt` | 8 dependency pins, each with a HIGH or CRITICAL advisory that has a fix | 2 |
| `README.md` | says whose set it is | 1 |

Some `app/` modules hold a seeded defect and some are **decoys**: code a scanner flags that is not a defect. Every set
holds a pin that trips `deps` and a credential that gitleaks sees, so every set trips both gates. None of the
credentials is real and none of the code ever runs; never merge the branch. `itsmlab canary 5 --print` lists your
set's files without touching git.

**The key is what is withheld**: which files hold defects, where, of which class. It is revealed to you after your SARIF
receipt (P-25). It is not a secret in the strong sense - classmates' revealed labels are public in the submissions
repository - but nothing in your grade depends on how well any detector scores, so knowing labels early gains you
nothing; the order exists so that your measurement is blind, as a fair measurement is.

## 3. The bake-off: from SARIF to a confusion matrix

### 3.1 Labels and results

| id | rule |
|---|---|
| P-14 | **Inputs.** SARIF 2.1.0 files, and a labels file: `{"set": "<root>", "defects": [...]}` where `<root>` is the set's root directory name (`lab5-canary` for your canary, `lab5-practice` for the practice set, anything for the grader's hidden inputs) and every defect is `{"id", "file", "class", "start_line", "end_line"}` or, for a vulnerable dependency, `{"id", "file", "class": "vulnerable-dependency", "package"}`. Ids are unique; `file` starts with `<root>/`; lines are 1-based and inclusive, `start_line <= end_line`; the list may be empty. Other fields (`cwe`, `note`) are informational. The labels are the course's and always have this shape: `bakeoff.py` need not check it, and what it does with any other labels file is not graded. |
| P-15 | **Tools.** Every entry of `runs[]` is a run of the tool named by `tool.driver.name`. Its tool id: `trivy`, `grype`, `osv-scanner`, `gitleaks` for those names; `semgrep` for `Semgrep`, `Semgrep OSS`, `Semgrep CE`, `Semgrep Community Edition`, `Semgrep Pro` and `semgrep`; otherwise the name lower-cased, with every run of characters other than `a-z` and `0-9` replaced by `-` and leading and trailing `-` removed (`ai-reviewer`, `opengrep`); a run without a driver name - `tool`, `tool.driver` or `tool.driver.name` absent, `null` or not of the right type (a name that is a number or an object) - or whose name leaves nothing, is `unknown`. An entry of `runs[]` that is not an object is not a run. Names compare case-insensitively, after surrounding whitespace is removed. Runs with the same tool id are one tool, across files. |
| P-16 | **Results.** Each entry of a run's `results[]` whose `kind` is absent, `null` or exactly `fail` (case-sensitive: `FAIL` and every other value drop the result), and whose `suppressions` is absent, `null` or empty (`[]`, `{}`; `false`, `0` and `""` count as empty too) - a result with any other `suppressions`, even `[null]`, is dropped, whatever the suppression's `status` (simpler than SARIF, which keeps a result whose suppressions were all rejected). Throughout, a member whose value is `null` counts as absent, and an array member that is not an array (`rules`, `results`, `locations`, `tags`) has no entries; an entry of `results[]` that is not an object is ignored. Its location is the `physicalLocation` of the **first** entry of `locations[]`; a result whose first location has no `physicalLocation.artifactLocation.uri` string, or an empty one, is ignored. Later locations are never read. |
| P-17 | **Paths and scope.** A result's path is its `artifactLocation.uri` with `%XX` escapes decoded as UTF-8 (as Python's `urllib.parse.unquote` does: `%2F` becomes a `/` and then separates components, an invalid escape such as `%zz` stays as it is), then a `file://` prefix removed (in any letter case), then one leading `./` removed (once: `././x` keeps `./x`). `uriBaseId` is not resolved, and a backslash is not a separator. It is **in the set** when one of its `/`-separated components equals the set root exactly (case-sensitive); its **file** is then the path from the **last** such component on: `/github/workspace/lab5-canary/app/x.py`, `file:///src/lab5-canary/app/x.py` and `./lab5-canary/app/x.py` are all `lab5-canary/app/x.py` (so the `file://` and `./` steps never change whether a result is in the set or its file; the decoding can). A result outside the set is ignored by the matrix - it is a finding on your own code, and triage material (P-12). |
| P-18 | **Lines.** From `region.startLine` (a JSON integer of at least 1: `7.0`, `"7"` and `true` are not integers) to `region.endLine`; a missing `endLine`, or one that is not an integer, is `startLine` (SARIF 2.1.0 §3.30.7), and an `endLine` below `startLine` is taken as `startLine`. A result without a `region.startLine` of at least 1 has no lines. |

### 3.2 Classes

A defect's `class` is one of ten course classes. A result's classes come from the first of these that gives any:

| id | rule |
|---|---|
| P-19 | A result's **rule** is the **first** entry of the same run's `tool.driver.rules[]` whose `id` equals the result's `ruleId` (`ruleIndex` is never read; no such entry, no rule); its tags are the string entries of `properties.tags`. (a) the result's own `properties.class`, when it is exactly (case-sensitive) the name of a class of the table below; (b) by tool - `gitleaks`: `secret`; `grype` and `osv-scanner`: `vulnerable-dependency`; `trivy`: from its rule's tags, each compared whole and case-insensitively, nothing trimmed - `vulnerability` gives `vulnerable-dependency`, `secret` gives `secret`, `misconfiguration` gives `misconfiguration` (a Trivy result whose rule has none of the three goes on to (c)); (c) every class whose CWE list holds a number `n` written as `CWE-<n>` inside a tag of the result or of its rule, where `CWE` is in any letter case, is not preceded by an ASCII letter or digit (`A-Z`, `a-z`, `0-9`), and `<n>` is the whole run of ASCII digits after the hyphen, leading zeros allowed (`"CWE-89: Improper Neutralization..."` and `external/cwe/cwe-089` give 89; `XCWE-89` and `CWE 89` give nothing); (d) otherwise `other`, which matches no defect. A result may have several classes. |

| class | CWE |
|---|---|
| `secret` | 259, 260, 321, 798 |
| `injection` | 74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336 |
| `deserialization` | 502 |
| `weak-crypto` | 261, 326, 327, 328, 330, 331, 338, 759, 760, 916 |
| `insecure-transport` | 295, 297, 319, 322, 757 |
| `path-traversal` | 22, 23, 35, 36, 73 |
| `ssrf` | 918 |
| `vulnerable-dependency` | 937, 1035, 1104, 1395 |
| `misconfiguration` | 16, 215, 250, 489, 668, 732, 1188 |
| `access-control` | 284, 285, 639, 862, 863 |

Why a course table: only Semgrep writes a CWE into its SARIF, and it writes it into tags; Trivy, Grype, OSV-Scanner
and gitleaks write none. A matching rule that needed a CWE from every scanner could not be applied.

### 3.3 Matching and counting

| id | rule |
|---|---|
| P-20 | **Matching.** A result matches a defect when its file (P-17) equals the defect's `file`, the defect's class is one of the result's classes (P-19), and: for `vulnerable-dependency`, the result's `message.text` names the package - some token of it equals the package name once both are lower-cased and every run of `-`, `_` and `.` is replaced by a single `-` (PEP 503), where a token is a maximal run of the characters `A-Z a-z 0-9 . _ -` with any `.`, `_` and `-` at its two ends removed (so `aiohttp.` at the end of a sentence is `aiohttp`); a result whose `message` has no `text` string (only `id` and `arguments`, or `markdown`) names no package; **lines are not compared** (Grype says line 1 of every dependency file, OSV-Scanner gives no line at all); for every other class, the result has lines and they overlap the defect's: `start <= defect's end_line` and `defect's start_line <= end`. |
| P-21 | **Counting, per tool.** **TP** = the defects matched by at least one of the tool's results in the set; **FN** = the defects matched by none; **FP** = the number of distinct (`ruleId`, file, start line, end line) among the tool's results in the set that match no defect - first drop every result that matches a defect, then count the rest with duplicates once (lines as P-18 gives them: a missing `endLine` and one equal to `startLine` are the same; a result with no lines counts with no start and no end line; a result without a `ruleId` string counts with no rule, which differs from every string, `""` included). Several results on one defect count once; one result may match two defects, and then both are found. A tool whose runs have no result in the set still appears, with TP 0 and FP 0. |
| P-22 | **Scores.** precision = TP / (TP + FP), `null` when TP + FP = 0; recall = TP / (TP + FN), `null` when there are no defects; F1 = 2 TP / (2 TP + FP + FN), `null` when that is 0 / 0. Scores are compared within 0.0005, so four decimals are enough (the course's engine rounds to four); the order of the keys, in `tools` and in each tool's entry, does not matter. There is no true-negative cell: nothing counts the code a tool rightly left alone. |

### 3.4 A worked example (the practice set)

`lab5-practice/` has 9 labelled defects. One result of each scanner, through the rules:

| scanner | the result | P-17 file | P-19 classes | P-20 |
|---|---|---|---|---|
| Trivy | `CVE-2024-23334`, `lab5-practice/requirements.txt` line 1, rule tags `vulnerability, security, HIGH`, message `Package: aiohttp ...` | `lab5-practice/requirements.txt` | `vulnerable-dependency` | token `aiohttp` = defect PD1's package: TP |
| Grype | `GHSA-2g68-c3qc-8985-werkzeug`, `/lab5-practice/requirements.txt` line 1, message `A high vulnerability in python package: werkzeug, ...` | the same file | `vulnerable-dependency` | token `werkzeug` = `Werkzeug` after lower-casing: TP for PD2 |
| OSV-Scanner | `CVE-2026-54279`, `file:///src/lab5-practice/requirements.txt`, no region, message `Package 'aiohttp@3.8.1' is ...` | the same file | `vulnerable-dependency` | tokens `aiohttp`, `3.8.1`, ...: TP for PD1. OSV-Scanner writes almost every result twice; for a match that changes nothing, for an FP it counts once (P-21) |
| gitleaks | `jwt`, `lab5-practice/config/notify.py` line 2 | that file | `secret` | overlaps PC2 (line 2): TP |
| Semgrep | `...insecure-hash-algorithm-sha1`, `lab5-practice/app/portal_users.py` line 7, rule tags `CWE-327: ...` | that file | `weak-crypto` | PA2, a password hash, line 7: TP |
| Semgrep | the same rule on `lab5-practice/app/fingerprint.py` line 7 | that file | `weak-crypto` | no defect there - a fingerprint of an e-mail body is not a security control: FP |

The last two rows are the same rule on the same kind of line. Only the key can tell them apart; that is what a
detector's precision measures. The practice set's `expected.json` is the full matrix.

### 3.5 The protocol

| id | rule |
|---|---|
| P-23 | **`bakeoff.py`** at the repository root: `python3 bakeoff.py --labels <labels.json> <sarif> [<sarif> ...]` prints `{"set", "defects", "tools": {<tool id>: {"tp", "fp", "fn", "precision", "recall", "f1"}}}` on stdout and exits 0 on every input of P-14's shape; `set` is the labels' `set`, `defects` the number of labelled defects, and `tools` has one entry per tool id with a run in the inputs. Python 3.13, **standard library only** (it runs as `python3 -S -E bakeoff.py ...`), at most 60 seconds per call, opening its input files for reading only. |
| P-24 | **Practice.** On the published practice set your `bakeoff.py` prints the published `expected.json`: the same `set`, `defects` and tool ids, TP, FP and FN equal, every score within 0.0005 (and `null` where it is `null`). |
| P-25 | **The order.** Push `lab5/canary`. When its run has finished (red), download its artifact `sarif` into `bakeoff/sarif/` of `main`, unchanged (`gh run download <run id> -n sarif -D bakeoff/sarif`), commit, push, and run `itsmlab submit 5 --kind sarif`. The bot receipts that commit and the sha256 of each SARIF file; within minutes the course posts your labels as a comment on the same issue, first line `itsmlab labels`. Your labels are revealed once, on your first valid `sarif` receipt. A later valid `sarif` receipt (a new canary on a green `main`, say) gets no new labels - your set, and so its labels, never change - but it replaces the first in grading when `bakeoff/sarif/` at your submission is exactly what it receipted: the grade then reads its SARIF, its canary commit and that canary's parent. A submission that carries the first receipt's files is graded against the first. An AI reviewer's SARIF counts for Stretch 2 only from the first receipt (P-30). Save the labels as `bakeoff/labels.json` (`itsmlab labels 5 --issue <n>` does it), unchanged. |
| P-26 | **Authentic SARIF.** Every file under `bakeoff/sarif/` at the receipted commit and at S has the receipted sha256; each has an attestation made by a workflow of your repository whose source commit is C (the `capture` job makes it on `lab5/canary`); the five scanners are all there. C is the canary commit of the graded receipt (P-25). An AI reviewer's SARIF (Stretch 2) needs no attestation on C: it may come unattested from the local route, and one the workflow route attested on the canary of your first receipt stays valid when a later receipt (a new canary) is graded - your set, and so what the reviewer saw, is the same. |
| P-27 | **`bakeoff.json`** at the repository root equals what your `bakeoff.py` prints for `bakeoff/labels.json` and every file of `bakeoff/sarif/`, and equals the grader's own computation under P-14..P-22: the same `set`, `defects` and tool ids, TP, FP and FN equal, the scores within 0.0005. |
| P-28 | **Hidden inputs** (grader only). The grader runs your `bakeoff.py` on labelled inputs of its own, built under the same rules - including another set root. On each, your output must be what the rules give. A mismatch names the rule the input exercises, never the expected value. |

## 4. Triage (`TRIAGE.md`)

| id | rule |
|---|---|
| P-10 | Front matter `lab5_triage:` with `image:` - `ghcr.io/<owner>/<repo>@sha256:<64 hex digits>`, this repository, in lower case - and `sarif_receipt:` - the issue number of the `sarif` receipt whose files are in `bakeoff/sarif/` (P-25; with one receipt, that one). |
| P-11 | A table with the columns `Tool`, `Rule`, `Decision`, `Reason`, in that order; every Decision one of `fix`, `ignore`, `false-positive`, `accept`; every Reason at least 20 characters; at least three rows. A row is one rule of one tool (Tool is the P-15 tool id); it may cover several locations, and the Reason says which. |
| P-12 | **Coverage.** Every ID of `.trivyignore` has a row with Tool `trivy`, that ID as Rule and Decision `ignore`. Every (tool, rule) of the results **outside** `lab5-canary/` in your receipted SARIF - the five scanners' findings on your own service - has a row. |
| P-13 | A section `## Bake-off` of at least 600 characters that reads your matrix: which detector you would put in a gate, and why, with the numbers. (Read by the lecturer.) |

`fix` means you changed the code, the Dockerfile or a pin so that the finding is gone (say where); `ignore` means an
entry of `.trivyignore` or `.gitleaksignore` with its reason and expiry; `false-positive` means the finding is wrong
about your code (say why); `accept` means it is right and you accept the risk for now (say until when and why).

## 5. Stretch (any two of three)

| id | rule |
|---|---|
| P-29 | **Mutation.** `mutation/slaclock.py` is the course module, verbatim (the grader uses its own copy). Your tests are `mutation/test_*.py`, with an optional `mutation/conftest.py`: regular files (no symbolic links), at most 20, each at most 256 KB; pytest and the standard library only. The suite must pass on the module and on each of its behaviour-preserving rewrites, within 60 seconds each; a mutant is **killed** when the suite fails on it (pytest exit code 1) within `min(60, max(10, 5 x T))` seconds, T being your suite's time on the module; **a timeout is not a kill**, and neither is a collection error. Pass: at least **30 of the 40 withheld mutants** killed (grader). `itsmlab mutants 5` runs the 12 published practice mutants and the 2 published rewrites; its threshold is 9 of 12. |
| P-30 | **AI detector.** An AI reviewer's findings on your set, written as the course's JSON (`tools/ai-to-sarif.py --help`) and converted to SARIF with driver name `ai-reviewer`, are in `bakeoff/sarif/` at the SARIF receipt your labels were revealed on - byte for byte the file receipted there, even when a later receipt is graded (P-25) - hence in `bakeoff.json` under `ai-reviewer` (P-27 applies). The model's raw answer is `bakeoff/transcript.md` (at least 200 bytes; the gates skip it, as they skip `bakeoff/sarif/*.sarif`, because it may quote the set's credentials). If a workflow ran it, that workflow is triggered by `workflow_dispatch` only, pins every action by SHA, sets no `allowed_non_write_users`, and its top-level permissions are `contents: read` (a job may add `id-token: write` and `attestations: write`). Any assistant will do: Claude Code (the action, or `claude -p` locally), Gemini CLI, Ollama. |
| P-31 | **Two Semgrep rules of your own.** `semgrep/rules.yml` with at least two rules, and next to it the test file `semgrep/rules.py`, annotated with `# ruleid: <id>` and `# ok: <id>` comments (Semgrep pairs a test file with the config of the same name); `semgrep --test semgrep/` (Semgrep 1.178.0, no network) exits 0; each rule has at least one `ruleid:` and one `ok:` annotation; `semgrep scan --config semgrep/rules.yml src/` reports at least one location in your service's code for each rule (Semgrep names them `semgrep.<id>`). |

## 6. What you add

| path | rules |
|---|---|
| `.github/workflows/ci.yml`, `.github/actions/` | the skeleton, wired: P-01..P-04 |
| `.trivyignore`, `.gitleaksignore` | P-06 |
| `Dockerfile` | whatever makes the `image` gate green - usually a newer base image digest and `apt-get upgrade` |
| branch `lab5/canary` | P-07, P-08 |
| `bakeoff.py` | P-23, P-24, P-28 |
| `bakeoff/sarif/*.sarif`, `bakeoff/labels.json`, `bakeoff.json` | P-25..P-27 |
| `TRIAGE.md` | P-10..P-13; the reasoning artifact of Lab 5 |
| `mutation/`, `bakeoff/transcript.md` + `tools/ai-to-sarif.py`, `semgrep/` | Stretch: P-29..P-31 |
| `itsmlab.yaml` | `lab: 5` |

## 7. Numbers at a glance

| what | value |
|---|---|
| the set | 6 modules of 16, 3 credentials of 7, 2 pins of 8, under `lab5-canary/` |
| gates | Trivy HIGH/CRITICAL in dependency files; gitleaks; Trivy HIGH/CRITICAL with a fix in the image |
| ignore expiry | after the check date, at most 90 days after it; justification at least 20 characters |
| score tolerance | 0.0005 |
| `bakeoff.py` | Python 3.13, standard library, 60 s per call |
| SARIF receipt | 1 to 20 files under `bakeoff/sarif/`, each at most 5 MB, SARIF 2.1.0 |
| `TRIAGE.md` | at least 3 rows, reasons of 20 characters, `## Bake-off` of 600 characters |
| mutation | 30 of 40 withheld mutants killed (practice: 9 of 12); 60 s for the module and each rewrite, `min(60, max(10, 5 x T))` s per mutant; a timeout is not a kill |
| AI transcript | at least 200 bytes |

## 8. What the grader does with all this

It clones your submitted commit and checks P-01..P-03, P-06, P-07, P-10..P-12 on the files; reads the runs of M, C and
S and your attestations from GitHub (P-05, P-08, P-09, P-26) with `gh attestation verify`; recomputes your matrix
from the receipted SARIF and your revealed labels with its own implementation of section 3 (P-27); and runs your
`bakeoff.py` and your mutation tests itself, in a container with no network, on the practice set, on your canary
inputs, on its hidden inputs (P-28) and against the 40 withheld mutants and three rewrites (P-29). It records the run
ids and conclusions it saw in your grade: GitHub deletes workflow runs after the repository's retention period (90
days by default), so your grade keeps its own evidence. Keep branch `lab5/canary` and the package until your grade
arrives.
