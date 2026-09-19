<!-- ai-generated: 0% - written by the course team -->
# Pre-work: do this before Saturday 19 September 2026

The first session has 150 minutes of lab time and none of it is for installing software. Everything below is done
at home, on your own laptop, before the session. Budget about two hours plus the downloads. Post the output of
step 7 (`itsmlab doctor`) into Moodle by **Thursday 17 September 2026** so that problems can be handled before
Saturday.

## The budget: 60 GB of disk, and what 16 GB of RAM buys

- **Disk: 60 GB free.** The images of the eight labs add up to 40 to 45 GB; 60 GB leaves room for build caches.
  Lab 1 alone needs about 1 GB on disk (about 250 MB of download).
- **RAM.** Docker Desktop with WSL2 costs about 2 GB on its own, and the video call another 2.5 to 3.5 GB. On a
  16 GB laptop the realistic ceiling for containers is about 5 GB. Lab 1 peaks at about 0.4 GB, so it runs
  anywhere; Lab 4 (about 4 GB) is the one to plan for. On Windows, `.wslconfig` (step 1) sets the ceiling.
- **8 GB laptops, or an employer-locked Windows without WSL2**: see "Escape hatch" at the end; Lab 1 works there.

## Checklist and expected downloads

| # | step | download | paste into Moodle |
|---|---|---|---|
| 0 | accounts: GitHub, Docker Hub, Claude Pro (or a free alternative), Google AI Studio | - | - |
| 1 | Docker (Desktop on Windows and macOS, Engine on Linux); `.wslconfig` on Windows | Windows about 605 MB, macOS about 580 MB (Apple Silicon) or 640 MB (Intel), Linux about 100 MB | - |
| 2 | git and uv; on Windows the PowerShell execution policy | git about 70 MB on Windows, uv about 20 MB | - |
| 3 | Claude Code (`claude doctor` clean), or Gemini CLI / GitHub Copilot Free | about 220 MB | - |
| 4 | `docker login` (free Docker Hub account) | - | - |
| 5 | your public repository from the course template; `itsmlab.yaml` filled in | - | the repository URL |
| 6 | pre-pull the images: about 250 MB of download (1 GB on disk) for Lab 1, up to about 5 GB with Labs 2 and 3 | 250 MB now, 5 GB by 10 October | - |
| 7 | `itsmlab doctor` | - | the whole table |
| 8 | a Google AI Studio key (free, no card; needed from Lab 4) | - | - |
| 9 | Ollama: **not now**; before Lab 8 (January) | - | - |

## Step 0 - accounts

- **GitHub** account (free). Your repository is public, so use a login you are comfortable with in public. The
  course collects your GitHub login and repository name in a Moodle form; the submissions bot accepts receipts
  only for the pair on that roster.
- **Docker Hub** account (free, no card): raises anonymous pull limits from 100 to 200 per 6 hours.
- **Claude Pro** (the course assumes every student has it) for Claude Code. Claude Pro is never required for any
  Core step: Gemini CLI (free tier, no card) or GitHub Copilot Free do the same job, and so does writing by hand.
- **Google AI Studio** (free, no card): step 8.

## Step 1 - Docker

### Windows (PowerShell, as your normal user)

Docker Desktop needs WSL2. Install both (accept the administrator prompts), then **restart Windows** before you
start Docker Desktop: WSL2 does not work until the restart.

    wsl --install
    winget install -e --id Docker.DockerDesktop

Or download the installer (about 605 MB): https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

Then raise the WSL2 memory ceiling. On a 16 GB laptop use 8 GB; on 32 GB use 16 GB:

    @"
    [wsl2]
    memory=8GB
    processors=4
    swap=4GB
    "@ | Set-Content -Path "$env:UserProfile\.wslconfig"
    wsl --shutdown

