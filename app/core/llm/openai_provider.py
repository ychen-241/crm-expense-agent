"""OpenAI 兼容协议实现：同样适用于 DashScope 兼容模式、DeepSeek、Moonshot 等。"""

import json
from collections.abc import AsyncIterator, Sequence

import httpx

from app.core.llm.base import BaseLLM


class OpenAICompatibleLLM(BaseLLM):
    def __init__(self, base_url: str, api_key: str, chat_model: str, embed_model: str):
        self.base_url = base_url.rstrip("/")
        self.chat_model = chat_model
        self.embed_model = embed_model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    async def chat(self, messages: list[dict], *, stream: bool = False) -> str | AsyncIterator[str]:
        if not stream:
            resp = await self._client.post(
                "/chat/completions",
                json={"model": self.chat_model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        return self._stream(messages)

    async def _stream(self, messages: list[dict]) -> AsyncIterator[str]:
        async with self._client.stream(
            "POST",
            "/chat/completions",
            json={"model": self.chat_model, "messages": messages, "stream": True},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                delta = json.loads(line[len("data: ") :])["choices"][0].get("delta", {})
                if content := delta.get("content"):
                    yield content

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        resp = await self._client.post(
            "/embeddings", json={"model": self.embed_model, "input": list(texts)}
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]

    async def health_check(self) -> bool:
        try:
            await self._client.get("/models")
            return True
        except httpx.HTTPError:
            return False
