"""OpenAI Responses API client (HTTP); internal use only."""

from __future__ import annotations

import json
from typing import Any

import httpx

RESPONSES_URL = "https://api.openai.com/v1/responses"


def _output_text(data: dict[str, Any]) -> str:
    for item in data.get("output", []) or []:
        if item.get("type") != "message":
            continue
        for block in item.get("content", []) or []:
            if block.get("type") == "output_text":
                return str(block.get("text") or "")
    return ""


def create_response(
    *,
    api_key: str,
    model: str,
    instructions: str,
    user_text: str,
    timeout_s: float,
    json_schema: dict[str, Any] | None,
    schema_name: str = "grounded_answer",
) -> tuple[dict[str, Any], str]:
    """
    Call POST /v1/responses.

    Returns (raw_json, output_text).
    If ``json_schema`` is None, the model must still return JSON per instructions.
    """
    body: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": user_text}],
            },
        ],
        "temperature": 0.2,
    }
    if json_schema is not None:
        body["text"] = {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": json_schema,
            },
        }
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(
            RESPONSES_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
    return data, _output_text(data)


def create_response_with_schema_fallback(
    *,
    api_key: str,
    model: str,
    instructions: str,
    user_text: str,
    timeout_s: float,
    json_schema: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """Try structured outputs; on 400, retry without schema (instructions-only JSON)."""
    try:
        return create_response(
            api_key=api_key,
            model=model,
            instructions=instructions,
            user_text=user_text,
            timeout_s=timeout_s,
            json_schema=json_schema,
        )
    except httpx.HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code == 400:
            return create_response(
                api_key=api_key,
                model=model,
                instructions=instructions
                + "\n\nOutput a single JSON object with keys answer, cited_chunk_indices, "
                "support only.",
                user_text=user_text,
                timeout_s=timeout_s,
                json_schema=None,
            )
        raise


def parse_model_json(text: str) -> dict[str, Any]:
    """Parse model output; tolerate fenced code blocks."""
    s = text.strip()
    if s.startswith("```"):
        parts = s.split("\n", 1)
        s = parts[1] if len(parts) > 1 else s
        if "```" in s:
            s = s.rsplit("```", 1)[0]
    return json.loads(s)
