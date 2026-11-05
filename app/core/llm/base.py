"""LLM 适配层抽象：所有业务代码只依赖此接口，不感知具体供应商。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence


class BaseLLM(ABC):
    """统一对话与向量化接口（OpenAI 兼容协议语义）。"""

    @abstractmethod
    async def chat(self, messages: list[dict], *, stream: bool = False) -> str | AsyncIterator[str]:
        """非流式返回完整文本；stream=True 返回增量文本的异步迭代器。"""

    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """批量向量化，返回与输入等长的向量列表。"""

    @abstractmethod
    async def health_check(self) -> bool:
        """供应商连通性探测（用于 /health 与启动自检）。"""
