<!-- ai-generated: 0% - written by the course team -->
# Lab 4 - On-call simulation, and scoring the AI investigator against ground truth

Saturday 24 October 2026, 150 minutes, fully online. AI Assessment Scale level 3 (AI Collaboration). Peak container
RAM about 4.5 GB: the heaviest lab of the course.

Disclosure: reasoning artifacts are pre-screened by an AI model; all grades are assigned by the lecturer.

**Two paths, the same grade bands.** The live path runs the whole OpenTelemetry Demo on your laptop and needs about
12 GB of RAM or more. The recorded path works a complete incident the lecturer recorded on the same playground - its
snapshot and its ticket - with everything else exactly as below: [recorded/README.md](recorded/README.md). There are
three recordings, `lab4-rec-1`, `lab4-rec-3` and `lab4-rec-4` (Moodle folder "Laboratory 4 recordings"), and you work
the one your GitHub login assigns: `./itsmlab.sh recording 4` (Windows: `.\itsmlab.ps1 recording 4`) prints it, and a
snapshot of another recording fails L4-CORE-3.02 (I-32). **If your machine has less than 12 GB of RAM, take the recorded path,
and decide before the lab.** It is a path, not a rescue.

## Goal

You are on call for a web shop: the OpenTelemetry Demo, some fifteen services and a load generator, with your own
`svcdesk` beside it as the ticketing system of record. Write symptom alerts for the shop, and a routing tree that
sends P1 to the pager and P2 and P3 to chat, with an inhibition you prove on a running Alertmanager. Let the healthy
shop run a ten-minute baseline with your pages quiet. Then arm the course's fault injector and wait. Two to six
minutes later, at a moment you do not know, three feature flags start failing - one from each of three classes. You
are paged. Open a P1 ticket in your `svcdesk`, acknowledge it, find what changed, and restore the service by
switching the flags off. Then let an AI agent investigate the same incident through the course's Prometheus MCP
server, and grade it: every hypothesis it states becomes a ledger entry with a PromQL prediction and one of four
verdicts. **The deliverable is a scorecard, not a working agent.**

Nothing you write down is believed. From the two artifacts you ship - your Prometheus snapshot and your ticket - the
grader recomputes the four timestamps and the three durations your postmortem declares, re-runs every prediction of
your ledger at the instant you name and on the healthy baseline, and opens the fault the injector sealed into your
snapshot to check which flags you identified and which services your correct verdicts blame. The fault is drawn at
random when you arm: a classmate's answers belong to another fault, and so do your own from a rehearsal.

Read, in this order: [INCIDENT-SPEC.md](INCIDENT-SPEC.md) (the whole rulebook, I-01 to I-32),
[CHECKS.md](CHECKS.md) (every check the checker runs), [playground/README.md](playground/README.md) (the commands of
the playground), and the templates listed in [README.md](README.md). `./itsmlab.sh checks 4` (Windows:
`.\itsmlab.ps1 checks 4`) prints the same catalogue from the checker itself; it runs nothing, so it is safe at any
point in the lab. The course [README](../README.md) explains the checker, the receipts and the deadlines.

## Before the lab

Do this at home, in the week before 24 October; none of it fits into the 150 minutes. `<lab4>` below is the path of
this folder.

1. **The playground.** Follow "Once, before the lab" in [playground/README.md](playground/README.md): clone the demo
   at its tag 3.1.0, copy `playground/` into it as `itsm/`, append the lines it lists to the demo's `.env.override`
   (among them `DEMO_VERSION=3.1.0` and the absolute path of your repository), and pull the images with the plain
   `pull` it shows: about **3.6 GB** of download (3.3 GB on Apple Silicon). The demo wants **14 GB** of free disk.
2. **A trial start.** Copy `demo-alerts-template.yml` to `prometheus/demo-alerts.yml` and `alertmanager-template.yml`
   to `alertmanager/alertmanager.yml` in your repository (the playground's Alertmanager does not start without its
   file), start the playground once with the two commands of "Start, and start over" (`build svcdesk` builds your
   service, then `up -d` starts the rest; never `up -d --build`, which compiles the whole demo from source), open the
   shop at http://localhost:8080 and your service at http://localhost:18080/health, and stop it with `down -v`. A
   trial run is never graded: the graded run is the one whose snapshot you commit, and every run draws a new fault.
3. **Memory.** Plan for about 4.5 GB: the pilot measured 2.6 GB for the playground's containers, and a local model
   adds about 2 GB while it answers. On Windows, the WSL2 ceiling of `.wslconfig` must allow it (PREWORK step 1:
   `memory=8GB` on a 16 GB laptop). With less than 12 GB of RAM, take the recorded path and download your recording
   now (`./itsmlab.sh recording 4` names it; [recorded/README.md](recorded/README.md)).
4. **The AI investigator** - one of these (see AI usage below):
   - **Gemini**: an API key from Google AI Studio (PREWORK step 8; free, no card). For Gemini CLI also
     `npm i -g @google/gemini-cli@0.61.0` (Node.js 20 or newer).
   - **Local**: Ollama, and `ollama pull qwen3:1.7b` (1.4 GB; PREWORK step 9). Install Ollama natively if you can:
     its Docker image is 9.3 GB on disk.
   - Both need the course's MCP server and agent loop, which need Python 3.10 or newer and two pinned packages.
     With uv (PREWORK step 2):

         uv venv --python 3.12 ~/itsm-agent
         uv pip install --python ~/itsm-agent -r <lab4>/agent/requirements.txt

     (Windows PowerShell: `$HOME\itsm-agent` in place of `~/itsm-agent`.)
   - **No AI**: nothing to install.

## If you have not finished Lab 3

