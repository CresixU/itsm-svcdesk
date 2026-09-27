# ai-generated: 90% - Claude Code drafted this; the author reviewed the assertions against METRIC-SPEC.md
"""Lab 2 sanity checks against the running svcdesk service (see docs/lab2/METRIC-SPEC.md)."""
import json
import os

from .client import post

WINDOW = {"from": "2026-09-01T00:00:00Z", "to": "2026-09-22T00:00:00Z"}
FIXTURES_DIR = os.environ.get("SVCDESK_FIXTURES_DIR", "/app/fixtures")


def _load_practice_events():
    with open(os.path.join(FIXTURES_DIR, "events-practice.jsonl")) as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_practice_expected():
    with open(os.path.join(FIXTURES_DIR, "metrics-practice.json")) as f:
        return json.load(f)


def _post_metrics(events, window=WINDOW):
    status, body = post("/dora/metrics", {"window": window, "events": events})
    return status, body


def test_metrics_practice_fixture_matches_published_values():
    events = _load_practice_events()
    expected = _load_practice_expected()
    status, got = _post_metrics(events)
    assert status == 200
    for key in ("deployment_frequency_per_day", "change_lead_time_seconds_p50",
                "failed_deployment_recovery_time_seconds_p50", "change_fail_rate", "deployment_rework_rate"):
        assert got[key] == expected[key], f"{key}: expected {expected[key]}, got {got[key]}"
    assert got["counts"] == expected["counts"]
    assert got["anomalies"] == expected["anomalies"]
    assert got["ground_truth"] == expected["ground_truth"]


def test_metrics_is_a_pure_function():
    events = _load_practice_events()
    _, a = _post_metrics(events)
    _, b = _post_metrics(events)
    assert a == b


def test_metrics_is_order_independent():
    events = _load_practice_events()
    _, a = _post_metrics(events)
    _, b = _post_metrics(list(reversed(events)))
    assert a == b


def test_metrics_ignores_duplicate_events():
    events = _load_practice_events()
    _, a = _post_metrics(events)
    _, b = _post_metrics(events + events)
    assert a == b


def test_empty_log_reports_zeroes_and_nulls():
    status, body = _post_metrics([])
    assert status == 200
    assert body["deployment_frequency_per_day"] == 0.0
    assert body["change_lead_time_seconds_p50"] is None
    assert body["change_fail_rate"] is None
    assert all(v == 0 for v in body["counts"].values())
    assert all(v == 0 for v in body["anomalies"].values())


def test_malformed_reverts_reference_is_rejected():
    events = [{
        "event_id": "c-bad", "type": "commit", "at": "2026-09-01T01:00:00Z",
        "sha": "sha-bad", "branch": "main", "change_id": None, "reverts": "sha-nowhere",
    }]
    status, body = _post_metrics(events)
    assert status in (400, 422)
    assert "error" in body
