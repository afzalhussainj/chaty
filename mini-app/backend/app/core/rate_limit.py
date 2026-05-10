"""Shared SlowAPI limiter (public endpoints)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# headers_enabled=False: with FastAPI + Pydantic return types, SlowAPI cannot inject
# rate-limit headers into a bare model (expects a Response); limits still apply.
public_limiter = Limiter(key_func=get_remote_address, headers_enabled=False)
