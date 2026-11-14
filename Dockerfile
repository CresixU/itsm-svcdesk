# Dockerfile - svcdesk (Lab 1), Python 3.13 / FastAPI.
# Two rules from API.md section 9: install every dependency at BUILD time (the grader's sandbox has no
# network once the image is built) and listen on port 8080 inside the container.
FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

WORKDIR /app

# Lab 5 (triage): the base image is pinned by digest above; this pulls the Debian fixes it does not yet contain
# (zlib1g CVE-2026-76844 and CVE-2026-85091 at the time of writing).
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Dependencies first, so Docker caches this layer while editing code.
# Lab 5 (triage): pip only installs. It carries old copies of msgpack, setuptools and urllib3 in pip/_vendor that no
# pip release has fixed yet, and svcdesk never calls pip at run time, so the same RUN removes it again.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt && pip uninstall -y pip

# Code lives under src/svcdesk (see src/README.md).
COPY src/ /app/src/

# The practice fixtures, so the tests profile (Stretch S3) can read them without a network call.
COPY fixtures/ /app/fixtures/

# The SQLite file goes to /data (a named volume in docker-compose.yml), so tickets survive a restart.
RUN mkdir -p /data
ENV SVCDESK_DB=/data/svcdesk.db
# Lab 3: no *_created gauge series next to every histogram label set (fewer series, M-07).
ENV PROMETHEUS_DISABLE_CREATED_SERIES=True

EXPOSE 8080
CMD ["uvicorn", "svcdesk.main:app", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8080"]
