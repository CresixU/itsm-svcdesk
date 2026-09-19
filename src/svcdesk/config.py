# ai-generated: 90% - Claude Code drafted this from REQUIREMENTS.md/API.md; the author chose the C1/C2/C3 values
"""Configuration and the three C1/C2/C3 resolutions this running service exhibits.

These three constants must always match the front matter of DECISIONS.md (L1-CORE-4): the checker
probes the running service and compares what it observes with what the document declares.
"""
import os

C1 = "wallclock"  # wallclock | business - the SLA clock for P1 (DECISIONS.md, section C1)
C2 = "reopen"  # reopen | immutable - closed tickets and reopening (DECISIONS.md, section C2)
C3 = "vip"  # matrix | vip - VIP reporters and the priority matrix (DECISIONS.md, section C3)

DB_PATH = os.environ.get("SVCDESK_DB", "/data/svcdesk.db")


def test_clock_enabled() -> bool:
    return os.environ.get("SVCDESK_TEST_CLOCK", "0").strip().lower() in ("1", "true")