Start Docker Desktop, then check:

    docker --version
    docker info --format "{{.NCPU}} CPUs, {{.MemTotal}} bytes RAM in the Docker VM, {{.Architecture}}"
    (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    (Get-PSDrive C).Free / 1GB

Expected: a version line (`Docker version 29...`), a line with your CPU count and a memory figure close to the
`.wslconfig` value, your total RAM in GB, and at least 60 (GB free).

### macOS

Download Docker Desktop: Apple Silicon (about 580 MB) https://desktop.docker.com/mac/main/arm64/Docker.dmg, Intel
(about 640 MB) https://desktop.docker.com/mac/main/amd64/Docker.dmg. Or with Homebrew: `brew install --cask docker`.
Start Docker Desktop, then:

    docker --version
    docker info --format "{{.NCPU}} CPUs, {{.MemTotal}} bytes RAM in the Docker VM, {{.Architecture}}"
    sysctl -n hw.memsize
    uname -m
    df -h ~

`uname -m` prints `arm64` on Apple Silicon: every course image is multi-arch, nothing else to do.

### Linux

Docker Engine from Docker's repository (packages `docker-ce`, `docker-ce-cli`, `containerd.io`,
`docker-compose-plugin`, about 100 MB): follow https://docs.docker.com/engine/install/ for your distribution.
Then let your user use the socket, and log out and in again:

    sudo usermod -aG docker "$USER"

Check:

    docker --version
    docker compose version
    docker info --format "{{.NCPU}} CPUs, {{.MemTotal}} bytes RAM, {{.Architecture}}"
    free -g
    df -h ~

Expected: `Docker version 29...`, `Docker Compose version v5...` (anything from v2.24.4 works), your CPU count and
RAM, and at least 60 GB free on the filesystem holding your home directory.

## Step 2 - git and uv

uv manages Python and runs spec-kit without installing anything globally.

Windows (PowerShell):

    winget install -e --id Git.Git
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

