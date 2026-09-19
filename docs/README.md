<!-- ai-generated: 0% - written by the course team -->
# ITSM 2026/27 - student package

Everything you need for the pre-work and for Lab 1 of the ITSM course (WSB Merito, 2026/27). The course language
for deliverables and written artifacts is English (a course decision: AI assistance then does the conceptual and
the linguistic work at once, and the human-read rubric takes that into account).

## Szybki start (po polsku)

1. Przed pierwszymi zajęciami (sobota 19 września 2026) wykonaj [PREWORK.md](PREWORK.md): Docker, git, uv, Claude
   Code (albo darmowa alternatywa: Gemini CLI, GitHub Copilot Free), publiczne repozytorium z szablonu kursu,
   pobranie obrazów (ok. 250 MB pobierania i ok. 1 GB na dysku na Lab 1, do ok. 5 GB na Lab 1-3), 60 GB wolnego
   dysku. Wynik polecenia
   `./itsmlab.sh doctor` (Windows: `.\itsmlab.ps1 doctor`, wcześniej jednorazowo
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`) wklej do Moodle do czwartku 17 września.
2. Na zajęciach pracujesz w swoim repozytorium. Jedno polecenie sprawdza wszystko: `./itsmlab.sh verify 1`.
   Kod wyjścia 0 oznacza, że wszystkie specyfikacje Core sprawdzane lokalnie przechodzą; jeden wyjątek:
   L1-CORE-5 (specyfikacja przed kodem) jest lokalnie zawsze pomijana (`skip`) i sprawdza ją dopiero grader na
   podstawie pokwitowań, zob. [sekcję 4.4](#44-reading-the-table) i punkt 4 poniżej. Sprawdzenia są opublikowane
   w [lab1/CHECKS.md](lab1/CHECKS.md); drukuje je też polecenie `./itsmlab.sh checks 1`, które niczego nie
   uruchamia (zob. [sekcję 4.2](#42-itsmlab-checks-the-rules-without-a-run)). Możesz je uruchamiać bez ograniczeń,
   nie liczą się jako próby.
3. Lab 1 ([lab1/HANDOUT.md](lab1/HANDOUT.md)): zbuduj usługę `svcdesk` z dokumentu wymagań, który zawiera trzy pary
   sprzecznych wymagań. Nie ma poprawnego rozwiązania, są tylko obronione: `DECISIONS.md` musi deklarować to, co
   Twoja usługa naprawdę robi, i to uzasadniać.
4. Kolejność: najpierw specyfikacja w `specs/` i pokwitowanie `specs` (`./itsmlab.sh submit 1 --kind specs` i
   formularz w repozytorium `swasik/itsm-2026-submissions`), dopiero potem kod w `src/`. Oddanie: commit i push
   implementacji, `verify 1` na czystym drzewie roboczym, tag `lab1/v1` na tym commicie,
   `./itsmlab.sh submit 1 --kind submission --tag lab1/v1`, formularz (pełna lista kroków: sekcja 5). Pierwsza próba do niedzieli 20 września
   2026, 23:59 (termin orientacyjny: późniejsze pokwitowanie nadal się liczy); próby 2 i 3 (poprawki) do soboty
   26 września 2026, 08:00 (początek następnych zajęć; pokwitowanie po tej chwili jest `late` i nie liczy się).
   Liczy się najlepsza próba. Ocena przychodzi jako komentarz `itsmlab grade` w tym samym issue.
5. Reszta tego pliku i pozostałe dokumenty są po angielsku. Pytania: forum na Moodle, zawsze z id sprawdzenia
   (np. `L1-CORE-2.41`).

## What is in this package

| file | what it is |
|---|---|
| [PREWORK.md](PREWORK.md) | what to install and check before the first session, per operating system, with sizes |
| [lab1/HANDOUT.md](lab1/HANDOUT.md) | the Lab 1 handout: goal, minute budget, the three conflicts, Core and Stretch, AI usage, rules, deliverables |
| [lab1/REQUIREMENTS.md](lab1/REQUIREMENTS.md) | the requirements document R-01 to R-25, as the product owner wrote it |
| [lab1/API.md](lab1/API.md) | the exact HTTP contract the checker enforces, with the SLA test vectors |
| [lab1/CHECKS.md](lab1/CHECKS.md) | every published check, by id, with the expected value; the output of `./itsmlab.sh checks 1 --markdown` |
| [lab1/DECISIONS-template.md](lab1/DECISIONS-template.md) | the skeleton of your reasoning artifact (also in the template repository as `DECISIONS.md`) |
| [template/](template/README.md) | the course template repository: compose file, Dockerfile skeleton, wrappers, config, workflow |

## 1. Pre-work

Follow [PREWORK.md](PREWORK.md). It ends with `itsmlab doctor`, whose output you paste into Moodle. Everything in
Lab 1 assumes the pre-work is done: Docker running, a public repository from the template, the checker image
pulled.

## 2. Your repository

Your repository is created from the course template (PREWORK.md, step 5) and keeps this layout for the whole
semester:

```
docker-compose.yml        the compose contract (API.md section 9): service svcdesk, port 8080, SVCDESK_TEST_CLOCK
Dockerfile                yours (start from Dockerfile.example)
DECISIONS.md              your reasoning artifact (front matter + three sections)
itsmlab.yaml              lab, baselines, repository, submissions_repo, checker_image
itsmlab.sh / itsmlab.ps1  wrappers around the checker container
specs/                    specifications, receipted before any code
src/                      the implementation
.github/workflows/tier-a.yml   runs the checker on every push
.gitattributes            LF line endings everywhere (keep it: without it Windows checkouts look "dirty" to the checker)
```

Fill in `repository:` in `itsmlab.yaml` before your first `submit`. Keep the repository public and free of
personal data (no hostnames, no usernames, no `doctor` output; that goes to Moodle).

## 3. `itsmlab doctor`

    ./itsmlab.sh doctor            # Linux, macOS
    .\itsmlab.ps1 doctor           # Windows PowerShell

Prints a table (Docker version and OS, CPUs, memory, architecture, free disk on the filesystem of your repository
(no path is printed), git, compose, repository layout, the checker image) and exits 0 when nothing is fatal.
Fatal: no Docker socket, no compose plugin. Warnings (less than 60 GB free) do not stop you. The image row is
`OK` for the course tag `ghcr.io/swasik/itsmlab:2026` (the expected value; a digest pinned by hand would warn,
because `docker pull` could never update it). Paste the table into Moodle (PREWORK.md, step 7).

## 4. Running the checker

### 4.1 Wrapper (container mode, the default)

From your repository root:

    ./itsmlab.sh verify 1 --json report.json            # Linux, macOS
    .\itsmlab.ps1 verify 1 --json report.json           # Windows PowerShell

What the wrapper does: `docker run --rm` of the checker image with your directory mounted (Linux and macOS at the
same absolute path, Windows at `/work`) and the Docker socket mounted, passing every argument through. The image
comes from `ITSMLAB_IMAGE` if set, else `checker_image:` in `itsmlab.yaml`, else `ghcr.io/swasik/itsmlab:2026`.

What the checker does: `docker compose --profile tests build` (untimed; every image, the `tests` one included,
is built up front, and a tests image that does not build costs S3, never Core), `docker compose up --wait svcdesk`
under a project name derived from your directory (with the `8080` port publication removed, so a busy port 8080
on your laptop does not matter), waits for `/health` (120 s from `up`), runs the checks of
[lab1/CHECKS.md](lab1/CHECKS.md) including Stretch S3 (`docker compose --profile tests run --rm --build tests`,
300 s cap), then tears everything down (`docker compose down -v --remove-orphans`), always, even on errors. `--keep`
keeps the project running for debugging; `--project NAME` overrides the project name; `--prune-images` also
removes the images compose built for the run (they otherwise stay as `itsmlab-<hash>-svcdesk` and `-tests` in
`docker image ls`, about 240 MB each, so reruns are fast). The checker image builds with BuildKit (it ships
`docker-buildx-plugin`), so a Dockerfile that builds on your laptop builds the same way inside the checker.

Exit codes: `0` every Core spec passes; `1` otherwise; `2` a checker error (no compose file, Docker unreachable,
an unexpected exception with a one-line reason).

`--debug` and `--version` are flags of `itsmlab` itself, not of `verify`, so they come **before** the subcommand:
`./itsmlab.sh --debug verify 1`. Placed after it, argparse rejects them (`unrecognized arguments: --debug`, exit
2). `--debug` writes pytest's own output to stderr; the check table is unchanged, and this is what to attach to a
forum question about a check that behaves in a way you cannot explain. `ITSMLAB_DEBUG` (any non-empty value) does
the same and additionally re-raises an unexpected exception with its traceback, but the wrappers do not forward
environment variables into the container, so in container mode use the flag. `--version` prints the checker
version (`itsmlab 0.2.0`), the same string `report.json` records as `itsmlab_version`; quote it when you report a
problem.

Expected on the unmodified template (no `Dockerfile`, no code yet): the build fails, so L1-CORE-1 fails at 1.03
with the compose error in the message, L1-CORE-2 is reported as `error` (the service never started), L1-CORE-3
fails at 3.03 (the template's `TODO` placeholders are shorter than 20 characters), L1-CORE-4 cannot compare,
L1-CORE-5 is `skip` ("checked by the grader from acceptance receipts"), and the exit code is 1. That is the
starting point; every step of Lab 1 turns one of those rows green.

### 4.2 `itsmlab checks`: the rules without a run

    ./itsmlab.sh checks 1                                # Linux, macOS
    .\itsmlab.ps1 checks 1                               # Windows PowerShell

Prints the published check catalogue of the lab and exits 0. Nothing is built and nothing is started: no compose
project, no service, no HTTP request, not even a look at your files. So it answers on a repository that does not
build yet, and it is the quickest way to find out what a check id in the table actually means. One line per check,
grouped by spec, and the advisory and the bundle rule (section 4.4) at the end:

    Lab 1 published checks (Tier A)

    L1-CORE-1  compose-up  [core]
      L1-CORE-1.01       compose file defines service svcdesk with build
      L1-CORE-1.02       no host-path bind mounts
      ...

    Advisory (reported, not graded):
      ai-disclosure      AI-disclosure header in source and spec files

`--markdown` prints the same catalogue with the full expectation of every check, in the format of
[lab1/CHECKS.md](lab1/CHECKS.md) - that file *is* this output, regenerated from the checker rather than written by
hand. So `./itsmlab.sh checks 1 --markdown` is also how you confirm that the checks in your copy of the package are
the ones your checker image runs, after a `docker pull` of `ghcr.io/swasik/itsmlab:2026` published a fix.

In container mode the wrapper still has to start the checker image, so Docker has to be running; your own stack
does not. Where Docker is not working yet, read [lab1/CHECKS.md](lab1/CHECKS.md) in this package - the same text.

### 4.3 Native mode

The checker is also a Python 3.13 package that runs natively with `uv`: from your repository root,
`uv run --project <path to the checker checkout> itsmlab verify 1`, documented in the checker's own README,
published with its source (link on Moodle). Native mode uses the port your compose file publishes
(`docker compose port svcdesk 8080`), so keep `"8080:8080"` (or any host port) in `docker-compose.yml`. Use it if
the socket mount is blocked on your machine. The container mode above is the supported path; this package does
not document native mode further.

`--base-url URL` skips compose entirely and runs the HTTP checks against a service you started yourself (1.03 and
1.04 only probe `/health`, for 10 s unless `--probe-window SECONDS` says otherwise); the file checks still run on
the current directory. Under `--base-url`, S3 is `skip` when the compose file defines `tests` (the run is not
performed) and `fail` when it does not, unless `--tests-result PATH` supplies the result of a run you performed
yourself: either a JSON object carrying `tests_exit` and `tests_last_line` (the shape the grader captures) or a
plain text log, whose last non-empty line is taken as the tests line and whose exit code is then assumed to be 0.
S3 is then judged on that, by the same rule as a real run. In compose mode the flag is ignored with a note on
stderr, because the `tests` service is run for real. The URL must be
reachable from where the checker runs: from inside the wrapper's container, your laptop's published port is
`http://host.docker.internal:8080` on Docker Desktop (Windows, macOS) and `http://172.17.0.1:8080` (the default
bridge gateway) on Linux:

    docker compose up -d svcdesk
    ./itsmlab.sh verify 1 --base-url http://172.17.0.1:8080

