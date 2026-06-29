"""
数据模型定义
"""
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    stream: bool = True
    history: list[ChatMessage] = []


class ChatChunk(BaseModel):
    type: Literal["thinking_stream", "cognitive_structure", "mao_quote", "content", "done", "error"]
    data: Optional[str] = None
    thinking_step: Optional[Dict[str, Any]] = None
    overall_percentage: Optional[int] = None
