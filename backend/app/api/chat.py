"""
聊天API路由模块

提供：
1. POST /chat/stream - SSE流式聊天
2. GET /health - 健康检查
"""

import json
import sys
import traceback
from typing import AsyncGenerator, Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatRequest, ChatChunk, HealthResponse
from app.core.persona_engine import persona_engine
from app.core.config import settings

router = APIRouter(prefix="", tags=["chat"])


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> EventSourceResponse:
    """
    SSE流式聊天接口

    接收用户消息，返回教员的实时思考流和回答。

    **请求体：**
    - message: 用户消息（必填，1-4096字符）
    - history: 历史对话（可选，最多6轮）

    **SSE事件类型：**
    - thinking_stream: 教员实时思考流
    - cognitive_structure: 认知结构标记
    - mao_quote: 教员原文引用
    - content: 最终回答内容
    - done: 流结束标记
    - error: 错误信息

    **示例请求：**
    ```json
    {
        "message": "我现在遇到困难，压力很大",
        "history": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "小同志，你好！有什么问题？"}
        ]
    }
    ```
    """
    try:
        # 确保引擎已加载
        persona_engine.ensure_loaded()

        # 创建生成器（内部捕获异常，防止SSE连接异常断开）
        async def event_generator() -> AsyncGenerator[dict, None]:
            try:
                async for chunk in persona_engine.generate_stream(
                    query=request.message,
                    history=request.history,
                ):
                    # 统一转换为字典（兼容 ChatChunk Pydantic 对象和原生 dict）
                    if isinstance(chunk, ChatChunk):
                        chunk_dict = chunk.model_dump() if hasattr(chunk, "model_dump") else chunk.dict()
                    else:
                        chunk_dict = chunk
                    yield {
                        "event": chunk_dict.get("type", "content"),
                        "data": json.dumps(chunk_dict, ensure_ascii=False),
                    }
            except Exception as gen_exc:
                error_detail = f"流生成错误: {str(gen_exc)}"
                traceback_str = traceback.format_exc()
                print(traceback_str, file=sys.stderr)
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "type": "error",
                        "data": error_detail,
                        "overall_percentage": 0,
                    }, ensure_ascii=False),
                }

        return EventSourceResponse(
            event_generator(),
            media_type="text/event-stream",
        )

    except Exception as e:
        error_detail = f"处理请求时出错: {str(e)}"
        traceback_str = traceback.format_exc()
        print(traceback_str, file=sys.stderr)
        # 返回SSE格式的错误
        async def error_generator() -> AsyncGenerator[dict, None]:
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "error",
                    "data": error_detail,
                    "overall_percentage": 0,
                }, ensure_ascii=False),
            }

        return EventSourceResponse(
            error_generator(),
            media_type="text/event-stream",
        )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    健康检查接口

    返回引擎加载状态和数据统计。
    """
    try:
        persona_engine.ensure_loaded()
        stats = persona_engine.get_stats()
        return HealthResponse(
            status="ok",
            engine_loaded=True,
            chunks_count=stats["chunks_count"],
            signatures_count=stats["signatures_count"],
            mock_mode=settings.is_mock_mode(),
        )
    except Exception as e:
        return HealthResponse(
            status=f"error: {str(e)}",
            engine_loaded=False,
            chunks_count=0,
            signatures_count=0,
            mock_mode=settings.is_mock_mode(),
        )