### 4.4 Reading the table

One row per spec: the spec id and name, its status, and for a failing spec the ids of the failing checks with their
messages. Statuses:

| status | meaning |
|---|---|
| `pass` | every check of the spec passed |
| `fail` | at least one check failed; the message says what was expected and what was observed |
| `error` | the check could not run: a fixture call failed (its request and response are in the message), or Docker failed; fix the cause and rerun |
| `skip` | not run here: L1-CORE-5 is always `skip` in Tier A; under `--base-url` S3 is `skip` when the compose file defines `tests` and `fail` when it does not |

Core passes when no Core spec is `fail` or `error` (`skip` is allowed only for L1-CORE-5). Stretch passes at two of
three.

### 4.5 Reading `report.json`

`--json report.json` writes (abbreviated):

```json
{
  "itsmlab_version": "0.2.0", "lab": 1, "mode": "tier-a", "started_at": "...", "finished_at": "...",
  "workdir": "/work", "base_url": "http://svcdesk:8080",
  "repo": {"commit": "<sha or null>", "dirty": true},
  "compose": {"files": ["docker-compose.yml"], "resolved": true},
  "specs": [
    {"id": "L1-CORE-2", "name": "conformance", "bundle": "core", "status": "pass|fail|skip|error",
     "checks": [{"id": "L1-CORE-2.07", "name": "priority matrix (1,1) -> P1", "status": "pass|fail|skip|error",
                 "message": null, "rule": "API.md §3"}]}
  ],
  "observations": {"C1": "wallclock|business|null", "C2": "reopen|immutable|null", "C3": "matrix|vip|null"},
  "advisories": [{"id": "ai-disclosure", "status": "info", "message": "3 of 5 files carry the header", "files_missing": ["src/x.py"]}],
  "summary": {"core": {"passed": 4, "total": 5, "skipped": 1, "pass": true},
              "stretch": {"passed": 1, "total": 3, "required": 2, "pass": false}}
}
```

