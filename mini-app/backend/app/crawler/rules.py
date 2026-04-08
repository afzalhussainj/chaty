"""Host / path allowlists and exclude globs derived from crawl configuration."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from urllib.parse import urlparse

from app.models.crawl_config import CrawlConfig
from app.models.tenant import Tenant


@dataclass(frozen=True, slots=True)
class CrawlRules:
    """Compiled policy for whether a normalized URL may be fetched or registered."""

    allowed_hosts: frozenset[str]
    path_prefixes: tuple[str, ...]
    exclude_globs: tuple[str, ...]

    @classmethod
    def from_config(cls, config: CrawlConfig, tenant: Tenant | None = None) -> CrawlRules:
        hosts: set[str] = set()
        base = urlparse(config.base_url)
        if base.hostname:
            try:
                hosts.add(base.hostname.encode("idna").decode("ascii").lower())
            except UnicodeError:
                hosts.add(base.hostname.lower())

        if config.allowed_hosts:
            for h in config.allowed_hosts:
                try:
                    hosts.add(h.strip().lower().encode("idna").decode("ascii"))
                except UnicodeError:
                    hosts.add(h.strip().lower())

        if tenant and tenant.allowed_domains:
            for d in tenant.allowed_domains:
                d = d.strip().lower()
                if d:
                    try:
                        hosts.add(d.encode("idna").decode("ascii"))
                    except UnicodeError:
                        hosts.add(d)

        prefixes = config.path_prefixes or ()
        normalized_prefixes = tuple(p if p.startswith("/") else f"/{p}" for p in prefixes if p)

        globs = tuple(config.exclude_globs or ())

        return cls(
            allowed_hosts=frozenset(hosts),
            path_prefixes=normalized_prefixes,
            exclude_globs=globs,
        )

    def host_allowed(self, hostname: str) -> bool:
        try:
            hn = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError:
            hn = hostname.lower()
        return hn in self.allowed_hosts

    def path_included(self, path: str) -> bool:
        if not self.path_prefixes:
            return True
        p = path if path.startswith("/") else f"/{path}"
        return any(p.startswith(prefix) for prefix in self.path_prefixes)

    def path_excluded(self, path: str) -> bool:
        p = path if path.startswith("/") else f"/{path}"
        for pattern in self.exclude_globs:
            if fnmatch.fnmatch(p, pattern) or fnmatch.fnmatch(p.rstrip("/") or "/", pattern):
                return True
        return False

    def allows_url(self, canonical_url: str) -> bool:
        p = urlparse(canonical_url)
        host = p.hostname
        if host is None:
            return False
        if not self.host_allowed(host):
            return False
        path = p.path or "/"
        if self.path_excluded(path):
            return False
        return self.path_included(path)
