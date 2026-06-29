"""
LLM客户端
支持OpenAI兼容格式的API
Mock模式时生成基于教员的模拟响应
"""
import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any

from app.core.config import settings


class LLMClient:
    def __init__(self):
        self.api_key = settings.API_KEY
        self.base_url = settings.BASE_URL
        self.model = settings.MODEL
        self.temperature = settings.TEMPERATURE
        self.max_tokens = settings.MAX_TOKENS
        self.mock = settings.is_mock_mode()
        self._client = None

        if not self.mock:
            try:
                import openai
                self._client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
                print(f"✅ LLM客户端: {self.model}")
            except Exception as e:
                print(f"⚠️ API连接失败，启用Mock: {e}")
                self.mock = True

    async def stream(
        self,
        system_prompt: str,
        user_message: str,
        history: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[Dict[str, str], None]:
        """流式调用LLM"""
        if self.mock:
            async for chunk in self._mock_stream(system_prompt, user_message):
                yield chunk
            return

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for h in history[-5:]:  # 最近5轮
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta:
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        yield {"type": "reasoning", "content": delta.reasoning_content}
                    if delta.content:
                        yield {"type": "content", "content": delta.content}
        except Exception as e:
            yield {"type": "error", "content": str(e)}

    async def _mock_stream(
        self,
        system_prompt: str,
        user_message: str,
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Mock模式：模拟教员的思考流和回答"""
        # 思考流模拟
        thinking_parts = [
            "嗯，让小同志先说说情况...",
            "这个嘛，要抓主要矛盾...",
            "我记得以前写过...",
        ]

        for part in thinking_parts:
            yield {"type": "reasoning", "content": part}
            await asyncio.sleep(0.3)

        # 回答模拟
        mock_response = (
            "小同志，这个问题要一分为二地看。"
            "首先要调查研究，没有调查就没有发言权。"
            "抓住了主要矛盾，其他问题就好解决了。"
        )

        for char in mock_response:
            yield {"type": "content", "content": char}
            await asyncio.sleep(0.05)
