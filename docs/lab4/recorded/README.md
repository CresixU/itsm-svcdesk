<!-- ai-generated: 0% - written by the course team -->
# The recorded incident

A complete run of the Lab 4 playground, recorded by the lecturer: the Prometheus snapshot and the P1 ticket of one
incident, worked from the healthy baseline through the page, the acknowledgement and the rollback of the flags to the
recovery - the same injector, the same pager, the same rules of [INCIDENT-SPEC.md](../INCIDENT-SPEC.md). It is a
path through Lab 4 with **the same grade bands** as the live playground, offered up front. It is not a rescue.

## Who should take it

- Your machine has **less than 12 GB of RAM**. The playground and a local model need about 4.5 GB (the pilot
  measured 2.6 GB for the playground's containers alone); Docker itself, your browser and the video call of the
  session need the rest.
- Or you cannot give Docker that much memory on the day, whatever the machine (an employer's laptop, a Windows
  without WSL2).

Decide before the lab, not at minute 60: the recorded path takes the same 150 minutes, spent differently. Download
your recording (below) during the pre-work.

## Where it is

Published separately, not in this folder (it is too large for the course package): the Moodle folder **"Laboratory 4
recordings"** holds three recordings, one subfolder each - `lab4-rec-1`, `lab4-rec-3` and `lab4-rec-4` (there is no
`lab4-rec-2`) - and every subfolder holds the three files of the table below.

**You work one of them: the one your GitHub login assigns.** Students who share a recording share its answer, so the
logins are spread over the three, deterministically: your recording is the (1 + (the SHA-256 of your login, trimmed
and in lower case, read as a number) modulo 3)-th of the list `lab4-rec-1`, `lab4-rec-3`, `lab4-rec-4`. You do not
compute it; the checker prints it, from `login:` in `itsmlab.yaml` (else the owner in `repository:`), or from
`--login`:

    ./itsmlab.sh recording 4                     # Windows: .\itsmlab.ps1 recording 4
    ./itsmlab.sh recording 4 --login <your GitHub login>

It prints `your recording: lab4-rec-N (login ... from ...)` (itsmlab 0.8.6 or newer; `docker pull
ghcr.io/swasik/itsmlab:2026` first). Download that subfolder only. The grader opens the sealed fault in your snapshot,
which names its recording, and compares it with your receipt's login: **a snapshot of another recording fails
L4-CORE-3.02** (INCIDENT-SPEC.md I-32), whatever else is right. `verify 4` cannot read the recording's id (it is
sealed), so it only reminds you which one is yours (the advisory `recording-assignment`). The live path needs no
recording, and I-32 does not apply to it.

| file | what it is | where it goes |
|---|---|---|
| `tsdb-snapshot.tar.gz` | the Prometheus snapshot of the run | `incident/tsdb-snapshot.tar.gz` in your repository |
| `ticket.json` | the incident's P1 ticket, as `svcdesk` answered `GET /tickets/{id}` | `incident/ticket.json` in your repository |
| `transcript-recorded.md` | the recorded investigator's transcript: the path without AI (AI usage in the handout) | stays in the recording's subfolder: the one of your recording is about your incident |

## What you do on it

1. Copy `tsdb-snapshot.tar.gz` and `ticket.json` of **your** recording (`itsmlab recording 4`) into `incident/` of
   your repository, unchanged, and commit them. The grader recomputes the incident from them exactly as it does for a
   live run, and it knows each recording exactly - its run and its sealed fault - so a snapshot changed in any way
   that touches them fails L4-CORE-3.02, and so does another login's recording (I-32). Your grade notes which
   recording you worked.
2. **Alerting** is the same as on the live path: `prometheus/demo-alerts.yml`, `alertmanager/alertmanager.yml` and
   `alertmanager/routing-tests.yml` (I-01 to I-08) are checked on your own files, with the checker's own `promtool`,
   `amtool` and Alertmanager - nothing of the playground is needed. Your rules never ran during the recording, but
   you can evaluate their expressions on it (below) and see when they would have fired, and whether they would have
   stayed quiet on its baseline.
