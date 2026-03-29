"""HTTP fetch layer (sync); swap implementation for Playwright-backed rendering later."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx

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
    ) -> None:
        self._user_agent = user_agent or "university-chatbot-crawler/1.0"
        self._timeout = timeout_s
        self._max_redirects = max_redirects

    def fetch(self, url: str, *, method: str = "GET") -> FetchResult:
        headers = {"User-Agent": self._user_agent}
        redirect_chain: list[str] = []
        with httpx.Client(
            follow_redirects=True,
            max_redirects=self._max_redirects,
            timeout=self._timeout,
        ) as client:
            resp = client.request(method, url, headers=headers)
            for h in resp.history:
                redirect_chain.append(str(h.url))
            body = resp.content
            ct = resp.headers.get("content-type")
            return FetchResult(
                url_requested=url,
                final_url=str(resp.url),
                status_code=resp.status_code,
                content_type=ct,
                body=body,
                redirect_urls=tuple(redirect_chain),
            )


class HeadOnlyFetcher:
    """Wraps another fetcher but only issues HEAD (for optional PDF verification)."""

    def __init__(self, inner: HttpFetcher) -> None:
        self._inner = inner

    def fetch(self, url: str, *, method: str = "HEAD") -> FetchResult:
        return self._inner.fetch(url, method="HEAD")
