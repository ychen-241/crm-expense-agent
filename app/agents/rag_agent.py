"""RAG 问答 Agent：向量化检索 → 拼提示词 → LLM 生成带引用回答。"""

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.factory import get_llm
from app.retrieval import vector_store
from app.retrieval.embedder import embed_query

_PROMPT_PATH = Path(__file__).parent / "prompts" / "rag_qa.md"


def _load_template() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_context(hits: list[dict]) -> str:
    blocks = [
        f"[片段{i + 1} | {h['document_title']}]\n{h['content']}"
        for i, h in enumerate(hits)
    ]
    return "\n\n".join(blocks) if blocks else "（知识库中暂无可用制度片段）"


def _to_citations(hits: list[dict]) -> list[dict]:
    return [
        {
            "document_title": h["document_title"],
            "chunk_index": h["chunk_index"],
            "score": h["score"],
            "snippet": h["content"][:120],
        }
        for h in hits
    ]


async def answer(db: AsyncSession, question: str) -> tuple[str, list[dict]]:
    """返回 (回答, 引用列表)。检索无结果时直接给出兜底话术，不调 LLM。"""
    query_vec = await embed_query(question)
    hits = await vector_store.search_chunks(db, query_vec)
    if not hits:
        return (
            "知识库中暂无相关制度文档，无法回答。请联系管理员上传报销制度，"
            "或直接咨询财务部。",
            [],
        )

    prompt = _load_template().format(context=_build_context(hits), question=question)
    reply = await get_llm().chat(
        [{"role": "system", "content": "你是严谨的企业报销制度助手。"},
         {"role": "user", "content": prompt}]
    )
    return reply, _to_citations(hits)
