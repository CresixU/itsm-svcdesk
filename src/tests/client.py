# ai-generated: 90% - Claude Code drafted this; the author reviewed it against API.md and METRIC-SPEC.md
"""A tiny HTTP client for the tests profile: no extra dependency beyond the standard library."""
import json
import os
import urllib.error
import urllib.request

BASE_URL = os.environ.get("SVCDESK_URL", "http://svcdesk:8080").rstrip("/")


def request(method: str, path: str, body=None, headers: dict = None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())


def get(path: str, headers: dict = None):
    return request("GET", path, headers=headers)


def post(path: str, body=None, headers: dict = None):
    return request("POST", path, body=body, headers=headers)
