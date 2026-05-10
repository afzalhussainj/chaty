"""HTTP fetch layer (sync); swap implementation for Playwright-backed rendering later."""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

import httpx

from app.core.http_retries import TRANSIENT_HTTP_STATUSES
from app.crawler.types import FetchResult


@runtime_checkable
class HttpFetcher(Protocol):
    """Fetches a URL; implementations may add Playwright, caching, or tracing."""

    def fetch(self, url: str, *, method: str = "GET") -> FetchResult:
        """Return the final response after redirects (caller normalizes URLs)."""
        ...


class HttpxFetcher:
    """Default synchronous fetcher using httpx (redirects followed with a hard cap)."""

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        timeout_s: float = 30.0,
        max_redirects: int = 10,
        max_retries: int = 3,
        retry_backoff_s: float = 0.5,
        max_response_bytes: int = 8 * 1024 * 1024,
    ) -> None:
        self._user_agent = user_agent or "university-chatbot-crawler/1.0"
        self._timeout = timeout_s
        self._max_redirects = max_redirects
        self._max_retries = max(0, max_retries)
        self._retry_backoff_s = retry_backoff_s
        self._max_response_bytes = max(256_000, max_response_bytes)

    def _fetch_once(self, url: str, *, method: str) -> FetchResult:
        headers = {"User-Agent": self._user_agent}
        redirect_chain: list[str] = []
        with httpx.Client(
            follow_redirects=True,
            max_redirects=self._max_redirects,
            timeout=httpx.Timeout(
                connect=self._timeout,
                read=self._timeout,
                write=self._timeout,
                pool=self._timeout,
            ),
        ) as client:
            started = time.monotonic()
            with client.stream(method, url, headers=headers) as resp:
                for h in resp.history:
                    redirect_chain.append(str(h.url))

                body = bytearray()
                for chunk in resp.iter_bytes():
                    if time.monotonic() - started > self._timeout:
                        raise httpx.ReadTimeout(
                            f"Timed out while reading response body from {url}",
                            request=resp.request,
                        )
                    body.extend(chunk)
                    if len(body) > self._max_response_bytes:
                        raise httpx.ReadTimeout(
                            (
                                "Response body exceeded crawler max_response_bytes "
                                f"({self._max_response_bytes}) for {url}"
                            ),
                            request=resp.request,
                        )

                ct = resp.headers.get("content-type")
                return FetchResult(
                    url_requested=url,
                    final_url=str(resp.url),
                    status_code=resp.status_code,
                    content_type=ct,
                    body=bytes(body),
                    redirect_urls=tuple(redirect_chain),
                )

    def fetch(self, url: str, *, method: str = "GET") -> FetchResult:
        """Transient transport errors and retryable HTTP statuses are retried with backoff."""
        attempt = 0
        while True:
            try:
                result = self._fetch_once(url, method=method)
            except (httpx.TimeoutException, httpx.TransportError, httpx.RequestError):
                attempt += 1
                if attempt > self._max_retries:
                    raise
                time.sleep(self._retry_backoff_s * (2 ** (attempt - 1)))
                continue

            if (
                result.status_code in TRANSIENT_HTTP_STATUSES
                and attempt < self._max_retries
            ):
                attempt += 1
                time.sleep(self._retry_backoff_s * (2 ** (attempt - 1)))
                continue
            return result


class HeadOnlyFetcher:
    """Wraps another fetcher but only issues HEAD (for optional PDF verification)."""

    def __init__(self, inner: HttpFetcher) -> None:
        self._inner = inner

    def fetch(self, url: str, *, method: str = "HEAD") -> FetchResult:
        return self._inner.fetch(url, method="HEAD")
