"""robots.txt evaluation (pluggable; respects crawl_config.respect_robots_txt)."""

from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsChecker:
    """
    Per-host cache of `urllib.robotparser.RobotFileParser` built from fetched robots.txt.

    When disabled or on fetch/parse errors, URLs are allowed (fail-open for availability).
    """

    def __init__(
        self,
        *,
        enabled: bool,
        user_agent: str,
        http_timeout_s: float = 10.0,
    ) -> None:
        self._enabled = enabled
        self._user_agent = user_agent
        self._timeout = http_timeout_s
        self._hosts: dict[str, RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        if not self._enabled:
            return True
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        host_key = parsed.hostname.lower()
        rp = self._hosts.get(host_key)
        if rp is None:
            rp = self._load_robots(parsed.scheme, host_key, parsed.port)
            self._hosts[host_key] = rp
        if rp is None:
            return True
        return rp.can_fetch(self._user_agent, url)

    def _load_robots(self, scheme: str, hostname: str, port: int | None) -> RobotFileParser | None:
        if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
            netloc = f"{hostname}:{port}"
        else:
            netloc = hostname
        robots_url = f"{scheme}://{netloc}/robots.txt"
        try:
            with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                r = client.get(robots_url)
                if r.status_code >= 400:
                    return None
                text = r.text
        except (OSError, httpx.HTTPError, httpx.RequestError):
            return None
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.parse(text.splitlines())
        except (TypeError, ValueError, AttributeError):
            return None
        return rp


def noop_robots_checker() -> RobotsChecker:
    """Always allow (used when robots are disabled without constructing fetchers)."""
    return RobotsChecker(enabled=False, user_agent="*")