3. **The four timestamps**: `./itsmlab.sh incident 4` (Windows: `.\itsmlab.ps1 incident 4`) prints the recording's
   onset, detection, acknowledgement and recovery, its detecting alert and the three durations. The alert, the page
   and the acknowledgement are the lecturer's; your postmortem declares them as the command prints them, and its
   `ticket` is the recording's ticket id.
4. **The investigation**: you see the incident only through its metrics. There is no flag state to read and no
   trace to open, so you identify the fault from its symptoms, with the table of where each flag shows and which
   services it affects (INCIDENT-SPEC.md section 2.2). That is harder than reading `/flags.json`, and it is the same
   `identified_flags` threshold (I-22).
5. **The AI investigator** works on the served recording (below), with the Gemini or the local path; or, without AI,
   you score `transcript-recorded.md`.
6. **The postmortem and the ledger** are yours. Several students work the same recording and so share its fault;
   what they write about it is each one's own work, and the lecturer sees who worked which recording - and which
   recording each login was assigned.

## Serving it

Prometheus serves the snapshot's blocks from a directory it can write to. From your repository root (Linux, macOS):

    mkdir ~/lab4-recording
    tar -xzf incident/tsdb-snapshot.tar.gz -C ~/lab4-recording
    docker run --rm -d --name lab4-recording -p 19090:9090 --user "$(id -u):$(id -g)" \
      -v "$HOME/lab4-recording:/prometheus" prom/prometheus:v3.15.0 \
      --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus \
      --storage.tsdb.retention.time=100y

Windows PowerShell (Docker Desktop needs no `--user`):

    mkdir $HOME\lab4-recording
    tar -xzf incident\tsdb-snapshot.tar.gz -C $HOME\lab4-recording
    docker run --rm -d --name lab4-recording -p 19090:9090 -v "${HOME}/lab4-recording:/prometheus" `
      prom/prometheus:v3.15.0 --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/prometheus `
      --storage.tsdb.retention.time=100y

The recording is then at http://localhost:19090, and `docker stop lab4-recording` ends it. Why each part:

- **A directory Prometheus can write to.** Prometheus writes a lock file, a write-ahead log and new data of its own
  into its data directory, and does not start on a read-only one: never mount it `:ro`. On Linux the image runs as
  the user `nobody`, who cannot write into a directory you own; `--user "$(id -u):$(id -g)"` runs it as you.
- **Outside your repository.** The directory changes while it is served, and it is not a deliverable: the archive in
  `incident/` is. For a clean copy, delete the directory and extract the archive again.
- **`--storage.tsdb.retention.time=100y`.** Prometheus deletes blocks that are older than its retention (15 days by
  default) than its newest block - and the image's default configuration scrapes Prometheus itself, so within a few
  hours it writes a block of today's data. With a retention of 100 years the recording stays; the checker serves your
  snapshot the same way.
- **Port 19090**, not 9090, so that it never collides with the playground or with your Lab 3 Prometheus.

## "Now" has no data

The recording happened on another day. An instant query without a time is evaluated now, where the recording holds
nothing, and a graph of the last hour is empty. In the Prometheus UI, set the end of the graph (or the evaluation
time of the table) inside the incident; `itsmlab incident 4` gives you the window. Tell the agent the window in UTC,
with the date, and it passes explicit times to the MCP server - every tool of the course's server that evaluates
PromQL takes one. Point it at the recording:

    PROMETHEUS_URL=http://localhost:19090 ~/itsm-agent/bin/python <lab4>/agent/agent.py \
      "Checkout errors paged at 10:44:30Z on 2026-10-24. Investigate 10:30Z to 11:10Z. What is the cause?"

(with the recording's own instants; PowerShell: `$env:PROMETHEUS_URL = "http://localhost:19090"` first). For Gemini
CLI, the same URL goes into `env` of the `prom` server in `.gemini/settings.json`. `<lab4>` is the course package's
`lab4` folder, and `~/itsm-agent` the Python environment of the handout's AI usage section.

## Your own snapshot, served the same way

The same commands serve your own `incident/tsdb-snapshot.tar.gz` after the playground has been stopped: to write the
ledger at home, to run a second investigator for Stretch 1, or to look again at what happened.
