# ai-generated: 90% - Claude Code drafted this from METRIC-SPEC.md R-01..R-21; the author reviewed every rule
# against the fixture and directed the gaming demonstration's target metric and rule
"""The five DORA metrics, ground truth and the six edge cases (docs/lab2/METRIC-SPEC.md).

Every rule id in a comment below (R-nn) is defined there; this module is a direct translation of
sections 2 to 5 into code, kept in the same order the spec presents them.
"""
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from .timeutil import parse_instant

VALID_TYPES = {"commit", "deployment", "incident"}
VALID_OUTCOMES = {"success", "failure"}
VALID_PHASES = {"opened", "resolved"}


class MalformedLogError(ValueError):
    """Raised when an event log fails the well-formedness rules of METRIC-SPEC.md section 1."""


# --- R-03 arithmetic ------------------------------------------------------------------------

def _delta_micros(later: datetime, earlier: datetime) -> int:
    d = later - earlier
    return (d.days * 86400 + d.seconds) * 1_000_000 + d.microseconds


def clamped_seconds(later: datetime, earlier: datetime) -> tuple[int, bool]:
    """(rounded, whole-second, half-up) duration later-earlier, clamped to >= 0; the bool says whether it was negative."""
    micros = _delta_micros(later, earlier)
    was_negative = micros < 0
    if was_negative:
        micros = 0
    seconds = (micros + 500_000) // 1_000_000
    return seconds, was_negative


