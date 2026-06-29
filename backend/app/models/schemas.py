"""数据模型定义"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

class ThinkingStep(BaseModel):
    """单个思考步骤"""
    id: str
    name: str
    description: str
    percentage: int = Field(ge=0, le=100)
    mao_quote: str
    status: Literal["pending", "active", "completed"] = "pending"
    content: Optional[str] = None  # 该步骤的具体思考内容
    timestamp: Optional[str] = None

class ChatMessage(BaseModel):
    """聊天消息"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    stream: bool = Field(default=True, description="是否流式输出")
    show_thinking: bool = Field(default=True, description="是否展示思考过程")
    history: Optional[List[ChatMessage]] = Field(default=[], description="历史消息")

class ThinkingProgress(BaseModel):
    """思考进度更新"""
    type: Literal["thinking_progress"] = "thinking_progress"
    step: ThinkingStep
    overall_percentage: int = Field(ge=0, le=100)
    status: Literal["thinking", "writing", "done"] = "thinking"

class ChatChunk(BaseModel):
    """流式输出块"""
    type: Literal["thinking", "thinking_stream", "cognitive_structure", "mao_quote", "content", "done", "error"] = "content"
    data: Optional[str] = None
    thinking_step: Optional[ThinkingStep] = None
    overall_percentage: Optional[int] = None
    final_message: Optional[str] = None
    error: Optional[str] = None

class ChatResponse(BaseModel):
    """完整聊天响应"""
    message: str
    thinking_steps: List[ThinkingStep] = []
    thinking_text: Optional[str] = None  # 原始思考过程文本
    session_id: str
    tokens_used: Optional[int] = None
    model: str
    timestamp: str

class HealthCheck(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    mock_mode: bool
    model: str
    timestamp: str
