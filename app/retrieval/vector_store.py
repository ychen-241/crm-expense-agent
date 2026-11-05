"""向量检索。

PostgreSQL：pgvector 余弦距离索引检索；
SQLite 演示模式：全量取回后 Python 计算余弦相似度（仅演示用，生产一律走 PG）。
"""

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import KBChunk, KBDocument


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _to_hit(content: str, doc_title: str, chunk_index: int, score: float) -> dict:
    return {
        "content": content,
        "document_title": doc_title,
        "chunk_index": chunk_index,
        "score": round(float(score), 4),
    }


async def search_chunks(db: AsyncSession, query_vec: list[float], top_k: int | None = None) -> list[dict]:
    """返回 [{content, document_title, chunk_index, score}]，score 为余弦相似度（越大越相关）。"""
    settings = get_settings()
    k = top_k or settings.RETRIEVAL_TOP_K

    if db.get_bind().dialect.name == "postgresql":
        distance = KBChunk.embedding.cosine_distance(query_vec).label("distance")
        stmt = (
            select(KBChunk, KBDocument.title.label("doc_title"), distance)
            .join(KBDocument, KBChunk.document_id == KBDocument.id)
            .where(KBDocument.status == "active")
            .order_by(distance)
            .limit(k)
        )
        rows = (await db.execute(stmt)).all()
        return [_to_hit(c.content, title, c.chunk_index, 1.0 - float(dist)) for c, title, dist in rows]

    # SQLite 演示模式：Python 侧暴力余弦
    stmt = (
        select(KBChunk, KBDocument.title.label("doc_title"))
        .join(KBDocument, KBChunk.document_id == KBDocument.id)
        .where(KBDocument.status == "active")
    )
    rows = (await db.execute(stmt)).all()
    scored = sorted(
        ((c, title, _cosine(query_vec, c.embedding)) for c, title in rows),
        key=lambda t: t[2],
        reverse=True,
    )
    return [_to_hit(c.content, title, c.chunk_index, score) for c, title, score in scored[:k]]
