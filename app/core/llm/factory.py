"""按配置实例化 LLM 供应商。换供应商 = 改 .env，不改代码。"""

from functools import lru_cache

from app.core.config import get_settings
from app.core.llm.base import BaseLLM
from app.core.llm.dashscope_provider import DashscopeLLM
from app.core.llm.mock_provider import MockLLM
from app.core.llm.openai_provider import OpenAICompatibleLLM


@lru_cache
def get_llm() -> BaseLLM:
    s = get_settings()
    if s.LLM_PROVIDER == "dashscope":
        return DashscopeLLM(api_key=s.LLM_API_KEY)
    if s.LLM_PROVIDER == "mock":
        return MockLLM()
    return OpenAICompatibleLLM(
        base_url=s.LLM_BASE_URL,
        api_key=s.LLM_API_KEY,
        chat_model=s.LLM_CHAT_MODEL,
        embed_model=s.LLM_EMBED_MODEL,
    )
