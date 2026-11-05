"""演示/测试用 Mock 供应商：无需 API Key 与网络。

- embed：字符级哈希向量（词面重叠即可产生相似度，够演示检索命中）
- chat：返回模板化回复，注明当前为演示模式
"""

import hashlib
import math
import re
from collections.abc import AsyncIterator, Sequence

from app.core.config import get_settings
from app.core.llm.base import BaseLLM

_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")


def _hash_vector(text: str, dim: int) -> list[float]:
    vec = [0.0] * dim
    for token in _TOKEN_RE.findall(text.lower()):
        idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class MockLLM(BaseLLM):
    def __init__(self, dim: int | None = None):
        self.dim = dim or get_settings().EMBEDDING_DIM

    async def chat(self, messages: list[dict], *, stream: bool = False) -> str | AsyncIterator[str]:
        raw = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        question = raw.split("问题：")[-1].strip() if "问题：" in raw else raw
        reply = (
            "【Mock 演示回答】\n"
            f"针对「{question[:120]}」，已基于知识库检索片段作答。\n"
            "当前 LLM_PROVIDER=mock（离线演示模式），"
            "在 .env 配置真实供应商的 LLM_API_KEY 后即可获得正式生成内容。"
        )
        if not stream:
            return reply

        async def _gen() -> AsyncIterator[str]:
            for i in range(0, len(reply), 8):
                yield reply[i : i + 8]

        return _gen()

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [_hash_vector(t, self.dim) for t in texts]

    async def health_check(self) -> bool:
        return True
