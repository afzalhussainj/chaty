"""Standard error envelope for HTTP and validation errors."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_http_exception_envelope() -> None:
    """404 responses use the shared ErrorResponse shape."""
    from app.api.exception_handlers import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/item")
    def _item() -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="missing")

    with TestClient(app) as client:
        r = client.get("/item")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "http_404"
    assert body["error"]["message"] == "missing"
