# ai-generated: 90% - Claude Code drafted this; the author reviewed the assertions against API.md and DECISIONS.md
"""Lab 1 sanity checks against the running svcdesk service (see docs/API.md)."""
from .client import get, post


def _make_ticket(impact, urgency, vip=False, clock="2026-10-14T10:00:00Z"):
    status, body = post(
        "/tickets",
        {"title": "test ticket", "reporter": {"name": "Tester", "vip": vip}, "impact": impact, "urgency": urgency},
        headers={"X-Test-Clock": clock},
    )
    assert status == 201, body
    return body


def test_health():
    status, body = get("/health")
    assert status == 200
    assert body == {"status": "ok", "service": "svcdesk"}


def test_priority_matrix_p1():
    ticket = _make_ticket(impact=1, urgency=1)
    assert ticket["priority"] == "P1"


def test_vip_override_raises_to_p2():
    # DECISIONS.md: C3 = vip - a P4-by-matrix VIP ticket is raised to P2.
    ticket = _make_ticket(impact=3, urgency=3, vip=True)
    assert ticket["priority"] == "P2"


def test_validation_missing_title_is_rejected():
    status, body = post(
        "/tickets",
        {"reporter": {"name": "Tester"}, "impact": 1, "urgency": 1},
        headers={"X-Test-Clock": "2026-10-14T10:00:00Z"},
    )
    assert status in (400, 422)
    assert "error" in body


def test_unknown_ticket_is_404():
    status, body = get("/tickets/does-not-exist-9f3c")
    assert status == 404
    assert "error" in body


def test_state_machine_ack_start_resolve_close():
    ticket = _make_ticket(impact=2, urgency=2, clock="2026-10-14T09:00:00Z")
    tid = ticket["id"]
    status, body = post(f"/tickets/{tid}/ack", headers={"X-Test-Clock": "2026-10-14T09:05:00Z"})
    assert status == 200 and body["state"] == "acknowledged"
    status, body = post(f"/tickets/{tid}/start", headers={"X-Test-Clock": "2026-10-14T09:06:00Z"})
    assert status == 200 and body["state"] == "in_progress"
    status, body = post(f"/tickets/{tid}/resolve", headers={"X-Test-Clock": "2026-10-14T09:07:00Z"})
    assert status == 200 and body["state"] == "resolved"
    status, body = post(f"/tickets/{tid}/close", headers={"X-Test-Clock": "2026-10-14T09:08:00Z"})
    assert status == 200 and body["state"] == "closed"


def test_reopen_closed_ticket_within_window():
    # DECISIONS.md: C2 = reopen - a closed ticket may be reopened within 7 days of closed_at.
    ticket = _make_ticket(impact=2, urgency=2, clock="2026-10-01T09:00:00Z")
    tid = ticket["id"]
    post(f"/tickets/{tid}/ack", headers={"X-Test-Clock": "2026-10-01T09:05:00Z"})
    post(f"/tickets/{tid}/start", headers={"X-Test-Clock": "2026-10-01T09:06:00Z"})
    post(f"/tickets/{tid}/resolve", headers={"X-Test-Clock": "2026-10-01T09:07:00Z"})
    post(f"/tickets/{tid}/close", headers={"X-Test-Clock": "2026-10-01T09:08:00Z"})
    status, body = post(f"/tickets/{tid}/reopen", headers={"X-Test-Clock": "2026-10-02T09:00:00Z"})
    assert status == 200 and body["state"] == "in_progress"


def test_sla_matches_published_t1_vector():
    # API.md section 4, vector T1: P1, business/wall-clock agree inside business hours.
    ticket = _make_ticket(impact=1, urgency=1, clock="2026-10-14T10:00:00Z")
    assert ticket["sla"]["ack_due_at"] == "2026-10-14T10:15:00Z"
    assert ticket["sla"]["resolve_due_at"] == "2026-10-14T14:00:00Z"
