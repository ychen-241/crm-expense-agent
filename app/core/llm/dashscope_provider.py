"""DashScope（通义千问）兼容模式供应商：仅预设默认参数，逻辑复用 OpenAI 兼容实现。"""

from app.core.llm.openai_provider import OpenAICompatibleLLM

_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
_DEFAULT_CHAT_MODEL = "qwen-plus"
_DEFAULT_EMBED_MODEL = "text-embedding-v3"


class DashscopeLLM(OpenAICompatibleLLM):
    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        chat_model: str = _DEFAULT_CHAT_MODEL,
        embed_model: str = _DEFAULT_EMBED_MODEL,
    ):
        super().__init__(base_url, api_key, chat_model, embed_model)