def median_seconds(values: list[int]) -> Optional[int]:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    avg = (s[mid - 1] + s[mid]) / 2
    return int(Decimal(str(avg)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def round_rate(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


# --- section 1: parsing and well-formedness --------------------------------------------------

def _require(cond: bool, message: str) -> None:
    if not cond:
        raise MalformedLogError(message)


def _parse_common(raw: dict) -> tuple[str, str, datetime]:
    _require(isinstance(raw, dict), "event is not an object")
    event_id = raw.get("event_id")
    _require(isinstance(event_id, str) and 1 <= len(event_id) <= 64, "event_id must be 1..64 characters")
    event_type = raw.get("type")
    _require(event_type in VALID_TYPES, f"unknown event type {event_type!r}")
    at_raw = raw.get("at")
    _require(isinstance(at_raw, str), "at must be an RFC 3339 instant")
    try:
        at = parse_instant(at_raw)
    except ValueError:
        raise MalformedLogError(f"event {event_id}: at is not a valid RFC 3339 instant")
    return event_id, event_type, at


class ParsedLog:
    def __init__(self) -> None:
        self.commits: dict[str, dict] = {}  # sha -> {at, branch, change_id, reverts}
        self.deployments: dict[str, dict] = {}  # deployment_id -> {at, environment, outcome, commits, unplanned, caused_by}
        self.incidents: dict[str, dict] = {}  # incident_id -> {opened_at, resolved_at, deployments: set}


def parse_and_validate_events(raw_events: list[Any]) -> ParsedLog:
    _require(isinstance(raw_events, list), "events must be an array")

    seen_event_ids: set[str] = set()
    deduped: list[dict] = []
    for raw in raw_events:
        event_id, event_type, at = _parse_common(raw)
        if event_id in seen_event_ids:
            continue  # R-05: first occurrence wins, later ones are ignored, never an error
        seen_event_ids.add(event_id)
        deduped.append({"raw": raw, "event_id": event_id, "type": event_type, "at": at})

    log = ParsedLog()

    for e in deduped:
        if e["type"] != "commit":
            continue
        raw = e["raw"]
        sha = raw.get("sha")
        branch = raw.get("branch")
        change_id = raw.get("change_id")
        reverts = raw.get("reverts")
        _require(isinstance(sha, str) and sha, f"commit {e['event_id']}: sha is required")
        _require(isinstance(branch, str), f"commit {e['event_id']}: branch is required")
        _require(reverts is None or isinstance(reverts, str), f"commit {e['event_id']}: reverts must be a sha or null")
        _require(change_id is None or isinstance(change_id, str), f"commit {e['event_id']}: change_id must be a string or null")
        _require(
            (reverts is None) != (change_id is None),
            f"commit {e['event_id']}: change_id must be null exactly when reverts is not null",
        )
        _require(sha not in log.commits, f"commit {e['event_id']}: duplicate sha {sha}")
        log.commits[sha] = {"at": e["at"], "branch": branch, "change_id": change_id, "reverts": reverts}

    for e in deduped:
        if e["type"] != "deployment":
            continue
        raw = e["raw"]
        deployment_id = raw.get("deployment_id")
        environment = raw.get("environment")
        outcome = raw.get("outcome")
        commits = raw.get("commits")
        unplanned = raw.get("unplanned")
        caused_by = raw.get("caused_by")
        _require(isinstance(deployment_id, str) and deployment_id, f"deployment {e['event_id']}: deployment_id is required")
        _require(isinstance(environment, str), f"deployment {e['event_id']}: environment is required")
        _require(outcome in VALID_OUTCOMES, f"deployment {e['event_id']}: outcome must be success or failure")
        _require(isinstance(commits, list) and all(isinstance(c, str) for c in commits), f"deployment {e['event_id']}: commits must be an array of shas")
        _require(isinstance(unplanned, bool), f"deployment {e['event_id']}: unplanned must be a boolean")
        _require(caused_by is None or isinstance(caused_by, str), f"deployment {e['event_id']}: caused_by must be an incident_id or null")
        _require(deployment_id not in log.deployments, f"deployment {e['event_id']}: duplicate deployment_id {deployment_id}")
        log.deployments[deployment_id] = {
            "at": e["at"], "environment": environment, "outcome": outcome,
            "commits": commits, "unplanned": unplanned, "caused_by": caused_by,
        }

    for e in deduped:
        if e["type"] != "incident":
            continue
        raw = e["raw"]
        incident_id = raw.get("incident_id")
        phase = raw.get("phase")
        deployments = raw.get("deployments")
        _require(isinstance(incident_id, str) and incident_id, f"incident {e['event_id']}: incident_id is required")
        _require(phase in VALID_PHASES, f"incident {e['event_id']}: phase must be opened or resolved")
        _require(isinstance(deployments, list) and all(isinstance(d, str) for d in deployments), f"incident {e['event_id']}: deployments must be an array")
        entry = log.incidents.setdefault(incident_id, {"opened_at": None, "resolved_at": None, "deployments": set()})
        _require(
            not (phase == "opened" and entry["opened_at"] is not None),
            f"incident {incident_id}: more than one opened phase",
        )
        _require(
            not (phase == "resolved" and entry["resolved_at"] is not None),
            f"incident {incident_id}: more than one resolved phase",
        )
        if phase == "opened":
            entry["opened_at"] = e["at"]
        else:
            entry["resolved_at"] = e["at"]
        entry["deployments"].update(deployments)

    # cross-references
    for sha, c in log.commits.items():
        if c["reverts"] is not None:
            _require(c["reverts"] in log.commits, f"commit {sha}: reverts an unknown sha {c['reverts']!r}")
    for dep_id, d in log.deployments.items():
        for sha in d["commits"]:
            _require(sha in log.commits, f"deployment {dep_id}: commits names an unknown sha {sha!r}")
        if d["caused_by"] is not None:
            _require(d["caused_by"] in log.incidents, f"deployment {dep_id}: caused_by names an unknown incident {d['caused_by']!r}")
    for incident_id, inc in log.incidents.items():
        for dep_id in inc["deployments"]:
            _require(dep_id in log.deployments, f"incident {incident_id}: deployments names an unknown deployment {dep_id!r}")
        _require(
            not (inc["resolved_at"] is not None and inc["opened_at"] is None),
            f"incident {incident_id}: resolved without having been opened",
        )

    return log


# --- R-06 / R-07: change identity -------------------------------------------------------------

def _build_change_resolver(commits: dict[str, dict]):
    cache: dict[str, str] = {}

    def resolve(sha: str, _stack: Optional[set] = None) -> str:
        if sha in cache:
            return cache[sha]
        _stack = _stack or set()
        _require(sha not in _stack, f"commit {sha}: cyclic revert chain")
        c = commits[sha]
        if c["reverts"] is None:
            result = c["change_id"]
        else:
            result = resolve(c["reverts"], _stack | {sha})
        cache[sha] = result
        return result

    return resolve


# --- the endpoint's computation ----------------------------------------------------------------

def compute_metrics(window_from: datetime, window_to: datetime, raw_events: list[Any]) -> dict:
    log = parse_and_validate_events(raw_events)
    resolve = _build_change_resolver(log.commits)

    prod = [d for d in log.deployments.values() if d["environment"] == "production"]
    in_window = [d for d in prod if window_from <= d["at"] < window_to]
    successful_in_window = [d for d in in_window if d["outcome"] == "success"]
    failed_in_window = [d for d in in_window if d["outcome"] == "failure"]

    # R-08 / E1: one pair per sha, at its earliest successful in-window deployment
    first_deploy_for_sha: dict[str, dict] = {}
    for d in successful_in_window:
        for sha in d["commits"]:
            cur = first_deploy_for_sha.get(sha)
            if cur is None or d["at"] < cur["at"]:
                first_deploy_for_sha[sha] = d
    lead_time_values: list[int] = []
    negative_lead_time_pairs = 0
    for sha, d in first_deploy_for_sha.items():
        seconds, was_negative = clamped_seconds(d["at"], log.commits[sha]["at"])
        if was_negative:
            negative_lead_time_pairs += 1
        lead_time_values.append(seconds)
    change_lead_time_p50 = median_seconds(lead_time_values)
    lead_time_pairs = len(lead_time_values)

    # E3: distinct off-main shas carried by any in-window production deployment, any outcome
    off_main_shas = {
        sha for d in in_window for sha in d["commits"] if log.commits[sha]["branch"] != "main"
    }
    commits_never_on_main = len(off_main_shas)

    # E4: in-window production deployments with no linked commits
    deployments_without_commits = sum(1 for d in in_window if len(d["commits"]) == 0)

    # R-11
    window_days = _delta_micros(window_to, window_from) / 1_000_000 / 86400.0
    deployment_frequency_per_day = round_rate(len(in_window) / window_days)

    # R-12 / R-13: recovery and overlapping incidents
    def covering_incident(deployment_id: str) -> Optional[tuple[str, dict]]:
        candidates = [
            (iid, inc) for iid, inc in log.incidents.items() if deployment_id in inc["deployments"]
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda kv: (kv[1]["opened_at"], kv[0]))
        return candidates[0]

    recovered_values: list[int] = []
    open_failures = 0
    for d in failed_in_window:
        dep_id = next(k for k, v in log.deployments.items() if v is d)
        covering = covering_incident(dep_id)
        if covering is None or covering[1]["resolved_at"] is None:
            open_failures += 1
            continue
        seconds, _ = clamped_seconds(covering[1]["resolved_at"], d["at"])
        recovered_values.append(seconds)
    failed_deployment_recovery_p50 = median_seconds(recovered_values)
    recovered_failures = len(recovered_values)

    incident_intervals = [
        (iid, inc["opened_at"], inc["resolved_at"] if inc["resolved_at"] is not None else window_to)
        for iid, inc in log.incidents.items()
    ]
    overlapping_incident_pairs = 0
    n = len(incident_intervals)
    for i in range(n):
        _, a_start, a_end = incident_intervals[i]
        for j in range(i + 1, n):
            _, b_start, b_end = incident_intervals[j]
            if a_start < b_end and b_start < a_end:
                overlapping_incident_pairs += 1

    # R-14 / R-15
    change_fail_rate = round_rate(len(failed_in_window) / len(in_window)) if in_window else None
    rework_deployments = [d for d in in_window if d["unplanned"] and d["caused_by"] is not None]
    deployment_rework_rate = round_rate(len(rework_deployments) / len(in_window)) if in_window else None

    # counts.changes: distinct changes with >= 1 commit anywhere in the log
    all_change_ids = {resolve(sha) for sha in log.commits}
    changes_count = len(all_change_ids)
    revert_chains_collapsed = sum(1 for c in log.commits.values() if c["reverts"] is not None)

    # R-16 / R-17: ground truth
    delivered_change_ids: set[str] = set()
    first_delivery_instant: dict[str, datetime] = {}
    for d in successful_in_window:
        for sha in d["commits"]:
            cid = resolve(sha)
            delivered_change_ids.add(cid)
            cur = first_delivery_instant.get(cid)
            if cur is None or d["at"] < cur:
                first_delivery_instant[cid] = d["at"]

    first_commit_instant: dict[str, datetime] = {}
    for sha, c in log.commits.items():
        cid = resolve(sha)
        cur = first_commit_instant.get(cid)
        if cur is None or c["at"] < cur:
            first_commit_instant[cid] = c["at"]

    true_lead_values: list[int] = []
    for cid in delivered_change_ids:
        seconds, _ = clamped_seconds(first_delivery_instant[cid], first_commit_instant[cid])
        true_lead_values.append(seconds)
    true_change_lead_time_p50 = median_seconds(true_lead_values)

    return {
        "spec_version": "1.0.0",
        "window": {"from": window_from, "to": window_to},
        "deployment_frequency_per_day": deployment_frequency_per_day,
        "change_lead_time_seconds_p50": change_lead_time_p50,
        "failed_deployment_recovery_time_seconds_p50": failed_deployment_recovery_p50,
        "change_fail_rate": change_fail_rate,
        "deployment_rework_rate": deployment_rework_rate,
        "counts": {
            "deployments": len(in_window),
            "successful_deployments": len(successful_in_window),
            "failed_deployments": len(failed_in_window),
            "recovered_failures": recovered_failures,
            "open_failures": open_failures,
            "rework_deployments": len(rework_deployments),
            "lead_time_pairs": lead_time_pairs,
            "changes": changes_count,
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": deployments_without_commits,
            "commits_never_on_main": commits_never_on_main,
            "revert_chains_collapsed": revert_chains_collapsed,
            "overlapping_incident_pairs": overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered": len(delivered_change_ids),
            "true_change_lead_time_seconds_p50": true_change_lead_time_p50,
        },
    }
