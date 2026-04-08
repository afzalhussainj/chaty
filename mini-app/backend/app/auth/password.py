"""Password hashing (bcrypt)."""

from __future__ import annotations

import bcrypt


def hash_password(plain: str) -> str:
    """Hash a plaintext password for storage."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plaintext against stored hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
