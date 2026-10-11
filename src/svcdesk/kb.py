# ai-generated: 90% - Claude Code drafted this from MONITORING-SPEC.md M-02; the author reviewed the refusal and 502 paths
"""GET /kb/search: one call to the kb-index dependency per request, no cache, no retry (M-02)."""
import os
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import APIRouter, FastAPI, Query

from .errors import ApiError

router = APIRouter()

DEFAULT_KB_INDEX_URL = "http://kb-index:8080"
UPSTREAM_TIMEOUT_SECONDS = 3.0  # M-02 asks for at least 2 s

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(UPSTREAM_TIMEOUT_SECONDS),
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=100),
        )
    return _client


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


@router.get("/kb/search")
async def kb_search(q: str = Query(min_length=1, max_length=200)) -> dict:
    base = os.environ.get("KB_INDEX_URL", DEFAULT_KB_INDEX_URL).rstrip("/")
    try:
        response = await _get_client().get(f"{base}/search", params={"q": q})
        if response.status_code != 200:
            raise ApiError(502, "upstream_unavailable", f"kb-index answered {response.status_code}")
        hits = response.json()["hits"]
    except ApiError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise ApiError(502, "upstream_unavailable", "kb-index did not answer with usable hits")
    return {"query": q, "hits": hits}