- `observations` is what the checker saw your service do for C1 (check 2.41), C2 (2.35) and C3 (2.46): these are
  the values `DECISIONS.md` must declare (L1-CORE-4). `null` means the probe could not run.
- `rule` cites the section of [lab1/API.md](lab1/API.md) a check enforces.
- `compose.files` are the compose files the run loaded (your main file and, if present, your
  `*.override.*` file); `resolved: true` means check 1.02 was decided on the effective configuration
  (`docker compose config`), where `.env` values and override files are already applied.
- `advisories` lists files without the AI-disclosure header; reported, not graded.
- `report.json` is in the template's `.gitignore`; do not commit it. In container mode the checker writes it as
  root and then hands it to you (the owner of the directory), so an editor or a native run can overwrite it.

The workflow `tier-a.yml` in your repository runs the same checker on every push, attaches `report.json` as an
artifact and writes a step summary (Core and Stretch totals, one row per spec, the failing checks with messages).

## 5. Receipts: specs, submission, prediction

Grading never trusts git dates: author, committer and tagger dates are all whatever the writer set. The course
issues its own receipts at the moment of acceptance. You obtain one by opening an issue in the public repository
`swasik/itsm-2026-submissions` through its issue form; a workflow runs within a minute, resolves your tag or
commit, computes the content digest, and posts a comment:

