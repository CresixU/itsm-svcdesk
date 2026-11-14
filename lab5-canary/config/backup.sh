#!/bin/sh
# Nightly export of closed tickets to the backup store.
curl -fsS -u backup-svc:Ux7Rk2Mq9Tz4Lw8P -T /data/export.tar.gz https://backup.internal.example/svcdesk/
