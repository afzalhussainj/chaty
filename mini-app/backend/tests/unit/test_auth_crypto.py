"""Unit tests for password hashing and JWT helpers (no database)."""

from __future__ import annotations

import jwt
import pytest
from app.auth.password import hash_password, verify_password
from app.auth.tokens import create_access_token, decode_token
from app.core.settings import Settings


def test_hash_and_verify_roundtrip() -> None:
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong", h)


def test_create_and_decode_access_token() -> None:
    settings = Settings(
        jwt_secret_key="unit-test-secret-key-at-least-32-bytes-long",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
    )
    token, expires_in = create_access_token(
        subject="42",
        settings=settings,
        extra_claims={"email": "a@b.com", "role": "super_admin"},
    )
    assert expires_in == 30 * 60
    payload = decode_token(token, settings)
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.com"
    assert payload["role"] == "super_admin"
    assert payload["type"] == "access"


def test_decode_rejects_wrong_secret() -> None:
    s1 = Settings(
        jwt_secret_key="first-secret-key-at-least-32-bytes-long-xx",
        jwt_algorithm="HS256",
        access_token_expire_minutes=5,
    )
    s2 = Settings(
        jwt_secret_key="second-secret-key-at-least-32-bytes-long-x",
        jwt_algorithm="HS256",
        access_token_expire_minutes=5,
    )
    token, _ = create_access_token(subject="1", settings=s1)
    with pytest.raises(jwt.PyJWTError):
        decode_token(token, s2)
