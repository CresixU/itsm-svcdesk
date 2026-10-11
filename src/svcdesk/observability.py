# ai-generated: 90% - Claude Code drafted this from MONITORING-SPEC.md M-03 to M-07; the author reviewed the labels and the ladder
"""The RED histogram of Lab 3 and the GET /metrics endpoint (docs/lab3/MONITORING-SPEC.md, section 2)."""
import time

from prometheus_client import REGISTRY, Histogram, generate_latest
from starlette.responses import Response

# The ladder: finite upper bounds in seconds, at most 30 (M-06; 28 here). Prometheus adds +Inf itself.
# Designed from the measured profile (slo.md, "Buckets"): p50 17 ms and a narrow slow mode at 70-112 ms that holds the
# p99 (q = 93.7 ms). Every bucket from 0.05 to 0.15 is at most 10 ms wide, and 5 ms wide across the slow mode, so any
# q between 0.05 and 0.15 is resolved (a bucket of at most 0.2 x q); the rest is coarse on purpose.
LADDER = [
    0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06,                      # the fast mode (median 17 ms)
    0.07, 0.075, 0.08, 0.085, 0.09, 0.095, 0.1, 0.105, 0.11, 0.115, 0.12,        # the slow mode, 5 ms steps
    0.13, 0.14, 0.15,                                                             # above the slow mode, 10 ms steps
    0.2, 0.3, 0.5, 1.0, 2.5,                                                      # the tail
]

REQUEST_DURATION = Histogram(
    "http_server_request_duration_seconds",
    "Duration of every HTTP request the service answers, in seconds.",
    ["http_request_method", "http_route", "http_response_status_code"],
    buckets=LADDER,
)

UNMATCHED_ROUTE = "unmatched"  # M-05: every request that matches no route gets this one constant
METRICS_PATH = "/metrics"


def _route_template(scope) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    return path if path else UNMATCHED_ROUTE


class MetricsMiddleware:
    """Pure ASGI middleware: observes every response exactly once, when its first byte is about to go out."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        observed = False

        def observe(status: int) -> None:
            nonlocal observed
            if observed:
                return
            observed = True
            route = _route_template(scope)
            if route == METRICS_PATH:
                return
            REQUEST_DURATION.labels(
                http_request_method=scope["method"],
                http_route=route,
                http_response_status_code=str(status),
            ).observe(time.perf_counter() - started)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                observe(message["status"])
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except BaseException:
            observe(500)
            raise


def metrics_endpoint() -> Response:
    # M-03: the Prometheus text exposition format, version 0.0.4, with a text/plain Content-Type.
    return Response(generate_latest(REGISTRY), media_type="text/plain; version=0.0.4; charset=utf-8")
