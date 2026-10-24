<!-- ai-generated: 0% - written by the course team -->
# The Lab 4 playground

The OpenTelemetry Demo 3.1.0 in its minimal mode, plus this directory: an overlay that adds the course's fault
injector, a pager, an Alertmanager with **your** configuration, and **your** `svcdesk`. Everything in the demo stays as
the demo ships it except six services, listed at the top of `compose.itsm.yaml` with the reason for each change.

Plan for about 4.5 GB of RAM while it runs and 14 GB of disk: the course's pilot measured 2.6 GB for the playground's
30 containers (OpenSearch alone takes 0.9 GB), and a local model for the AI investigation adds about 2 GB while it
answers. The images (about 3.6 GB of download, 3.3 GB on Apple Silicon; about 12.4 GB on disk) are pulled during
the pre-work, not in the lab.

## Once, before the lab (pre-work)

```sh
git clone --depth 1 --branch 3.1.0 https://github.com/open-telemetry/opentelemetry-demo.git
cd opentelemetry-demo
cp -r <this directory> itsm
```

Append to the demo's `.env.override` (it exists; keep what is in it):

```sh
DEMO_VERSION=3.1.0
IMAGE_VERSION=3.1.0
OTEL_RESOURCE_ATTRIBUTES=service.namespace=opentelemetry-demo,service.version=3.1.0
SVCDESK_REPO=/absolute/path/to/your/svcdesk/repository
ITSM_LOGIN=<your GitHub login>
```

Your repository must hold `alertmanager/alertmanager.yml` before the first start (the template in the Lab 4 package
is a working one): the playground's Alertmanager reads it from there and exits without it. Prometheus reads
`prometheus/alerts.yml` and `prometheus/demo-alerts.yml` from the same repository and starts without them.

`DEMO_VERSION=3.1.0` matters: without it the demo pulls its nightly `latest-*` images, which do not match the 3.1.0
files. The demo's own `.env` still says `IMAGE_VERSION=3.0.0` at tag 3.1.0 and bakes it into
`OTEL_RESOURCE_ATTRIBUTES` before this file is read, so without the third line every span says
`service_version="3.0.0"` although the images are 3.1.0. On Windows write the path with forward slashes (`C:/Users/you/svcdesk`).

Then pull everything once:

```sh
docker compose --env-file .env --env-file .env.override \
  -f compose.yaml -f compose.observability.yaml -f itsm/compose.itsm.yaml pull
```

It pulls 29 images and skips only your `svcdesk` ("No image to be pulled"), which is built from your repository.
Do not add `--ignore-buildable`: every demo service declares a `build:` next to its `image:`, so that flag skips
the whole demo.

## Start, and start over

From the `opentelemetry-demo` directory:

```sh
docker compose --env-file .env --env-file .env.override \
  -f compose.yaml -f compose.observability.yaml -f itsm/compose.itsm.yaml build svcdesk
docker compose --env-file .env --env-file .env.override \
  -f compose.yaml -f compose.observability.yaml -f itsm/compose.itsm.yaml up -d
```

The first command builds your `svcdesk` from your repository (run it again whenever you change your service: `up -d`
alone keeps the image it built last); the second starts the playground on the pulled images, in about half a minute.
**Never add `--build` to `up`**: it builds every demo service from source - Go, Rust, .NET, Java, Node and Python,
tens of minutes and many more gigabytes - and replaces the images you pulled with local builds.

To start over - after a restart of the injector, or to rehearse - stop with `down -v` (the `-v` deletes Prometheus's
data: a new run needs a new TSDB):

```sh
docker compose --env-file .env --env-file .env.override \
  -f compose.yaml -f compose.observability.yaml -f itsm/compose.itsm.yaml down -v
```

**What the demo sees of your machine.** The overlay gives the demo's collector a constant `host.name`
(`itsm-playground`), so your machine's name, often its owner's, is in no series of the snapshot you publish. The
collector still reads the statistics of *every* container on your Docker host (its `docker_stats` receiver), not
only the demo's, so the names of your other running containers do end up in it (`container_name` on `container_*`
series): stop the containers you do not want named there before you start the playground.

## What runs where

| what | address |
|---|---|
| the shop | http://localhost:8080 |
| Grafana (the demo's dashboards) | http://localhost:8080/grafana |
| Jaeger | http://localhost:8080/jaeger/ui |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| the pager (the on-call's phone) | http://localhost:18091 |
| the injector's status | http://localhost:18090/status |
| your svcdesk | http://localhost:18080 |

Prometheus loads `prometheus/alerts.yml` and `prometheus/demo-alerts.yml` from your repository, Alertmanager
`alertmanager/alertmanager.yml`. After editing them, reload without a restart:

```sh
curl -X POST http://localhost:9090/-/reload
curl -X POST http://localhost:9093/-/reload
```

## The injector

It serves the demo's feature flags to flagd. For ten minutes after it starts it refuses to arm: that is the baseline
your P1 alerts must stay quiet through. Then:

```sh
curl -X POST http://localhost:18090/arm          # the fault starts 2 to 6 minutes later, at a moment you do not know
curl http://localhost:18090/status               # armed? how long has the baseline run?
curl -X POST http://localhost:18090/flags/<flag>/off     # switch one flag back (mitigation)
```

The fault is three flags, one from each of three classes. It ends when you have switched all three off, or by
itself 45 minutes after it started. Do not use the demo's flag UI for these flags: the injector's values win.

## The course images, and where they come from

The overlay pulls three course images from the GitHub Container Registry, all public: the injector
`ghcr.io/swasik/seeded-flagd:2026`, the pager `ghcr.io/swasik/itsm-pager:2026` and the Lab 3 knowledge base
`ghcr.io/swasik/seeded-toxic:2026`. Three variables replace them when set in `.env.override`:
`ITSM_SEEDED_FLAGD_IMAGE`, `ITSM_PAGER_IMAGE` and `ITSM_SEEDED_TOXIC_IMAGE`. They exist for the course's own tests
with locally built images; leave them unset. The injector seals the fault with
the grader's public key, and an injector built from the sources seals it with another key: the grader cannot open
that fault, and 4.06 and 5.06 then fail.

## After the incident

```sh
./itsmlab.sh snapshot 4 --ticket <your P1 ticket id>     # writes incident/tsdb-snapshot.tar.gz and incident/ticket.json
./itsmlab.sh incident 4                                  # the four instants and three durations, as the grader computes them
```

Run both from your svcdesk repository while the playground is still up (`itsmlab.ps1` on Windows).
