"""Retrieval limits and hybrid weights from application settings."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import get_settings


@dataclass(frozen=True, slots=True)
class RetrievalRuntimeConfig:
    top_k: int
    vector_pool: int
    fts_pool: int
    weight_vector: float
    weight_fts: float
    max_query_chars: int


def load_retrieval_config(
    *,
    top_k: int | None = None,
    vector_pool: int | None = None,
    fts_pool: int | None = None,
) -> RetrievalRuntimeConfig:
    s = get_settings()
    k = top_k if top_k is not None else s.retrieval_default_top_k
    vm = s.retrieval_vector_candidate_multiplier
    fm = s.retrieval_fts_candidate_multiplier
    vp = vector_pool if vector_pool is not None else max(k * vm, k)
    fp = fts_pool if fts_pool is not None else max(k * fm, k)
    wv = float(s.retrieval_weight_vector)
    wf = float(s.retrieval_weight_fts)
    total = wv + wf
    if total <= 0:
        wv, wf = 0.5, 0.5
    else:
        wv, wf = wv / total, wf / total
    return RetrievalRuntimeConfig(
        top_k=k,
        vector_pool=vp,
        fts_pool=fp,
        weight_vector=wv,
        weight_fts=wf,
        max_query_chars=s.retrieval_max_query_chars,
    )