The last line needs no administrator rights. Windows refuses to run any PowerShell script by default ("running
scripts is disabled on this system"); `RemoteSigned` lets you run the scripts in your own repository: the course
wrapper `.\itsmlab.ps1` and the scripts spec-kit installs in Lab 1. Scripts downloaded from the internet still
need a signature.

macOS:

    xcode-select --install
    curl -LsSf https://astral.sh/uv/install.sh | sh

Linux (Debian/Ubuntu shown; use your package manager):

    sudo apt-get install -y git
    curl -LsSf https://astral.sh/uv/install.sh | sh

Open a new terminal and check `git --version` and `uv --version` (expected: `uv 0.11...` or newer). A terminal
inside VS Code keeps the old `PATH` until you close and reopen VS Code itself.

Configure git once with a name and an e-mail you are comfortable publishing (commits in a public repository are
public):

    git config --global user.name "Your Name"
    git config --global user.email "you@example.com"

## Step 3 - Claude Code, or a free alternative

Native Windows needs no administrator rights, no Node.js and no WSL2. About 220 MB.

Windows (PowerShell):

    irm https://claude.ai/install.ps1 | iex

macOS and Linux:

    curl -fsSL https://claude.ai/install.sh | bash

Then, in a new terminal, `claude` once to log in with your Claude Pro account, and

    claude doctor

Expected: a report with no errors. A Desktop app exists as well (https://claude.ai/download) if you prefer it.

Free alternatives, either of which drives the Lab 1 spec-kit chain equally well:

- **Gemini CLI** (free tier with a Google account, no card): https://github.com/google-gemini/gemini-cli, installed
  with `npm install -g @google/gemini-cli` (needs Node.js 20 or newer) or `brew install gemini-cli`.
- **GitHub Copilot Free**: enable it at https://github.com/settings/copilot; use it in VS Code or through the
  Copilot CLI (https://github.com/github/copilot-cli).

## Step 4 - docker login

    docker login

Enter your Docker Hub login and password (or a personal access token). Expected: `Login Succeeded`.

## Step 5 - your repository from the course template

1. Open [the course template repository](https://github.com/swasik/itsm-2026-template), click **Use this
   template**, **Create a new repository**, owner: you, name: for example `itsm-svcdesk`, visibility:
   **Public**. Or, with the GitHub CLI:

       gh repo create itsm-svcdesk --public --template swasik/itsm-2026-template --clone

2. Clone it (if not cloned above), then edit `itsmlab.yaml`: set `repository: "<your login>/<your repo>"`.
3. On Linux and macOS make sure the wrapper is executable (`chmod +x itsmlab.sh`); commit and push.
4. Later in the course (Lab 5) you will push a container image to GHCR; when you do, set that package's visibility
   to **public** (package page, Package settings, Danger zone). Nothing to do about it now, but note it: every
   attestation check depends on it and it is easy to miss.
5. Post the repository URL in the Moodle form (roster).

## Step 6 - pre-pull the images

Lab 1 (the checker image is published before this pre-work is sent out; its exact figures are on Moodle):

    docker pull python:3.13-slim
    docker pull ghcr.io/swasik/itsmlab:2026

Expected: `python:3.13-slim` is about 46 MB of download and 188 MB on disk (`docker image ls`); the checker image
about 150 MB of download and about 490 MB on disk. Both are multi-arch (amd64 and arm64). Apple Silicon layers are
larger than the amd64 ones quoted here: measured on arm64, `python:3.13-slim` is 215 MB on disk and the checker
image 146 MB of download and 609 MB on disk. Every checker run also leaves the images it built of your own
service on disk (`itsmlab-<hash>-svcdesk`, about 240 MB, 265 MB on arm64;
`./itsmlab.sh verify 1 --prune-images` removes them at the end of a run, and "Troubleshooting" in the course
[README](README.md) shows how to remove them by name later; plain `docker image prune` leaves them, they are
tagged), so budget about 1 GB for Lab 1, or about 1.5 GB on Apple Silicon, plus roughly 0.5 GB of build cache.

Labs 2 and 3 (planned list; the definitive list with exact tags is republished before Lab 3 on 10 October; pull them
by then, not necessarily now): Prometheus 3.14.0 (`prom/prometheus:v3.14.0`, about 110 MB), Grafana 13.2.1
(`grafana/grafana:13.2.1`, about 475 MB), Grafana Alloy 1.19.2 (`grafana/alloy:v1.19.2`, about 210 MB), Toxiproxy
2.12.0 (`ghcr.io/shopify/toxiproxy:2.12.0`, about 8 MB), `oha` 1.16.0 and the course-built `seeded-toxic` image.
Lab 2 adds no images.

## Step 7 - `itsmlab doctor`, and what to paste into Moodle

In your repository directory:

    ./itsmlab.sh doctor            # Linux, macOS
    .\itsmlab.ps1 doctor           # Windows PowerShell (after the execution policy of step 2)

The first run pulls the checker image if step 6 did not. `doctor` prints a table: Docker server version and OS,
CPU count and memory of the Docker host, architecture, free disk on the working directory (warning under 60 GB),
git present, `docker compose version` working, the repository layout (compose file, `DECISIONS.md`, `specs/`,
`src/`, `itsmlab.yaml`), and the checker image you run (`ghcr.io/swasik/itsmlab:2026`, the course tag, is the
expected value; the course updates the image under that tag and you fetch updates with `docker pull`). It exits
0 when nothing is fatal; fatal means no Docker socket or no compose plugin.

**Paste the whole table into the Moodle "pre-work" assignment.** It contains no hostnames, no usernames and no
paths (the free-disk row names no directory). Post it even if it shows warnings; that is the point.

If the wrapper itself fails (no `docker`, permission denied on the socket, PowerShell refusing to run scripts), see
"Troubleshooting" in the course [README](README.md) and paste the error text instead.

## Step 8 - a Google AI Studio key

Create one at https://aistudio.google.com/apikey (free, no card). Store it in a password manager. Needed from
Lab 4 onward by tools that want a raw API key; nothing in Lab 1 uses it. Never commit it.

## Step 9 - Ollama: not now

`ollama pull qwen3:1.7b` and `ollama pull all-minilm:22m` are needed before Lab 8 (16 January 2027). Do not pull
them now; the instructions come with Lab 7.

## Escape hatch: Claude Code on the web

If your laptop cannot run Docker (8 GB of RAM, or an employer-locked Windows without WSL2), Claude Code on the web
(included in Claude Pro) gives an Anthropic-managed Ubuntu VM with about 4 vCPU, 16 GB RAM, 30 GB disk, `docker`
and `docker compose` preinstalled, with no separate compute charge. It covers Lab 1 fully. It shares your account's
usage limits: it solves hardware, not quota. Whether it counts as an equal-credit path for the visual labs later in
the semester is a course decision announced separately; for Lab 1 it is equal.
