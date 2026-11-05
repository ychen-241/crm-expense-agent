"""Embedding 编排：批量 + 分批调用 LLM 适配层，业务侧唯一入口。"""

from collections.abc import Sequence

from app.core.llm.factory import get_llm

_BATCH_SIZE = 16


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """批量向量化；内部按 _BATCH_SIZE 分批，规避单请求 token 上限。"""
    llm = get_llm()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = list(texts[i : i + _BATCH_SIZE])
        vectors.extend(await llm.embed(batch))
    return vectors


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text]))[0]


__all__ = ["embed_query", "embed_texts"]