```
itsmlab receipt
{"lab": 1, "kind": "submission", "login": "...", "repository": "...", "tag": "lab1/v1", "commit": "...",
 "tree_sha": "...", "archive_sha256": "...", "attempt": 1, "late": false, "after_attempt1_due": false,
 "received_at": "<issue created_at>", "issue": 42, "run_id": 123}
```

and adds the label `receipted`. The issue's creation time and the bot's comment are server-timestamped and not
editable by you. A receipt proves the order of publications; it says nothing about the order of your local work.
The bot accepts an issue only when `repository` matches the one on the roster for your GitHub login (PREWORK.md,
step 5), and only from the form's fields.

`itsmlab submit` never opens the issue for you: it checks what it can locally and prints a prefilled issue-form
URL for you to open, review and submit. Two things must be true before it prints anything: `repository:` in
`itsmlab.yaml` is filled in (the `<owner>/<repo>` placeholder is refused with a message), and the commit it
prefills is already on `origin` (the tag for a submission; `main` for specs and prediction; an unpushed `main`
stops it with `push first: git push origin main`). The bot checks both again and refuses a mismatch, so the
local check saves you a refused issue, nothing more. If you cloned over SSH (`origin` is
`git@github.com:...`), the check reads your public repository over HTTPS instead and says so in a `note:` line:
the checker container has no `ssh` and no keys, and a public repository needs none to be read.

