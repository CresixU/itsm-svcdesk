# ai-generated: 90% - Claude Code drafted this from REQUIREMENTS.md, API.md and METRIC-SPEC.md; the author
# chose the C1/C2/C3 resolutions, the gaming demonstration's target metric, and reviewed the DORA endpoints
"""svcdesk - the HTTP service (API.md, METRIC-SPEC.md). See specs/spec.md for C1/C2/C3, dora.py for the metrics."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import dora, storage
from .config import C2
from .errors import ApiError
from .models import CreateTicketIn
from .priority import compute_priority, targets_for
from .sla import ack_clock_for, due_at, is_outside_business_hours, resolve_clock_for
from .timeutil import format_instant, parse_instant

app = FastAPI(title="svcdesk")
storage.init_db()


# --- test clock (API.md section 8) -----------------------------------------------------------

def get_now(request: Request) -> datetime:
    from .config import test_clock_enabled

    if test_clock_enabled():
        header = request.headers.get("X-Test-Clock")
        if header:
            try:
                return parse_instant(header)
            except ValueError:
                raise ApiError(422, "validation", "X-Test-Clock is not a valid RFC 3339 instant")
    return datetime.now(timezone.utc)


# --- serialization -----------------------------------------------------------------------------

def _fmt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return format_instant(dt)


def serialize(t: dict) -> dict:
    return {
        "id": t["id"],
        "title": t["title"],
        "description": t["description"],
        "reporter": t["reporter"],
        "impact": t["impact"],
        "urgency": t["urgency"],
        "priority": t["priority"],
        "state": t["state"],
        "created_at": _fmt(t["created_at"]),
        "acknowledged_at": _fmt(t["acknowledged_at"]),
        "resolved_at": _fmt(t["resolved_at"]),
        "closed_at": _fmt(t["closed_at"]),
        "related_to": t["related_to"],
        "sla": {"ack_due_at": _fmt(t["ack_due_at"]), "resolve_due_at": _fmt(t["resolve_due_at"])},
    }


# --- error handlers (API.md section 7: every error is a top-level "error" object) --------------

@app.exception_handler(ApiError)
def _handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RequestValidationError)
def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    message = errors[0]["msg"] if errors else "validation error"
    return JSONResponse(status_code=422, content={"error": {"code": "validation", "message": message}})


@app.exception_handler(StarletteHTTPException)
def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    content = detail if isinstance(detail, dict) and "error" in detail else {
        "error": {"code": "http_error", "message": str(detail)}
    }
    return JSONResponse(status_code=exc.status_code, content=content)


# --- endpoints -----------------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets", status_code=201)
def create_ticket(payload: CreateTicketIn, now: datetime = Depends(get_now)) -> dict:
    priority = compute_priority(payload.impact, payload.urgency, payload.reporter.vip)
    ack_minutes, resolve_minutes = targets_for(priority)
    ack_clock = ack_clock_for(priority)
    resolve_clock = resolve_clock_for(priority)
    ticket = {
        "id": str(uuid4()),
        "title": payload.title,
        "description": payload.description,
        "reporter": {
            "name": payload.reporter.name,
            "email": payload.reporter.email,
            "vip": payload.reporter.vip,
        },
        "impact": payload.impact,
        "urgency": payload.urgency,
        "priority": priority,
        "state": "new",
        "created_at": now,
        "acknowledged_at": None,
        "resolved_at": None,
        "closed_at": None,
        "related_to": payload.related_to,
        "ack_due_at": due_at(now, ack_minutes, ack_clock),
        "resolve_due_at": due_at(now, resolve_minutes, resolve_clock),
        "resolve_clock": resolve_clock,
    }
    storage.insert(ticket)
    return serialize(ticket)


@app.get("/tickets")
def list_tickets(
    state: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
) -> list[dict]:
    return [serialize(t) for t in storage.list_tickets(state, priority)]


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str) -> dict:
    t = storage.get(ticket_id)
    if t is None:
        raise ApiError(404, "not_found", "ticket not found")
    return serialize(t)


@app.get("/tickets/{ticket_id}/sla")
def get_sla(ticket_id: str, now: datetime = Depends(get_now)) -> dict:
    t = storage.get(ticket_id)
    if t is None:
        raise ApiError(404, "not_found", "ticket not found")

    if t["acknowledged_at"] is not None:
        ack_breached = t["acknowledged_at"] > t["ack_due_at"]
    else:
        ack_breached = now > t["ack_due_at"]

    if t["resolved_at"] is not None:
        resolve_breached = t["resolved_at"] > t["resolve_due_at"]
    else:
        resolve_breached = now > t["resolve_due_at"]

    is_open = t["state"] not in ("resolved", "closed")
    paused = is_open and t["resolve_clock"] == "business" and is_outside_business_hours(now)

    return {
        "priority": t["priority"],
        "ack_due_at": _fmt(t["ack_due_at"]),
        "resolve_due_at": _fmt(t["resolve_due_at"]),
        "ack_breached": ack_breached,
        "resolve_breached": resolve_breached,
        "paused": paused,
    }


def _apply_transition(t: dict, action: str, now: datetime) -> None:
    state = t["state"]
    if action == "ack":
        if state != "new":
            raise ApiError(409, "invalid_transition", f"cannot acknowledge a ticket in state {state}")
        t["state"] = "acknowledged"
        t["acknowledged_at"] = now
    elif action == "start":
        if state != "acknowledged":
            raise ApiError(409, "invalid_transition", f"cannot start a ticket in state {state}")
        t["state"] = "in_progress"
    elif action == "resolve":
        if state != "in_progress":
            raise ApiError(409, "invalid_transition", f"cannot resolve a ticket in state {state}")
        t["state"] = "resolved"
        t["resolved_at"] = now
    elif action == "close":
        if state != "resolved":
            raise ApiError(409, "invalid_transition", f"cannot close a ticket in state {state}")
        t["state"] = "closed"
        t["closed_at"] = now
    elif action == "reopen":
        if state == "resolved":
            if now > t["resolved_at"] + timedelta(days=7):
                raise ApiError(409, "reopen_window_expired", "reopen window has expired")
        elif state == "closed":
            if C2 != "reopen":
                raise ApiError(409, "ticket_closed", "closed tickets cannot be reopened; open a new ticket")
            if now > t["closed_at"] + timedelta(days=7):
                raise ApiError(409, "reopen_window_expired", "reopen window has expired")
        else:
            raise ApiError(409, "invalid_transition", f"cannot reopen a ticket in state {state}")
        t["state"] = "in_progress"
        t["resolved_at"] = None
        t["closed_at"] = None
    else:  # pragma: no cover - internal use only
        raise ValueError(f"unknown action {action}")


def _transition(ticket_id: str, action: str, now: datetime) -> dict:
    t = storage.get(ticket_id)
    if t is None:
        raise ApiError(404, "not_found", "ticket not found")
    _apply_transition(t, action, now)
    storage.update(t)
    return t


@app.post("/tickets/{ticket_id}/ack")
def ack(ticket_id: str, now: datetime = Depends(get_now)) -> dict:
    return serialize(_transition(ticket_id, "ack", now))


@app.post("/tickets/{ticket_id}/start")
def start(ticket_id: str, now: datetime = Depends(get_now)) -> dict:
    return serialize(_transition(ticket_id, "start", now))


@app.post("/tickets/{ticket_id}/resolve")
def resolve(ticket_id: str, now: datetime = Depends(get_now)) -> dict:
    return serialize(_transition(ticket_id, "resolve", now))


@app.post("/tickets/{ticket_id}/close")
def close(ticket_id: str, now: datetime = Depends(get_now)) -> dict:
    return serialize(_transition(ticket_id, "close", now))


@app.post("/tickets/{ticket_id}/reopen")
def reopen(ticket_id: str, now: datetime = Depends(get_now)) -> dict:
    return serialize(_transition(ticket_id, "reopen", now))


# --- Lab 2: DORA metrics (METRIC-SPEC.md) -------------------------------------------------------

class DoraWindowIn(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    from_: str = Field(alias="from")
    to: str


class DoraMetricsIn(BaseModel):
    model_config = ConfigDict(extra="ignore")
    window: DoraWindowIn
    events: list[dict[str, Any]]


def _format_metrics_response(result: dict) -> dict:
    out = dict(result)
    out["window"] = {"from": format_instant(result["window"]["from"]), "to": format_instant(result["window"]["to"])}
    return out


@app.post("/dora/metrics")
def dora_metrics(payload: DoraMetricsIn) -> dict:
    try:
        window_from = parse_instant(payload.window.from_)
        window_to = parse_instant(payload.window.to)
    except ValueError:
        raise ApiError(400, "validation", "window.from and window.to must be RFC 3339 instants")
    if not (window_to > window_from):
        raise ApiError(400, "validation", "window.to must be after window.from")
    try:
        result = dora.compute_metrics(window_from, window_to, payload.events)
    except dora.MalformedLogError as exc:
        raise ApiError(422, "validation", str(exc))
    return _format_metrics_response(result)


def _ticket_lifecycle_events(t: dict) -> list[dict]:
    events = []
    for phase, field, state in (
        ("created", "created_at", "new"),
        ("acknowledged", "acknowledged_at", "acknowledged"),
        ("resolved", "resolved_at", "resolved"),
        ("closed", "closed_at", "closed"),
    ):
        at = t[field]
        if at is not None:
            events.append({"ticket_id": t["id"], "at": at, "phase": phase, "priority": t["priority"], "state": state})
    return events


@app.get("/dora/ticket-events")
def dora_ticket_events() -> list[dict]:
    events = []
    for t in storage.list_tickets():
        events.extend(_ticket_lifecycle_events(t))
    events.sort(key=lambda e: (e["at"], e["ticket_id"]))
    return [{**e, "at": format_instant(e["at"])} for e in events]
