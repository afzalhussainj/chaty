"""Grounded refusal when no retrieval context (mocked deps)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.chat.answer_service import generate_chat_answer
from app.retrieval.types import HybridRetrievalResult


def test_empty_chunks_force_none_support() -> None:
    hybrid = HybridRetrievalResult(
        chunks=(),
        query_normalized="q",
        vector_candidates=0,
        fts_candidates=0,
        weights=(0.5, 0.5),
    )
    fake_sess = MagicMock()
    fake_sess.id = 7
    fake_sess.title = None

    settings = MagicMock(
        openai_api_key="sk-test",
        openai_chat_model="gpt-4o-mini",
        chat_retrieval_top_k=5,
        chat_openai_timeout_s=30.0,
    )

    with (
        patch("app.chat.answer_service.retrieve_hybrid", return_value=hybrid),
        patch(
            "app.chat.answer_service.create_response_with_schema_fallback",
            return_value=({}, '{"answer":"","cited_chunk_indices":[],"support":"high"}'),
        ),
        patch("app.chat.answer_service.get_settings", return_value=settings),
        patch("app.chat.answer_service.ChatSessionRepository") as CSR,
        patch("app.chat.answer_service.ChatMessageRepository"),
    ):
        CSR.return_value.get.return_value = None
        CSR.return_value.create.return_value = fake_sess
        CSR.return_value.next_sequence.side_effect = [0, 1]

        db = MagicMock()
        r = generate_chat_answer(
            db,
            tenant_id=1,
            user_message="anything",
            session_id=None,
            answer_mode="concise",
        )
    assert r.support == "none"
    assert "indexed" in r.answer.lower() or "not find" in r.answer.lower()


def test_invalid_json_from_model_raises() -> None:
    hybrid = HybridRetrievalResult(
        chunks=(),
        query_normalized="q",
        vector_candidates=0,
        fts_candidates=0,
        weights=(0.5, 0.5),
    )
    fake_sess = MagicMock(id=3, title=None)
    settings = MagicMock(
        openai_api_key="sk-test",
        openai_chat_model="gpt-4o-mini",
        chat_retrieval_top_k=5,
        chat_openai_timeout_s=30.0,
    )
    with (
        patch("app.chat.answer_service.retrieve_hybrid", return_value=hybrid),
        patch(
            "app.chat.answer_service.create_response_with_schema_fallback",
            return_value=({}, "not json"),
        ),
        patch("app.chat.answer_service.get_settings", return_value=settings),
        patch("app.chat.answer_service.ChatSessionRepository") as CSR,
        patch("app.chat.answer_service.ChatMessageRepository"),
    ):
        CSR.return_value.get.return_value = None
        CSR.return_value.create.return_value = fake_sess
        CSR.return_value.next_sequence.side_effect = [0, 1]
        db = MagicMock()
        try:
            generate_chat_answer(
                db,
                tenant_id=1,
                user_message="x",
                session_id=None,
                answer_mode="concise",
            )
        except RuntimeError as e:
            assert "invalid JSON" in str(e).lower() or "JSON" in str(e)
        else:
            raise AssertionError("expected RuntimeError")


def test_greeting_short_circuits_retrieval() -> None:
    fake_sess = MagicMock(id=11, title=None)
    settings = MagicMock(
        openai_api_key="sk-test",
        openai_chat_model="gpt-4o-mini",
        chat_retrieval_top_k=5,
        chat_openai_timeout_s=30.0,
    )
    with (
        patch("app.chat.answer_service.retrieve_hybrid") as mocked_retrieval,
        patch("app.chat.answer_service.get_settings", return_value=settings),
        patch("app.chat.answer_service.ChatSessionRepository") as CSR,
        patch("app.chat.answer_service.ChatMessageRepository"),
    ):
        CSR.return_value.get.return_value = None
        CSR.return_value.create.return_value = fake_sess
        CSR.return_value.next_sequence.side_effect = [0, 1]
        db = MagicMock()
        r = generate_chat_answer(
            db,
            tenant_id=1,
            user_message="hello",
            session_id=None,
            answer_mode="concise",
        )
    mocked_retrieval.assert_not_called()
    assert r.support == "none"
    assert "unibot" in r.answer.lower()
