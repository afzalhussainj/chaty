"""Shared httpx GET with transient-error retries (extraction / fetch helpers)."""

from __future__ import annotations

import time

import httpx

# Upstream / proxy errors (incl. common Cloudflare edge codes) — often worth retrying.
TRANSIENT_HTTP_STATUSES: frozenset[int] = frozenset({502, 503, 504, 520, 521, 522, 523, 524})
_TRANSIENT_STATUS = TRANSIENT_HTTP_STATUSES


def httpx_get_with_retry(
    url: str,
    *,
    user_agent: str,
    timeout_s: float,
    max_retries: int,
    backoff_s: float = 0.5,
) -> httpx.Response:
    """Retry transport failures and transient HTTP statuses (502–504, common Cloudflare 52x) with backoff."""
    attempt = 0
    while True:
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout_s) as client:
                resp = client.get(url, headers={"User-Agent": user_agent})
        except (httpx.TimeoutException, httpx.TransportError, httpx.RequestError):
            attempt += 1
            if attempt > max_retries:
                raise
            time.sleep(backoff_s * (2 ** (attempt - 1)))
            continue

        if resp.status_code in _TRANSIENT_STATUS and attempt < max_retries:
            attempt += 1
            time.sleep(backoff_s * (2 ** (attempt - 1)))
            continue
        return resp
