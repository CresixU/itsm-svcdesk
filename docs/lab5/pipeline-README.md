<!-- ai-generated: 0% - written by the course team -->
# The Lab 5 pipeline skeleton

This directory is the pipeline you copy into your repository in Lab 5: five scanners in three jobs, an image job
that scans your container image, builds an SBOM and attests both, a policy check on ignores, and a capture job that
bundles the scanners' SARIF. The rules it implements are in `CI-SPEC.md` (P-01 to P-09); this file says what each
piece is, where it goes and what you wire.

## What is here, and where it goes

Copy every path to the same path in your repository (the root of your repository, next to `docker-compose.yml`).

| path | what it is |
|---|---|
| `.github/workflows/ci.yml` | the pipeline: jobs `build-test`, `deps`, `secrets`, `code`, `image`, `ignore-policy`, `capture` (P-01) |
| `.github/actions/scan-deps/action.yml`, `trivy.yaml` | Trivy fs, Grype, OSV-Scanner: `trivy.sarif`, `grype.sarif`, `osv-scanner.sarif`; gate on Trivy HIGH/CRITICAL |
| `.github/actions/scan-secrets/action.yml`, `gitleaks.toml` | gitleaks in `dir` mode: `gitleaks.sarif`; gate on any secret |
| `.github/actions/scan-code/action.yml` | Semgrep with the registry's `p/default`: `semgrep.sarif`; never fails |
| `.github/actions/image/action.yml`, `trivy.yaml` | `docker build`, the Trivy image gate, a Syft SBOM; on `main`: push to GHCR, attest provenance and SBOM |
| `.github/actions/ignore-policy/action.yml`, `ignore_policy.py` | the P-06 check of `.trivyignore` and `.gitleaksignore` (standard-library Python) |
| `.github/actions/capture/action.yml` | the five SARIF files as artifact `sarif`, attested on `lab5/canary`, uploaded to code scanning |
| `.trivyignore`, `.gitleaksignore` | empty apart from a header that states the policy (P-06) |
| `.github/workflows/tier-a.yml`, `itsmlab.sh`, `itsmlab.ps1` | **replace your copies**: they now hand the checker a GitHub token (the Lab 5 checks read your runs and attestations from the GitHub API, which rate-limits anonymous calls); `tier-a.yml` also checks out every branch with its history and tells the checker it runs in GitHub Actions (a `ci.yml` run still in progress is then `skip` there, `error` locally) |
| `.github/workflows/ai-review.yml.example` | Stretch 2 only: the AI reviewer as a workflow you start by hand on `lab5/canary` (P-30); rename to `.yml` |
| `ai-review/PROMPT.md` | Stretch 2: the review prompt and the JSON answer shape |
| `tools/ai-to-sarif.py` | Stretch 2: the AI reviewer's JSON answer to SARIF with driver `ai-reviewer` (`--help` shows the shape) |

## What you wire

1. **`build-test`**: `ci.yml` ships with one placeholder step marked `ITSM-TODO` that fails on purpose. Replace the
   whole step with your build and your tests, for example
   `docker compose build svcdesk tests` then `docker compose --profile tests run --rm tests`. No `ITSM-TODO` may
   remain anywhere under `.github/` (P-02).
2. **The image job's inputs**, only if your `Dockerfile` is not at the repository root: set `context:` and
   `dockerfile:` in the `image` job of `ci.yml`.
3. **Push and read the first red run.** Expect `build-test` green once wired, `image` red on the base image's
   fixable CVEs: that is the triage (a newer base digest, `apt-get upgrade`, and for what no upgrade fixes an entry in
   `.trivyignore` with a reason above it and an expiry within 90 days).
4. **Make the package public, once.** The first green run on `main` pushes `ghcr.io/<owner>/<repo>` (lower case),
   and GHCR creates the package **private**. On GitHub: your profile, **Packages**, the package, **Package
   settings**, **Danger Zone**, **Change visibility**, **Public**. This cannot be undone (a public package stays
   public); do it after the first push, the grader reads the package anonymously (P-09).
5. **Stretch 2 only, before the canary**: if you will use the workflow route, commit `ai-review.yml` (renamed from
   the example), `ai-review/PROMPT.md` and `tools/ai-to-sarif.py` to `main` **before** `itsmlab canary 5`. The
   workflow runs on the canary commit C (start it with "Use workflow from: `lab5/canary`", or
   `gh workflow run ai-review.yml --ref lab5/canary`), so C must already carry it; the canary branch may not change
   anything else (P-07).

**Findings every image meets.** After `apt-get upgrade`, the gate still reports fixable HIGH findings that sit inside
pip itself: pip vendors other packages in `pip/_vendor` at old versions (`msgpack`, `setuptools`' `pkg_resources`
and `urllib3` at the time of writing, four IDs; Trivy reads them from pip's own bill of materials), and even the newest
pip release ships them. There are two honest options. The simplest is a runtime image without pip: end the
`RUN pip install ...` line of your `Dockerfile` with `&& pip uninstall -y pip` (pip only installs; svcdesk never calls
it at run time), or use a multi-stage `Dockerfile` that copies only the installed packages into the final stage. The
other is one `.trivyignore` entry per ID, each with its reason and an expiry (as the course's reference does), and a
new entry whenever the Trivy database names another vendored package.

## What you never change

- The seven job ids, and no `name:` and no `strategy.matrix` on those jobs: the checks read job results from the
  GitHub API, which reports a job by its name.
- Each job's `uses: ./.github/actions/<name>` step (P-01). What runs inside an action is yours to change.
- The SARIF file names: `trivy.sarif`, `grype.sarif`, `osv-scanner.sarif`, `gitleaks.sarif`, `semgrep.sarif`, and
  the artifact name `sarif` with the five files at its root: `gh run download <run id> -n sarif -D bakeoff/sarif`
  gives `bakeoff/sarif/trivy.sarif` and so on (P-25).
- `on: push` for every branch (no branch or path filter: the canary branch `lab5/canary` must run too).
- The pins: each scanner image by tag and digest (the inputs of its action; Trivy's in `scan-deps` and `image` are
  the same), each action by full commit SHA. Workflow hygiene (P-03) checks every file under `.github/`.

Trivy, gitleaks and Semgrep skip exactly `bakeoff/sarif/*.sarif` and `bakeoff/transcript.md`: the evidence you
commit there quotes the canary's secrets, and `main`'s own gates must not trip on it. Ignores go to `.trivyignore` and
`.gitleaksignore` only, where P-06 asks for a reason and an expiry: Trivy runs with the action's own empty
`trivy.yaml`, so a `trivy.yaml` in your repository does not change the gates, and gitleaks runs with
`--ignore-gitleaks-allow`, so an inline `gitleaks:allow` comment hides nothing.

## Artifacts of a run

| artifact | from | contents |
|---|---|---|
| `sarif-deps`, `sarif-secrets`, `sarif-code` | the three scanner jobs | their SARIF, uploaded before the gate runs |
| `sarif` | `capture` | the five files together; on `lab5/canary` each is attested (P-26) |
| `sbom` | `image` | `sbom.spdx.json` (SPDX 2.3), the SBOM that `main` attests |
| `ai-sarif` | `ai-review` (Stretch 2) | `ai-reviewer.sarif`, `ai-findings.json`, `bakeoff/transcript.md` |