| kind | when | command | what it checks and prefills |
|---|---|---|---|
| `specs` | after pushing your specification to `main`, before any file under `src/` | `./itsmlab.sh submit 1 --kind specs` | uses the current `main` HEAD; the tree has at least one file of 500 bytes or more under `specs/` (other than `.gitkeep` and `README.md`) and no file under `src/` other than `src/README.md`; prefills the commit SHA |
| `submission` | an attempt: the checker exits 0 on a committed, clean tree (or you decide to submit anyway) | commit and push `main`, `git tag -a lab1/v1 -m "Lab 1 attempt 1"`, `git push origin lab1/v1`, then `./itsmlab.sh submit 1 --kind submission --tag lab1/v1` | the tag exists locally and on `origin`; warns when the working tree has uncommitted changes or HEAD is not the tagged commit; prints the commit and the `tree_sha`; prefills lab, kind, repository and tag |
| `prediction` | not used in Lab 1 (a Lab 2 Stretch): binds a text to the current `main` SHA before the work starts | `./itsmlab.sh submit 1 --kind prediction --text "..."` | prefills the SHA and the text |

Steps for an attempt, in your repository root (bash on Linux and macOS; the PowerShell form is given where it
differs):

1. Commit everything that belongs to the attempt and push it: `git status` shows nothing to commit, otherwise
   `git add -A && git commit -m "Lab 1 attempt 1"` (PowerShell: `git add -A; git commit -m "Lab 1 attempt 1"`);
   then `git push origin main`.
2. `./itsmlab.sh verify 1` (`.\itsmlab.ps1 verify 1`) exits 0 on that clean tree. Its `commit` line names the
   commit you are about to tag and must not say `(dirty)`: `(dirty)` means files differ from the commit, so what
   was verified is not what a tag would contain.
3. `git tag -a lab1/v1 -m "Lab 1 attempt 1"` and `git push origin lab1/v1`.
4. `./itsmlab.sh submit 1 --kind submission --tag lab1/v1` (`.\itsmlab.ps1 submit 1 --kind submission --tag
   lab1/v1`). It prints a `warning:` when the working tree has uncommitted changes or when HEAD has moved past
   the tag; if a named file belongs to the attempt, go back to step 1 and use the next tag name. Open the printed
   URL in a browser (you must be logged in to GitHub as the login on the roster); check the fields; **Submit new
   issue**.
5. Within a minute the bot comments with the receipt and labels the issue `receipted`. If it comments with a
   refusal instead (repository not on the roster, tag not found, a fourth attempt), fix the cause and open a new
   issue; a refused issue is not an attempt.

The tag must identify the same committed files that were verified. Tier B clones the tag's commit and grades
exactly those files: an implementation that passed `verify 1` in your working directory but was never
committed is simply absent from the tag (the graded tree then holds `src/README.md` alone), and the attempt
counts. Never move a tag after its receipt: Tier B grades exactly the receipted digest, and if the tag has
moved, the attempt is void and still counts. Use a new tag for every attempt: `lab1/v1`, `lab1/v2`, `lab1/v3`.

## 6. Attempts and deadlines