Lab 4 needs two things from Lab 3. Your `prometheus/alerts.yml` must still load, and each of its alerting rules must
carry `severity` P1, P2 or P3 (I-03, which Lab 3's M-17 already asked for): `svcdesk`'s alerts join the routing tree.
And your `svcdesk` must expose Lab 3's histogram on `/metrics` - `http_server_request_duration_seconds` with route
templates and status codes (M-03 to M-05) - because the acknowledgement is checked in it (I-16). Neither needs your
Lab 3 buckets, SLO or dashboard to be right. On the recorded path, I-16 reads the recording's `svcdesk`, so only
`alerts.yml` matters.

Lab 3's correction window closes on Saturday 24 October 2026 at 08:00:00 Europe/Warsaw, on the morning of this session.
Whether a `checkpoint/lab-3` tag is published at that moment is announced on Moodle; do not plan on it. If it is,
the announcement carries the commands to adopt it, and you declare `baselines: {lab3: checkpoint}` in
`itsmlab.yaml`. Otherwise declare `baselines: {lab3: student}` and bring the two things above into your own service.

## Before you start

1. Pull the current checker image and check its version:

       docker pull ghcr.io/swasik/itsmlab:2026
       ./itsmlab.sh --version                  # Linux, macOS
       .\itsmlab.ps1 --version                 # Windows PowerShell

   It must print `itsmlab 0.8.6` or newer (the image published on 12 October 2026): before 0.8.6 there is no `itsmlab recording 4`, the
   command that names your recording on the recorded path; before 0.8.2 a miscased file
   (`Alertmanager.yml`) could pass on macOS and fail for the grader, and before 0.8.0 the image does not know Lab 4 and
   carries neither Alertmanager nor `amtool`.

2. In `itsmlab.yaml`, set `lab: 4` and your `baselines:` (above).

3. **Free the playground's ports.** Stop your own stack in your repository (`docker compose --profile observability
   down`): your Lab 3 Prometheus holds port 9090 and your `svcdesk` port 8080, which the playground's Prometheus and
   the shop need. If your `docker-compose.yml` gives `svcdesk` a fixed `container_name: svcdesk`, delete that line:
   the playground's `svcdesk` has that name, and `itsmlab verify 4` starts yours next to it.

4. **The templates** go into your repository before the first start: the table in [README.md](README.md) says where.

## Minute budget

Core items sum to 110 minutes; the remaining 40 are slack. If an item overruns by more than its budget, stop, run
the checker, and ask on the forum with the check id. The injector's ten-minute baseline starts with the playground
and runs while you write your rules: item 2 is the baseline.

| # | Core item | minutes | at |
|---|---|---|---|
| 1 | Start the playground (images pre-pulled); open the shop, Grafana, the pager, `svcdesk` | 15 | 15 |
| 2 | `demo-alerts.yml`, `alertmanager.yml`, `routing-tests.yml`; `./itsmlab.sh verify 4` for L4-CORE-2 - the baseline runs meanwhile | 20 | 35 |
| 3 | Arm; paged; P1 ticket; acknowledge; investigate; revert the flags; recovery | 25 | 60 |
| 4 | The AI investigator: transcript and ledger | 15 | 75 |
| 5 | `./itsmlab.sh snapshot 4 --ticket <id>`, `./itsmlab.sh incident 4`, commit | 5 | 80 |
| 6 | The postmortem | 20 | 100 |
| 7 | `./itsmlab.sh verify 4`, fix, submit | 10 | 110 |
| | slack | 40 | 150 |

Item 3 runs on the incident's clock, not yours: the onset comes 2 to 6 minutes after you arm, and a detecting alert on
the shop's symptoms resolves some minutes after the last flag goes off, when its 5-minute window has slid past the
fault. That is what the slack is for. On the recorded path, items 1 and 3 become serving the recording and
investigating it.

## The incident, step by step

Every command runs in your repository root, except the playground's `docker compose` commands, which run in the
`opentelemetry-demo` directory. Windows: `curl.exe` for `curl`, `.\itsmlab.ps1` for `./itsmlab.sh`.

1. **Start the playground** with the two commands of [playground/README.md](playground/README.md) ("Start, and start
   over"): `build svcdesk`, then `up -d`. Open the shop (http://localhost:8080), Grafana
   (http://localhost:8080/grafana), the pager (http://localhost:18091), your `svcdesk`
   (http://localhost:18080/health) and the injector's status (http://localhost:18090/status). From now on the
   injector counts its baseline.

2. **Rules and routes.** Write `prometheus/demo-alerts.yml`, `alertmanager/alertmanager.yml` and
   `alertmanager/routing-tests.yml` from the templates, then reload both servers:

       curl -X POST http://localhost:9090/-/reload
       curl -X POST http://localhost:9093/-/reload

   A reload answers with an error when a file does not load, and Prometheus keeps the rules it had: check first
   (below). http://localhost:9090/alerts lists your rules and their state. The fault is one flag from each class of
   INCIDENT-SPEC.md section 2.2 - errors, latency and load, resources - and I-17 needs a page: at least one of your
   P1 alerts must fire after the onset. Page on what the shop's users would feel (Lecture 4 slide 7), and keep every
   rule quiet on the healthy shop. Every fault the injector draws makes checkout fail or slow down, so a P1 on
   checkout's errors and another on its latency page on every draw; a P1 on errors alone misses the draws whose only
   checkout symptom is latency. Check the files in a second each, without the checker:

       docker run --rm -v "$PWD/prometheus:/p" -w /p --entrypoint promtool prom/prometheus:v3.15.0 check rules demo-alerts.yml
       docker run --rm -v "$PWD/alertmanager:/a" -w /a --entrypoint amtool prom/alertmanager:v0.34.1 check-config alertmanager.yml
       docker run --rm -v "$PWD/alertmanager:/a" -w /a --entrypoint amtool prom/alertmanager:v0.34.1 config routes test --config.file=alertmanager.yml alertname=CheckoutErrorRate service=checkout severity=P1

   (Windows PowerShell: `-v "${PWD}/prometheus:/p"`.) Neither `amtool` command evaluates an inhibition. Prove yours
   the way Lecture 4 slide 11 showed - on a throwaway Alertmanager, never the playground's, which would page your
   pager:

       docker run -d --name am-try -v "$PWD/alertmanager:/etc/alertmanager:ro" prom/alertmanager:v0.34.1 --config.file=/etc/alertmanager/alertmanager.yml --cluster.listen-address=
       docker exec am-try amtool --alertmanager.url=http://localhost:9093 alert add alertname=PaymentDown service=payment severity=P1 cluster=shop
       docker exec am-try amtool --alertmanager.url=http://localhost:9093 alert add alertname=CheckoutErrorRate service=checkout severity=P2 cluster=shop
       docker exec am-try amtool --alertmanager.url=http://localhost:9093 -o extended alert query -i
       docker rm -f am-try

   (with your own alerts' labels). The target your rule inhibits is listed `suppressed`. Then run
   `./itsmlab.sh verify 4` and read L4-CORE-2: the checker does the same with every case of `routing-tests.yml`, on a
   fresh Alertmanager each. Until you have a snapshot the incident checks report `error` (`incident/tsdb-snapshot.tar.gz
   not found`); that is expected.

3. **Rehearse the ticket path**, during the baseline: create a practice ticket and acknowledge it.

       curl -X POST http://localhost:18080/tickets -H "Content-Type: application/json" -d '{"title": "Practice ticket before the fault", "reporter": {"name": "on-call"}, "impact": 3, "urgency": 3}'
       curl -X POST http://localhost:18080/tickets/<its id>/ack

   (Windows: `curl.exe`, with the JSON body in a file: `-d "@body.json"`.) It proves your `svcdesk` works inside
   the playground - that Prometheus scrapes it and the ticket's requests appear in its histogram, which I-16 reads -
   before a real page depends on it.

4. **The baseline.** Ten minutes after the start, `curl http://localhost:18090/status` says `baseline_so_far` is past
   `baseline_required`. The first minutes after `up -d` are a warm-up: the shop is slow while its services start,
   and a latency P1 can fire then and resolve by itself. The injector does not look at your alerts - it arms as soon
   as its ten minutes have passed - so the next step's check is yours.

5. **Check that your pages are quiet, then arm**, and wait for the pager. Right before you arm, no P1 may be firing
   or have fired in the last 10 minutes (I-10). Run this in Prometheus (http://localhost:9090/query, or the `curl`
   below on Linux and macOS):

       max_over_time(ALERTS{alertstate="firing", severity="P1"}[10m])

       curl -s http://localhost:9090/api/v1/query --data-urlencode 'query=max_over_time(ALERTS{alertstate="firing", severity="P1"}[10m])'

   It must return nothing (`"result":[]`). If it returns a series, do not arm: the alert it names fired on the
   healthy shop. Wait and run it again; a P1 that fired once in the warm-up drops out 10 minutes after its last
   firing. If it keeps firing, the rule is wrong: fix it (step 2), reload, and wait until the query returns nothing.
   Better still, `ALERTS{alertstate="firing"}` shows nothing at all: any alert that starts firing after the onset can
   become your detecting alert (I-12). Then arm:

       curl -X POST http://localhost:18090/arm

   202 says it is armed; 409 says why not (the baseline is too short, or it is armed already). I-10 counts the 10
   minutes back from the onset, not from the moment you arm, so a P1 that fires between arming and the onset fails it
   too. Once armed, the only way back is `down -v` and a new baseline; `itsmlab incident 4` prints a `warning:` line
   for every P1 that fired in those 10 minutes, with its times. The onset comes 2 to 6 minutes after you arm and
   nothing announces it: the pager does. If your inhibition mutes P2 while a shop P1 fires, as the template's
   example does (add P3 to its `target_matchers` if you want those muted too), no `chat` notification of a muted alert
   reaches the pager's page while the P1 fires: that is the inhibition working, not a broken chat route.

6. **Open a P1 ticket and acknowledge it**, in your `svcdesk` on port 18080, when the page arrives:

       curl -X POST http://localhost:18080/tickets -H "Content-Type: application/json" -d '{"title": "Shop checkout failing, paged by CheckoutErrorRate", "reporter": {"name": "on-call"}, "impact": 1, "urgency": 1}'
       curl -X POST http://localhost:18080/tickets/<its id>/ack

   Impact 1 and urgency 1 make it P1 under every Lab 1 decision. The server stamps `created_at` and
   `acknowledged_at`: the playground runs `svcdesk` with the test clock off, and no header can set a time.
   Acknowledge after the page - an acknowledgement before the detecting alert fired fails I-15. Keep the id: the
   snapshot command needs it, and the ticket goes into a public repository, so write nothing personal into it.

7. **Investigate.** What is broken for the shop's users, since when, and how badly: your alert, Grafana's dashboards,
   Jaeger's traces. Then the on-call's first question: what changed recently? The flags are visible - in the
   injector's `curl http://localhost:18090/flags.json` (a failing flag has a `defaultVariant` other than `off`) and
   in the `feature_flag.evaluation` span events in Jaeger. That is a legitimate clue, and the lab grades what you do
   with it: the flags you identify (I-22), the causes and the trigger you explain, the resolution you choose. Note
   every instant and what you saw and did; that is your timeline.

8. **Mitigate** by switching the flags off through the injector, one at a time, watching what each one changes:

       curl -X POST http://localhost:18090/flags/<flag>/off

   `"changed": true` means it was failing. That is your workaround, in ITIL's word. The demo's flag UI cannot do
   it: the injector's values override the demo's file.

9. **Recovery.** A detecting alert on the shop's symptoms resolves a few minutes after the last flag goes off; one on
   a single flag's symptom can resolve earlier, while other flags still fail (INCIDENT-SPEC.md section 4.3: the
   recovery is still that alert's). The pager shows the `resolved` notification of a P1 (with
   `send_resolved: true`). If you like, move the ticket on through your state machine
   (`/start`, `/resolve`): nothing checks it, but an incident record closes when service is restored (Lecture 4
   slide 16) - the problem record is the one that stays open.

