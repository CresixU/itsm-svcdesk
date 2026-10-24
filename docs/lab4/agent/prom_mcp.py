# ai-generated: 100% - Claude Code (Opus 5.5) wrote this server for the course, from design/LAB4.md section 1.4; the lecturer reviews it
"""The course's Prometheus MCP server for Lab 4: five read-only tools over Prometheus's HTTP API, over stdio.

    PROMETHEUS_URL=http://localhost:9090 python prom_mcp.py          # started by the agent, never by hand

Read-only on purpose: nothing it exposes can change Prometheus, the shop or the fault. Every tool that evaluates
PromQL takes an explicit time, because an incident is investigated after the fact (a snapshot, a recording) where
"now" has no data. Answers are compact JSON, cut to what a small model can read.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from mcp.server import MCPServer

URL = os.environ.get("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
MAX_SERIES = 40
MAX_POINTS = 60
mcp = MCPServer("prometheus")


def _get(path: str, params: dict, method: str = "POST") -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    if method == "GET":
        request = urllib.request.Request(URL + path + (f"?{query}" if query else ""))
    else:
        request = urllib.request.Request(URL + path, data=query.encode(), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:          # Prometheus explains a bad query in a 400's body
        try:
            body = json.loads(exc.read())
        except ValueError:
            return {"error": f"HTTP {exc.code}"}
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    if body.get("status") != "success":
        return {"error": body.get("error", "request failed")}
    return body.get("data")


def _compact(data: dict) -> str:
    if not isinstance(data, dict) or "error" in data:
        return json.dumps(data)
    result = data.get("result")
    if data.get("resultType") == "vector":
        rows = [{"labels": r["metric"], "value": r["value"][1]} for r in result[:MAX_SERIES]]
    elif data.get("resultType") == "matrix":
        rows = [{"labels": r["metric"], "values": r["values"][:: max(1, len(r["values"]) // MAX_POINTS)]}
                for r in result[:MAX_SERIES]]
    else:
        rows = result
    extra = {"truncated_series": len(result) - MAX_SERIES} if isinstance(result, list) and len(result) > MAX_SERIES else {}
    return json.dumps({"resultType": data.get("resultType"), "result": rows, **extra})


@mcp.tool()
def list_metrics(contains: str = "") -> str:
    """List metric names in Prometheus, optionally only those containing `contains` (for example "span_metrics")."""
    data = _get("/api/v1/label/__name__/values", {}, "GET")
    if isinstance(data, dict):
        return json.dumps(data)
    names = [n for n in data if contains.lower() in n.lower()]
    return json.dumps({"count": len(names), "names": names[:200]})


@mcp.tool()
def label_values(label: str, metric: str = "") -> str:
    """List the values of one label, optionally only on series of one metric (for example label "service_name")."""
    params = {"match[]": metric} if metric else {}
    return json.dumps(_get(f"/api/v1/label/{urllib.parse.quote(label)}/values", params, "GET"))


@mcp.tool()
def query(expr: str, time: str) -> str:
    """Evaluate a PromQL expression at one instant (RFC 3339 such as YYYY-MM-DDTHH:MM:SSZ, inside the window you were asked about, or a unix time)."""
    return _compact(_get("/api/v1/query", {"query": expr, "time": time}))


@mcp.tool()
def query_range(expr: str, start: str, end: str, step: str = "60s") -> str:
    """Evaluate a PromQL expression over a time range (RFC 3339 or unix start and end, a step such as 60s)."""
    return _compact(_get("/api/v1/query_range", {"query": expr, "start": start, "end": end, "step": step}))


@mcp.tool()
def alerts_at(time: str) -> str:
    """The alerts that were pending or firing at one instant (the ALERTS series Prometheus keeps)."""
    return _compact(_get("/api/v1/query", {"query": "ALERTS", "time": time}))


if __name__ == "__main__":
    mcp.run()
