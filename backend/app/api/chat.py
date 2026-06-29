"""
聊天API路由
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.core.persona_engine import PersonaEngine
from app.models.schemas import ChatRequest

router = APIRouter()
engine = PersonaEngine()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE流式聊天"""
    history_dict = [msg.model_dump() for msg in request.history]

    async def event_generator():
        async for chunk in engine.generate_stream(request.message, history_dict):
            yield chunk.model_dump()

    return EventSourceResponse(event_generator())


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "3.0.0",
        "mock_mode": True,  # 简化
    }