10. **The AI investigator** works on the incident window: see AI usage below. Short of memory? Do step 11 first,
    stop the playground, serve the snapshot as [recorded/README.md](recorded/README.md) shows, and point the agent at
    it.

11. **The snapshot**, once the detecting alert has resolved and a minute more, with the playground still up:

        ./itsmlab.sh snapshot 4 --ticket <the P1 ticket's id>
        ./itsmlab.sh incident 4

    The first writes `incident/tsdb-snapshot.tar.gz` (through Prometheus's admin API) and `incident/ticket.json`
    (your `svcdesk`'s `GET /tickets/<id>`). The second prints the four instants, the detecting alert and the three
    durations exactly as the grader computes them, and a line for anything it cannot compute - `still firing` means
    the snapshot came too early: take it again. Commit `incident/`.

12. **Stop the playground** (`down -v`) when you no longer need it: everything that follows reads the snapshot. The
    `-v` deletes Prometheus's data, so first make sure `itsmlab incident 4` computed all four instants.

13. **The postmortem and the ledger**: `postmortem.md` from `postmortem-template.md`, with the values of
    `itsmlab incident 4`; `ai-rca-eval.json` from `ai-rca-eval-template.json`.

14. **Verify, tag `lab4/v1`, submit** (below).

## Four timestamps, three durations

The four instants and three clocks of Lecture 4 slide 14, each read from what you ship (INCIDENT-SPEC.md section 4.3
has the details):

| id | rule |
|---|---|
| **I-11** | **onset** = the timestamp of the first sample of `seeded_fault_active` (the series starts at the onset). |
| **I-12** | **detection** = the earliest start of a firing run of any `ALERTS{alertstate="firing"}` series that starts at or after the onset; a firing run is a sequence of samples of one label set no more than 1.5 evaluation intervals apart. That series is the **detecting alert**; when several runs start at that instant, it is the most severe (`P1`, then `P2`, `P3`, then any other), then the first by `alertname`, then by label set. (Prometheus sends Alertmanager `startsAt` = the moment the alert began firing, so this is the `startsAt` Alertmanager shows, also for an alert your inhibition lists as `suppressed`.) |
| **I-13** | **recovery** = the end of the detecting alert's firing run: its last sample plus its rule group's evaluation interval (10 s unless the group sets `interval`) - the `endsAt` Prometheus sends when the alert resolves. A detecting alert still firing at the end of the snapshot has no recovery: take the snapshot after it resolves. |
| **I-14** | **acknowledgement** = `acknowledged_at` of the P1 ticket in `incident/ticket.json`. **MTTD = detection - onset, MTTA = acknowledgement - detection, MTTR = recovery - onset**, in whole seconds: the differences of the instants as `itsmlab incident 4` prints them. Each is a single difference: one incident has no mean. The postmortem declares the four instants and the three durations, each within **30 s** of the recomputed value, and `detecting_alert`, the recomputed detecting alert's name. `itsmlab incident 4` prints the recomputation - it is the grader's script. |

Rule groups do not tie. Prometheus evaluates each group at its own offset inside the 10 s interval, so alerts in
different groups that see the same symptom start a few seconds apart, and the earliest wins whatever its severity:
a P3 cause alert in one group can beat the P1 page in another by one second, and it detects even while your
inhibition mutes it. Put the alerts that should compete on severity into one group, or expect that race; either way
the postmortem names the alert `itsmlab incident 4` prints.

MTTD is the time to detect (from the fault to the first alert), MTTA the time to acknowledge (from the alert to the
person), MTTR the time to recover (from the fault to its end, as the detecting alert sees it). The letters mean
"mean time", and over many incidents they are means; for one incident each is a single difference. Write the four
instants in UTC, as the command prints them.

## Core specs (all must pass; no partial credit inside the bundle)

| spec | what it checks |
|---|---|
| `L4-CORE-1` `compose-up` | your `svcdesk` still builds from your repository and answers `GET /health` |
| `L4-CORE-2` `alerting` | the shop's alerts and `svcdesk`'s; the receivers; P1 to the pager, P2 and P3 to chat; your route cases; your inhibitions on a running Alertmanager; the equal-labels pair (I-01 to I-08) |
| `L4-CORE-3` `incident` | the snapshot: one run, the baseline gate, detection, recovery; the ticket; the acknowledgement in `svcdesk`'s telemetry; the page; **the postmortem's clocks against the recomputation** (I-09 to I-17) |
| `L4-CORE-4` `postmortem` | the front matter, the thirteen fields, incident and problem separated, the action items, the timeline, and the fault identified (Tier B) (I-18 to I-22) |
| `L4-CORE-5` `ai-scorecard` | the ledger and its transcript, verbatim quotes, evaluable predictions, re-executed on your snapshot, false on the baseline, components against the fault (Tier B) (I-23 to I-28) |

**The recomputation is the heart of the lab** (3.09, 5.04), as resolution was in Lab 3: you do not report your
incident, you ship the data it left behind, and every number is computed again from it.

## Stretch (any two of three; each lifts the grade band equally)

| spec | what it is |
|---|---|
| `L4-STRETCH-1` `second-investigator` | **I-29.** `ai-rca-eval-2.json` from a different agent or model (HolmesGPT with Gemini or Ollama, Claude Code, or the other free option), scored by I-23 to I-28, and `ai-rca/COMPARISON.md` of at least 600 characters. |
| `L4-STRETCH-2` `regulator-clocks` | **I-30.** The front matter of `comms-log.md` declares the awareness (NIS2), detection (KSC) and classification (DORA) instants you defend, the submission instants of the reports you would send, and the deadlines: NIS2 early warning +24 h and notification +72 h from awareness, final report one calendar month after the notification; KSC the same from detection; DORA initial report 4 h after classification and no later than 24 h after awareness when classified within those 24 h (else 4 h after classification), intermediate 72 h after the initial notification, final one month after the intermediate report (the weekend relief of the DORA technical standard, Art. 5(4), is ignored). The checker recomputes every deadline (+-1 minute). |
| `L4-STRETCH-3` `k8s` | **I-31.** `k8s/k8sgpt-analyze.json` (`k8sgpt analyze -o json`, k8sgpt v0.4.39, against the demo's Helm chart 0.42.3 on kind with your incident's flags set) and `k8s/COMPARISON.md` (at least 600 characters) comparing its analyzers with the agentic loop. Structure only. |

**Stretch 1.** "Different" means another (agent, model) pair in `investigator`: the course's agent loop with
`qwen3:1.7b` and the same loop with a Gemini model are two investigators; so are Gemini CLI and the loop. Claude
Code is allowed here and never required: register the same MCP server with `claude mcp add`, ask the same question,
and save the conversation with `/export`. Keep the second transcript as `ai-rca/second/transcript.md`: the
AI-disclosure advisory exempts files whose name begins with `transcript`, and the agent loop writes wherever
`TRANSCRIPT` points.
The comparison says where the two agreed, where they parted, and which one your data proved right, entry by entry.

**Stretch 2.** Start from [comms-log-template.md](comms-log-template.md); INCIDENT-SPEC.md section 4.7 has the
arithmetic key by key and a worked example. Write every instant in UTC: Warsaw leaves summer time in the night
after the lab, and a deadline 24 hours after a Saturday noon is 11:00 on a Warsaw clock on Sunday, not 12:00.

**Stretch 3.** The agenda's Kubernetes track: k8sgpt against the demo's Helm chart on kind. It is optional, never
required, **explicitly discouraged at this RAM budget**, and the least machine-checkable option: what is checked is
that the JSON is k8sgpt's (an object with a `results` list) and that the comparison exists.

- **Memory and time.** The whole chart runs in one kind node, which used **6.1 to 6.8 GiB** in the course's runs -
  more than the compose playground. Take your snapshot and stop the playground (`down -v`) first; never run both.
  From `helm install` to every pod running took 6 minutes on a quiet machine (the node pulls the images itself) and
  20 minutes when the inotify limit below got in the way.
- **Versions** (tested 11 October 2026): kind v0.33.0, kubectl v1.35.9, Helm v4.3.0, the chart `opentelemetry-demo`
  0.42.3 (app version 3.1.0, the playground's), k8sgpt v0.4.39. (v0.4.38, named here before, has no release
  binaries.)
- **k8sgpt** is one binary from its release page (Linux x86_64 below; macOS `k8sgpt_Darwin_arm64.tar.gz`, Windows
  `k8sgpt_Windows_x86_64.zip`):

      curl -LO https://github.com/k8sgpt-ai/k8sgpt/releases/download/v0.4.39/k8sgpt_Linux_x86_64.tar.gz
      tar -xzf k8sgpt_Linux_x86_64.tar.gz k8sgpt
      ./k8sgpt version                  # k8sgpt: 0.4.39 (ed1aac4)

  Or the official image, `ghcr.io/k8sgpt-ai/k8sgpt:v0.4.39`, in place of `./k8sgpt` below (Linux; it needs the
  host's network to reach kind's API on 127.0.0.1):

      docker run --rm --network host --user "$(id -u)" -e HOME=/tmp -v "$HOME/.kube:/kube:ro" \
        -e KUBECONFIG=/kube/config ghcr.io/k8sgpt-ai/k8sgpt:v0.4.39 analyze -o json > k8s/k8sgpt-analyze.json

- **The cluster and the chart.** At the chart's default limits `ad`, `fraud-detection` and Grafana are OOM-killed on
  kind; the `--set` lines give them room:

      kind create cluster --name itsm-k8s
      helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
      helm install demo open-telemetry/opentelemetry-demo --version 0.42.3 \
        --set components.ad.resources.limits.memory=512Mi \
        --set components.fraud-detection.resources.limits.memory=512Mi \
        --set grafana.resources.limits.memory=512Mi --set grafana.sidecar.resources.limits.memory=512Mi
      kubectl get pods -w               # wait until every pod is Running and ready

  On Linux, a node that does not start or a `kube-proxy` that crash-loops with "too many open files" is kind's
  known inotify limit (https://kind.sigs.k8s.io/docs/user/known-issues/): `sudo sysctl
  fs.inotify.max_user_watches=524288 fs.inotify.max_user_instances=512`. Other containers and clusters count against
  it.
- **What to analyse: your incident's fault.** The injector exists only in the compose playground; the chart runs
  the demo's own flagd. Set the three flags of your incident in its ConfigMap by hand - `kubectl edit configmap
  flagd-config`, and in its `demo.flagd.json` give each flag the `defaultVariant` it had in the injector's
  `/flags.json` (for `productCatalogFailure` also change the first `"off"` of its `targeting` to `"on"`: its
  targeting overrides `defaultVariant`, and the injector does the same). Then `kubectl rollout restart deploy/flagd`,
  wait five minutes for the symptoms, and analyse:

      ./k8sgpt analyze -o json > k8s/k8sgpt-analyze.json
      kind delete cluster --name itsm-k8s           # when you are done

  An `analyze` before you set the flags is worth keeping too (`k8s/k8sgpt-analyze-baseline.json`, not checked).
- **No AI backend is needed.** `analyze` without `--explain` runs k8sgpt's analyzers alone, and that is the graded
  file. `--explain` sends each finding to a model for an explanation; it is optional and not checked - with a local
  Ollama: `./k8sgpt auth add --backend ollama --model qwen3:1.7b --baseurl http://localhost:11434`, then
  `./k8sgpt analyze --explain --backend ollama -o json`.
- **What k8sgpt can and cannot see** - the point of the comparison. Its analyzers read the state of Kubernetes
  objects: pods that crash or were OOM-killed, failing probes, Services without ready endpoints, unused ConfigMaps.
  A feature-flag fault leaves every pod running and ready, and requests fail or slow down inside them. In the
  course's runs k8sgpt reported OOM kills (before the `--set` lines) and unused ConfigMaps, and nothing about the
  three flags, while the chart's Prometheus showed product-catalog and frontend failing and checkout's p95 at 13 s.
  `k8s/COMPARISON.md` says, finding by finding, what k8sgpt reported, what your agent loop and your ledger found,
  and which of the incident's symptoms each tool could observe at all.

## AI usage

An AI agent investigates; you grade the agent. The deliverable is a **scorecard**, not a working agent. This is
AIAS level 3, and Claude Pro is never on the Core path:

| Core AI step | Default | Free alternative (no card) | Without AI |
|---|---|---|---|
| Lab 4 AI investigator | Gemini CLI with the supplied Prometheus MCP server (free, with an AI Studio key) | Ollama `qwen3:1.7b` behind an OpenAI-compatible agent, same MCP server | the recorded investigator transcript shipped with the lab |

All three reach the same grade bands. The ledger is graded on whether your verdicts agree with the data, never on
whether the agent was right: an agent that invents metric names, blames the wrong service or offers only vague
suspicions gives you `hallucinated` and `unfalsifiable` entries, which score exactly as `correct` ones do.

**The MCP server** is the course's own, `agent/prom_mcp.py`: five read-only tools over Prometheus's HTTP API -
`list_metrics`, `label_values`, `query`, `query_range`, `alerts_at` - each PromQL tool with an explicit time,
because an incident is investigated after the fact. Its versions are pinned in `agent/requirements.txt` (27
September 2026: `mcp==2.2.0`, `openai==3.19.2`); name it in your ledger as `prom_mcp.py (mcp 2.2.0)`. It reads
`PROMETHEUS_URL` (default `http://localhost:9090`). Nothing it offers can change Prometheus, the shop or the fault,
and no metric names a flag of the pool (INCIDENT-SPEC.md section 2.3).

**Asking the agent.** Give it the window and the symptom, in UTC with the date, and not your own conclusions - the
point is to grade what it finds on its own:

    Checkout errors paged at 10:44:30Z on 2026-10-24. Investigate 10:30Z to 11:10Z. What is the cause?

The agent does not start blind, though: `alerts_at` returns every alert that was pending or firing, with your alert
names and labels, and those are your conclusions about where the symptoms are. A small model often reads them and
turns each alert into a hypothesis ("the CheckoutErrorRate alert suggests a failure in checkout"). Score such an
entry like any other - your query decides its verdict - and say in its `evidence`, and in `COMPARISON.md` for
Stretch 1, whether the agent went beyond what your alerts already told it.

**Gemini, and what changed in June.** Since 18 June 2026 "Login with Google" no longer works for Gemini CLI: the only
free route is an API key from Google AI Studio, in `GEMINI_API_KEY`, and it serves Flash models only. The model
names move: on 27 September 2026 the course's key got "no longer available to new users" for `gemini-2.5-flash`, and was
served `gemini-3.8-flash` and `gemini-3.5-flash-lite` (the aliases `gemini-flash-latest` and
`gemini-flash-lite-latest` always name the current ones - if a name below answers 404, take the alias). Google no
longer publishes the free limits; plan on a few investigations a day, and a Flash-Lite leaves more room than a Flash.
Whether a key without billing is served for Gemini CLI's own traffic is not verified, so the tested route with the
same key is the course's agent loop below: `gemini-3.8-flash` answered the course's pilot incident in 15 seconds. Never
commit the key.

- **Gemini CLI 0.61.0.** Register the MCP server in `.gemini/settings.json` in your repository root, and add that
  file to `.gitignore` (it holds paths of your machine):

      {"mcpServers": {"prom": {"command": "/home/you/itsm-agent/bin/python",
                               "args": ["/path/to/lab4/agent/prom_mcp.py"],
                               "env": {"PROMETHEUS_URL": "http://localhost:9090"},
                               "trust": true}}}

  (Windows: `C:/Users/you/itsm-agent/Scripts/python.exe`, forward slashes.) `trust` skips the confirmation of each
  tool call, which a run without a terminal cannot answer; the server is read-only. Run it headless, with the two
  settings it needs - without `--allowed-mcp-server-names prom` its MCP tools are silently dropped - and
  `-o stream-json`, which records every tool call:

      export GEMINI_API_KEY=<your key>
      mkdir -p ai-rca
      GEMINI_CLI_TRUST_WORKSPACE=true gemini -m gemini-3.8-flash --allowed-mcp-server-names prom -o stream-json \
        -p "Checkout errors paged at 10:44:30Z on 2026-10-24. Investigate 10:30Z to 11:10Z. What is the cause?" \
        > ai-rca/gemini.jsonl

  In that file the agent's words arrive in chunks, one JSON line each, so a sentence can be split across lines and
  never be found verbatim. Join them into the readable transcript your ledger quotes:

      jq -j 'if .type == "message" and .role == "user" then "# Gemini CLI transcript\n\n## Question\n\n\(.content)\n\n## Investigation\n\n"
        elif .type == "message" then .content
        elif .type == "tool_use" then "\n\n### Tool call `\(.tool_name)`\n\n```\n\(.parameters | tojson)\n```\n\n"
        elif .type == "tool_result" then "```\n\((.output // .error.message // "") | .[0:3000])\n```\n\n"
        else empty end' ai-rca/gemini.jsonl > ai-rca/transcript.md

  If the transcript shows no call to an `mcp_prom_...` tool, the server was not loaded and the agent answered from
  nothing: check `trust`, the paths, and the two settings. On Windows, run the two commands in Git Bash or WSL
  (Windows PowerShell 5 writes `>` as UTF-16, which jq cannot read), or take the agent loop, which writes its
  transcript itself.

- **The course's agent loop with Gemini** (the tested route): `agent/agent.py` speaks to any OpenAI-compatible
  endpoint, and Gemini has one:

      BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/ API_KEY=$GEMINI_API_KEY MODEL=gemini-3.8-flash \
        ~/itsm-agent/bin/python <lab4>/agent/agent.py "Checkout errors paged at 10:44:30Z on 2026-10-24. Investigate 10:30Z to 11:10Z. What is the cause?"

  Windows PowerShell: `$env:BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"`,
  `$env:API_KEY = $env:GEMINI_API_KEY`, `$env:MODEL = "gemini-3.8-flash"`, then
  `& $HOME\itsm-agent\Scripts\python.exe <lab4>\agent\agent.py "..."`.

**The free local path: Ollama with `qwen3:1.7b`** (1.4 GB) and the same agent loop, whose defaults are Ollama and
that model. Give Ollama an 8k context, or the tool results do not fit:

    OLLAMA_CONTEXT_LENGTH=8192 ollama serve        # in its own terminal; quit the Ollama app or stop its service first
    ~/itsm-agent/bin/python <lab4>/agent/agent.py "Checkout errors paged at 10:44:30Z on 2026-10-24. Investigate 10:30Z to 11:10Z. What is the cause?"

(Windows PowerShell: `$env:OLLAMA_CONTEXT_LENGTH = "8192"; ollama serve`.) A model this small is unreliable at a
multi-step investigation: it often invents metric names, or stops without an answer. That is fine - you are scoring
what it said, not repairing it. Run it again with a sharper question if one run gave you fewer than three
hypotheses.

The agent loop writes `ai-rca/transcript.md` in the directory you run it from (run it from your repository root):
every model message verbatim and every tool call with its arguments and result, plus a JSON-lines twin
`ai-rca/transcript.jsonl`. Every run is appended to the same files, and the ledger may quote any of them. Its
variables: `BASE_URL`, `API_KEY`, `MODEL`, `PROMETHEUS_URL`, `MAX_STEPS` (model calls before it must answer,
default 8), `TRANSCRIPT` (the transcript's path).

**Without AI: the recorded investigator transcript**, `transcript-recorded.md` in a recording's subfolder of the
Moodle folder "Laboratory 4 recordings" (`lab4-rec-1`, `lab4-rec-3` or `lab4-rec-4`, [recorded/README.md](recorded/README.md)):
an agent's investigation of that recording, saved verbatim. Copy it to `ai-rca/transcript.md`, name its agent and
model in `investigator` as the transcript records them, and score it. On the recorded path take your recording's
(`itsmlab recording 4`): it is about your incident; on the live path take any of the three: its hypotheses are claims
about another run, and you score them against your own snapshot all the same.

**Scoring.** One ledger entry per hypothesis the agent stated, quoted verbatim (I-24); for each testable one, your
own PromQL prediction that could prove it wrong, evaluated at an instant inside the fault (I-25 to I-27); a verdict
from Lecture 4 slide 25. No query, no timeline (slide 26): a hypothesis nobody tested has no place in the ledger,
and "untested" is not "unfalsifiable". INCIDENT-SPEC.md section 4.6 has the fields and how a prediction is run.

## Deliverables

At the repository root, on the tag you submit:

| path | what |
|---|---|
| `prometheus/demo-alerts.yml` | your symptom alerts on the shop (I-01, I-02) |
| `prometheus/alerts.yml` | Lab 3's, still loading, every alert with `severity` (I-03) |
| `alertmanager/alertmanager.yml`, `alertmanager/routing-tests.yml` | the routing tree and the cases that prove it (I-04 to I-08) |
| `incident/tsdb-snapshot.tar.gz`, `incident/ticket.json` | written by `itsmlab snapshot 4 --ticket <id>`, committed as written (I-09 to I-17) |
| `postmortem.md` | front matter, the thirteen fields, the problem record (I-18 to I-22) |
| `ai-rca-eval.json`, `ai-rca/transcript.md` | the ledger and the transcript it quotes (I-23 to I-28) |
| `itsmlab.yaml` | `lab: 4`, and `baselines: {lab3: student}` or `{lab3: checkpoint}` |
| `ai-rca-eval-2.json`, `ai-rca/second/transcript.md`, `ai-rca/COMPARISON.md` | Stretch 1 only |
| `comms-log.md` | Stretch 2 only |
| `k8s/k8sgpt-analyze.json`, `k8s/COMPARISON.md` | Stretch 3 only |

Know what you publish: your repository is public. The snapshot holds the shop's telemetry, whose labels include
`host_name` - the playground's overlay sets it to the constant `itsm-playground`, so your machine's name is not in
it - and the names of the other containers running on your Docker host (`container_name`: stop the ones you do not
want named before you start the playground, as its README says); the ticket holds whatever you typed into it.

## When a check fails

| check | the usual cause |
|---|---|
| 2.01 | fewer than two rules on the shop's telemetry with `service` and a P1-P3 `severity` (a rule on `svcdesk`'s metrics, or a heartbeat such as `Watchdog`, is allowed but does not count); no P1 among them |
| 2.05 | a route on a label your rule does not declare in `labels:`; a root receiver that catches a P1 |
| 2.06 | receivers in another order than `amtool` prints; a case whose labels are not your rule's |
| 2.07, 2.08 | matchers that do not match the posted labels; `equal` on a label the two alerts do not both carry; a pair that differs in two labels |
| 3.02 | a second armed run in the database: the injector was armed, then the stack restarted without `down -v` (a start that was never armed does not count). In the grade only: on the recorded path, a recording other than your login's (`itsmlab recording 4`, I-32) |
| 3.03 | a P1 that fires on the healthy shop - counting CLIENT spans, or a window shorter than 5 minutes; armed while a P1 had fired in the warm-up (step 5's query was not empty) |
| 3.04, 3.08 | no alert fired after the onset, or no P1 did: your rules do not watch the symptoms this fault caused |
| 3.05 | the snapshot was taken while the detecting alert was still firing |
| 3.06 | acknowledged before the page; not P1; a ticket in another copy of `svcdesk` |
| 3.07 | the ticket was created or acknowledged on another `svcdesk` than the playground's, so its requests are not in the snapshot (step 3 shows them in Prometheus), or `incident/ticket.json` was edited |
| 3.09 | Warsaw time instead of UTC; values copied before the final snapshot |
| 4.02 | a heading spelt differently; a field holding a date or a name alone (under 20 characters) |
| 4.03 | a section after `## Problem record` (it ends the postmortem); `Incident record:` without the ticket's id |
| 4.05 | the timeline in Warsaw time |
| 5.01 | fewer than three hypotheses; a verdict that is not one of the four; a correct entry's `component` not spelt as in INCIDENT-SPEC.md section 2.2 (`product-catalog`, not `productcatalogservice`) |
| 5.02 | a paraphrase, or changed punctuation or Markdown |
| 5.03 | `bool` in the comparison; no comparison at the top; a selector without a metric name (`{__name__=~"..."}`, `{job="..."}`); a metric the snapshot does not hold; `at` before the onset or after the snapshot; an unfalsifiable entry with a query |
| 5.04 | a `result` that is not what the query returns at `at`; a verdict the result contradicts |
| 5.05 | a prediction that is also true on the healthy shop |

## Submission, receipts and attempts

Same path as Labs 1 to 3; every command runs in your repository root (PowerShell users: `.\itsmlab.ps1`, `;`
instead of `&&`).

1. **Implement**, running `./itsmlab.sh verify 4` (Windows: `.\itsmlab.ps1 verify 4`) as often as you like. Tier A
   runs are unlimited and never count.
2. **Commit and push**: `git add -A && git commit -m "Lab 4 attempt 1" && git push origin main` (Windows:
   `git add -A; git commit -m "Lab 4 attempt 1"; git push origin main`). The snapshot is committed to git like any
   other file: at most 50 MB, packed as `itsmlab snapshot 4` wrote it, never unpacked in the repository.
3. **Verify the committed tree**: `./itsmlab.sh verify 4` (Windows: `.\itsmlab.ps1 verify 4`) exits 0 and its
   `commit` line does not say `(dirty)`.
4. **Tag and push the tag**: `git tag -a lab4/v1 -m "Lab 4 attempt 1"` and `git push origin lab4/v1`. Tier B
   grades the tag's files, never your working directory.
5. **Submission receipt**: `./itsmlab.sh submit 4 --kind submission --tag lab4/v1` (Windows:
   `.\itsmlab.ps1 submit 4 --kind submission --tag lab4/v1`). Open the URL, submit the issue, keep the receipt.
6. Three attempts. Attempt 1 is due Sunday 25 October 2026, 23:59:59 (Europe/Warsaw); that deadline is advisory - a
   receipt after it is marked `after_attempt1_due` and still counts. Attempts 2 and 3 are the correction window and
   close **Saturday 14 November 2026 at 08:00:00 Europe/Warsaw**, on the morning of session 5; a receipt after that
   instant is `late` and still counts, with 10 % off its points if it arrives before the lecture of session 6
   (Saturday 28 November 2026, 13:30) and 50 % off after that. The best attempt counts, after its penalty.
7. The grade arrives as a comment `itsmlab grade` on the same issue. No comment after an hour: ask on the forum with
   the issue number.

A later attempt keeps your incident. The snapshot and the ticket of attempt 1 stay valid for attempts 2 and 3: fix
the postmortem, the ledger or the alerting files and resubmit. A new run is a new fault, and all its artifacts -
snapshot, ticket, postmortem, ledger - must then come from that run.

## What the grader does that the checker cannot

Nothing of the playground runs on the grader. It runs the same checker, from the same image pinned by digest, on
your receipted tag, and recomputes everything from the two artifacts you ship, as `itsmlab incident 4` does on your
laptop. Then it does the one thing the checker cannot: it opens the fault the injector sealed into your snapshot. It
checks `identified_flags` against the three flags that really failed (I-22, 4.06), the `component` of every correct
and partially correct entry against the services those flags affect (I-28, 5.06), and that the sealed fault belongs
to the run in your snapshot and, on the recorded path, is your login's recording (3.02; I-09, I-32). Locally 4.06 and
5.06 show as `skip`.

Its messages name the check and the threshold, never a seeded flag: a later attempt is graded against the same run,
and the answer is not in the grade.

## The AI-disclosure header

Every file the `ai-disclosure` advisory covers (see the end of [CHECKS.md](CHECKS.md)) carries in its first ten
lines a comment matching `ai-generated: <0-100>% - <one line on how>`. For Lab 4 that is every file under `src/`,
`specs/`, `metrics/` and `ai-rca/` with extension `.py .go .ts .js .java .cs .rb .rs .kt .md` except a transcript
(a file whose name begins with `transcript`), every `prometheus/*.yml` and `alertmanager/*.yml`, and `DECISIONS.md`, `EDGE-CASES.md`,
`slo.md`, `ai-first-draft.md`, `postmortem.md`, `comms-log.md`:

    # ai-generated: 40% - Gemini CLI drafted the inhibit rule, I wrote the routes and the tests   (YAML)
    <!-- ai-generated: 10% - an assistant checked my spelling, the text is mine -->             (Markdown)

In `postmortem.md` and `comms-log.md` the front matter must come first: put the header on the line right after its
closing `---`, as the templates do. The transcript is the agent's by construction and needs no header; the ledger is
JSON and carries none. The templates' lines read `ai-generated: ??% - TODO ...` and are flagged by the advisory until
you replace `??` with a number. The checker lists files without the header as an advisory; the course rules require
it on every checked file.

## Style of the written artifacts

Plain prose. `postmortem.md` is read by the lecturer (after an AI pre-screen, see the disclosure line above), and
graded on whether it is a postmortem an engineer who was not there could act on - not on whether it restates the
rules:

- **Blameless** (Lecture 4 slide 18): what happened, and what each person knew at the time; never who is to blame.
  "You can't 'fix' people, but you can fix systems and processes."
- **The incident is not the problem** (slide 16). The incident record is the ticket: it restores service, and it
  closes when service is back. The problem record holds what stays open after that - the root cause, the known error,
  the workaround - until the cause is gone. Root Causes and Trigger are two fields for the same reason: what was
  already wrong, and what set it off.
- **Impact and Detection with numbers**: which requests failed or slowed, how many, for how long, each with the
  query that measured it; which alert detected the fault, after how long, and who would have noticed without it.
- **The Timeline admits an AI hypothesis only with its query** (slide 26): cite the ledger entry, its query and what
  it returned.
- **Action Items** that make the next incident shorter: detect sooner, restore faster, or stop it recurring, each
  with an owner and a Bug id - a ticket id such as `ITSM-42`, not `none`. Lab 4 does not check the Bug column, but
  Labs 6 and 8 refer to one of these action items by its Bug id; without one they take the row's Action Item text,
  quoted exactly.

In the ledger, `evidence` says what the query returned and why that decides the verdict; in `COMPARISON.md`, what
each investigator got right and wrong, entry by entry, and why.
