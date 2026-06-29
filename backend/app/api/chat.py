"""聊天API端点"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

from ..models.schemas import ChatRequest, ChatResponse, ChatChunk, HealthCheck
from ..services.kimi_client import get_kimi_client
from ..core.config import settings
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["chat"])

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE流式聊天接口
    
    返回事件流：
    - thinking_progress: 思考过程更新
    - content: 内容片段
    - done: 完成
    - error: 错误
    """
    client = get_kimi_client()
    
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
    
    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.post("/chat")
async def chat(request: ChatRequest):
    """非流式聊天接口（用于测试）"""
    client = get_kimi_client()
    
    full_content = ""
    thinking_steps = []
    
    try:
        async for chunk in client.stream_chat(
            user_message=request.message,
            history=request.history
        ):
            if chunk.type == "content" and chunk.data:
                full_content += chunk.data
            elif chunk.type == "thinking" and chunk.thinking_step:
                thinking_steps.append(chunk.thinking_step)
            elif chunk.type == "done" and chunk.final_message:
                full_content = chunk.final_message
        
        return ChatResponse(
            message=full_content,
            thinking_steps=thinking_steps,
            session_id=request.session_id or "default",
            model=settings.MOONSHOT_MODEL,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """健康检查"""
    return HealthCheck(
        status="ok",
        version=settings.APP_VERSION,
        mock_mode=settings.MOCK_MODE,
        model=settings.MOONSHOT_MODEL,
        timestamp=datetime.now().isoformat()
    )
