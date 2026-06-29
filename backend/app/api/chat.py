"""聊天API端点 v2.0 - 支持三层输出"""
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import json

from ..models.schemas import ChatRequest
from ..services.kimi_client_v2 import get_kimi_client_v2
from ..core.config import settings
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE流式聊天 - v2完整引擎
    
    返回事件类型:
    - thinking_stream: 思考流事件（内心独白）
    - cognitive_structure: 认知结构数据（思维导图）
    - mao_quote: 毛选原文引用
    - content: 回答内容片段
    - done: 完成
    - error: 错误
    """
    client = get_kimi_client_v2()
    
    async def event_generator():
        try:
            async for chunk in client.stream_chat(
                user_message=request.message,
                history=request.history
            ):
                yield {
                    "event": chunk.type,
                    "data": json.dumps(chunk.model_dump(exclude_none=True), ensure_ascii=False)
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}, ensure_ascii=False)
            }
    
    return EventSourceResponse(event_generator(), media_type="text/event-stream")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "mock_mode": settings.MOCK_MODE,
        "model": settings.MOONSHOT_MODEL,
        "timestamp": datetime.now().isoformat()
    }