- **Three Tier B attempts per lab.** Attempt 1 is the submission, due **Sunday 20 September 2026, 23:59:59
  Europe/Warsaw** (the Sunday after the session); that deadline is advisory: a receipt after it carries
  `after_attempt1_due: true` and still counts. Attempts 2 and 3 are the correction window and must be receipted
  **before the next session: the window closes Saturday 26 September 2026 at 08:00:00 Europe/Warsaw**, the start
  of session 2; a receipt after that instant carries `late: true`, is graded, and does not count. The exact
  instants for every lab are in `deadlines.json` of the submissions repository (the same pattern: Sunday
  23:59:59, then the next session's Saturday 08:00:00; Lab 8 closes Saturday 30 January 2027, 08:00:00).
- **The best of the up-to-three attempts counts.** A fourth submission issue is refused. Attempts are counted
  from the labels the bot puts on your receipted issues (`receipted`, `lab:1`, `kind:submission`), never from
  the issue text.
- **How the grade arrives.** Grading runs on GitHub in two stages and takes about 20 minutes. The grader then
  posts a comment `itsmlab grade` on the same issue: the verdict per spec, the notes (why something did not
  count), and two files verbatim, `grade.json` and `grade.json.sigstore`. The grade is signed keylessly with
  Sigstore by the grading workflow itself; to check that it is genuine, save the two blocks as files and run
  (cosign 2.2 or newer: `brew install cosign`, or a release from https://github.com/sigstore/cosign/releases)
  the `cosign verify-blob` command quoted in the comment. No comment after an hour: ask on the forum with the
  issue number.
- **Tier A runs are unlimited and never count.** The checker on your laptop and the workflow in your repository
  are the same image as the grader's; use them as often as you like.
- If a check fails for more than 60 % of the cohort, it is suspended and investigated within 48 hours; the outcome
  is published, and attempts consumed by a defective check are not counted against you. A merged pull request
  that fixes a defective check earns a class-contribution point.

## 7. What is graded

Each lab is 12.5 % of the course:

| component | weight | how |
|---|---|---|
| Core bundle (L1-CORE-1 to L1-CORE-5) | 8 % | pass/fail as a whole: every Core spec must pass; no partial credit inside the bundle |
| Stretch bundle (S1, S2, S3) | 3 % | passes at any two of three; the options are equivalent |
| Reasoning artifact (`DECISIONS.md`) | 1.5 % | read by the lecturer: is the reason sound, is the service owner the right role, is the customer outcome named the one the behaviour actually serves |

Disclosure: reasoning artifacts are pre-screened by an AI model; all grades are assigned by the lecturer. The AI
pass only ranks candidates for the lecturer's attention; the mechanical Tier A and Tier B checks contain no model
at all.

The direction of your decisions is never graded: `wallclock` or `business`, `reopen` or `immutable`, `matrix` or
`vip` score identically. What is graded is that the service does what `DECISIONS.md` says, and that the reasoning
holds. Claude Pro is never on the Core path: every AI step has a free and a no-AI alternative with identical grade
bands. Lab 1 is AI Assessment Scale level 4 (Full AI): use AI for any part, disclose it, own the result.

## 8. The AI-disclosure header

Every file under `src/` and `specs/` with extension `.py .go .ts .js .java .cs .rb .rs .kt .md`, plus
`DECISIONS.md`, carries in its first ten lines a comment matching `ai-generated: <0-100>% - <one line on how>`:

    # ai-generated: 80% - Claude Code drafted, I rewrote the SLA clock
    // ai-generated: 0% - by hand
    <!-- ai-generated: 30% - outline by Gemini CLI, text mine -->

That is exactly the set of files the checker reads; YAML, shell, Dockerfiles and `requirements.txt` are not
checked and need no header. An otherwise empty `__init__.py` needs the one comment line. In `DECISIONS.md`, put
it on the line right after the closing `---` of the front matter, as the template does; the template's line
reads `ai-generated: ??% - TODO ...` and is flagged by the advisory until you replace `??` with a number. The
percentage is your honest estimate; the text after the hyphen says how the AI was used. The checker reports the
files that lack it (advisory `ai-disclosure`); the course rules require it on every checked file, and it is cheap.

## 9. Troubleshooting

**Windows without WSL2.** Docker Desktop needs WSL2 (or Hyper-V on Windows Pro). If your employer blocks WSL2, you
cannot run Docker locally: use Claude Code on the web (PREWORK.md, "Escape hatch"), which has Docker preinstalled,
and push from there. Claude Code itself runs on native Windows without WSL2, but the checker and your service
need Docker.

**PowerShell refuses to run `itsmlab.ps1`** ("running scripts is disabled on this system", the default on
Windows): run once `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (no administrator rights needed;
PREWORK.md step 2), or run a single command as `powershell -ExecutionPolicy Bypass -File .\itsmlab.ps1 verify 1`.

**`itsmlab.ps1: docker was not found`**: Docker Desktop is not installed, or the window was opened before it was.
Finish PREWORK.md step 1 (including the restart), start Docker Desktop, open a new PowerShell window.

**Windows: `verify` says `(dirty)` and `submit` warns about uncommitted changes although `git status` is clean.**
Your repository lacks the template's `.gitattributes` (it was created before the file was added). Git for Windows
checks files out with CRLF line endings, and the checker's git, which runs on Linux inside the container, then sees
every file as changed. Add the file once, in PowerShell in the repository root:

    Set-Content .gitattributes "* text=auto eol=lf"
    git add .gitattributes; git commit -m "Normalise line endings"; git push origin main

**Git Bash on Windows** mangles `/var/run/docker.sock` and `$PWD` into Windows paths. Use PowerShell and
`itsmlab.ps1` on Windows.

**Apple Silicon.** Every course image is multi-arch (amd64 and arm64); `python:3.13-slim` too. If you pick a base
image that has no arm64 build, add `platform: linux/amd64` to the service (it runs emulated, slower) and prefer a
multi-arch base. The grader runs on amd64.

**File names are case-sensitive for the grader** (`DECISIONS.md`, not `decisions.md`; `specs/`, not `Specs/`).
macOS and Windows match names case-insensitively, so a miscased file opens and edits normally there, and the
grader, which runs on Linux and reads the same commit, does not find it at all: L1-CORE-3 fails and the Core
bundle goes with it. The checker holds you to the grader's rule on every platform, so `doctor` and `verify` report
a miscased name rather than accepting it. Rename with git, which records the change on a case-insensitive
filesystem too: `git mv -f decisions.md DECISIONS.md`.

**Port 8080 busy.** In container mode the checker removes the port publication, so a busy 8080 does not affect
`verify`. It affects your own `docker compose up` and native mode: find the process (`lsof -i :8080` on macOS and
Linux, `netstat -ano | findstr :8080` on Windows) or change the host side of the mapping to
`"18080:8080"`. The container side must stay 8080.

**"fatal: detected dubious ownership in repository"** from git inside the checker. The current image marks every
directory safe; if you see this, you have an old image: `docker pull ghcr.io/swasik/itsmlab:2026` and rerun.
Natively: `git config --global --add safe.directory "$PWD"`.

**Docker socket.** `permission denied while trying to connect to the Docker daemon socket` on Linux: add yourself
to the `docker` group (`sudo usermod -aG docker "$USER"`, log out and in). `Cannot connect to the Docker daemon`:
Docker Desktop is not running, or (Linux) the daemon is stopped (`sudo systemctl start docker`). Rootless Docker,
Colima or OrbStack put the socket elsewhere: the Linux and macOS wrapper follows `DOCKER_HOST` when it is a
`unix://` URL; set it (`export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock` for rootless Docker) and rerun.
On Docker Desktop for macOS there is normally no `/var/run/docker.sock` on the Mac itself (the CLI uses
`~/.docker/run/docker.sock` through the `desktop-linux` context); that is expected and the wrapper still works,
because the bind mount resolves inside Docker Desktop's own VM, where the socket does exist.

**`./itsmlab.sh: Permission denied`**: `chmod +x itsmlab.sh` and commit the mode.

**Check 1.01 fails: "no `build:` key".** `svcdesk` names an `image:` but does not build. The Core bundle is
earned by the code in your repository, so the service must be built from it: `build: .` (the Dockerfile may
start `FROM` any public base image).

**Check 1.02 fails: "bind mount".** The checker runs `docker compose` from inside a container, where your host
paths do not exist, so `./data:/data` cannot work. Replace it with a named volume (the template's `svcdesk-data`)
and `COPY` your code into the image instead of mounting it. The check reads the resolved configuration, so a
bind mount in `docker-compose.override.yml`, behind a `.env` variable or as a named volume with `driver_opts`
(`type: none`, `o: bind`) is found too.

**Check 1.03 fails: the build or the start failed.** The message carries the compose error. Common causes:
no `Dockerfile` (copy `Dockerfile.example`), no `requirements.txt`, a `CMD` module path that does not match your
layout, or a service that fetches something at start (the grader's sandbox has no network after the build).
Run `docker compose build && docker compose up svcdesk` yourself and read the log. If the message says
`requires BuildKit` (`RUN --mount=...`, `RUN <<EOF`, a `# syntax=` line) while the build works on your laptop, you
are running an old checker image without the buildx plugin: `docker pull ghcr.io/swasik/itsmlab:2026` and rerun;
the current image builds with BuildKit exactly as your laptop does.

**`report.json` belongs to root** (Linux, after a container-mode run with an old checker image): the current
image hands the file to you at the end of the run; with an old one, `rm -f report.json` before a native run or
before opening it in an editor, or pull the current image. A native run that cannot write the file says so at
the start (exit 2), not after the checks.

**Disk fills up with images.** Every checker project leaves its built images behind (`itsmlab-<hash>-svcdesk`,
`itsmlab-<hash>-tests`, about 240 MB each); `docker compose down -v` removes containers, networks and volumes,
never images. Run `./itsmlab.sh verify 1 --prune-images` (removes the images of that run at its end), or remove
every course-built image by name:

    docker image ls --format '{{.Repository}}:{{.Tag}}' 'itsmlab-*' | xargs -r docker image rm                       # bash
    docker image ls --format '{{.Repository}}:{{.Tag}}' 'itsmlab-*' | ForEach-Object { docker image rm $_ }          # PowerShell

The names (`repository:tag`) matter: `docker image rm <id>` refuses an id that carries more than one name
(`image is referenced in multiple repositories`, for example after a `docker tag` of your own), while removing
by name untags each one in every case. (Compose stamps every image it builds with its service name, so the
checker's `svcdesk` and `tests` images have distinct ids even when they share all their layers.) With nothing
to remove the bash line does nothing (`xargs -r`). Plain `docker image prune` does not reclaim them: it removes
only dangling (untagged) images, and
these are tagged. `docker image prune -a` would remove them, but also every other image no container uses,
including the ones you pre-pulled for later labs.

**Check 1.04 or 2.01 fails but the service runs on your laptop.** The service must listen on `0.0.0.0:8080` inside
the container, not on `127.0.0.1`.

**L1-CORE-4 fails.** `DECISIONS.md` declares one value and the service does another. The report's `observations`
show what the checker saw; either fix the service or fix the declaration, then rerun.

**Docker Hub pull rate limit** (`toomanyrequests`): `docker login` (PREWORK.md, step 4).

**Claude Code on the web shares quota.** It draws on the same Claude Pro limits as Claude Code on your laptop. If
`/usage` shows you are low, switch to Gemini CLI or Copilot Free for the session; quota is never a reason for a
deadline extension.

**`docker pull ghcr.io/swasik/itsmlab:2026` is denied.** The image is public and an anonymous pull was verified
on Linux and macOS. Run `docker logout ghcr.io`, retry the pull, and check that the package name is exact. If it
still fails, paste the complete error on the forum.

## Open questions (being finalised before term)

- The URL of the checker's source for optional native mode will be published with the Moodle package. The
  supported container path needs no source checkout. The student template is already public at
  `https://github.com/swasik/itsm-2026-template`.
- The design document names GitHub spec-kit v1.0.0 with commands written `/speckit.constitution`; the version
  verified for this package (v1.0.6, September 2026) takes `--integration` rather than `--ai` and installs,
  for Claude Code and Copilot, skills named with a hyphen (`/speckit-constitution`), while its Gemini CLI
  integration installs `.gemini/commands/speckit.*.toml`, so there the dotted names stay
  (`/speckit.constitution`). The handout follows the verified version and gives both spellings.
- The list of Lab 2 and Lab 3 images in PREWORK.md step 6 is planned, not final; the exact tags are republished
  before Lab 3.
- The checker image is published for amd64 and arm64. The measured compressed layers are about 150 MB on amd64
  and 146 MB on arm64; PREWORK.md gives the measured disk sizes. Students use the moving `:2026` tag, while
  the grader pins the published digest.
- The template's compose file ships the `tests` service commented out (as the course design decides): an
  uncommented stub with no runner would fail S3 with a build or run error instead of the clear "defines no
  service `tests`", and S3 is a Stretch option. Uncomment it when you write the tests.
- When the course publishes a fixed checker (the fairness valve), it goes out under the same tag
  `ghcr.io/swasik/itsmlab:2026`: you run `docker pull ghcr.io/swasik/itsmlab:2026` and nothing in your repository
  changes (your `tier-a.yml` runs pull the tag fresh on every push). Only the grader pins a digest, and every
  grade records the one that produced it.
- How the roster (GitHub login to repository) is collected: this package assumes a Moodle form.
- The correction window closes at the start of the next session, Saturday 26 September 2026, 08:00:00
  Europe/Warsaw (`deadlines.json` in the submissions repository); the hour is confirmed with the timetable.
- `lab1/CHECKS.md` is the output of `itsmlab checks 1 --markdown` (regenerated at integration and diffed against
  the hand-written draft: every id and expectation agreed); when a check changes, regenerate the file from the
  checker rather than editing it.
