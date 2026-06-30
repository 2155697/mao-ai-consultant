"""
Kimi API客户端 v2.0 - 人格蒸馏完整引擎
三层输出：思考流 + 认知结构 + 毛选原文
"""
import os
import json
import asyncio
from typing import AsyncGenerator, Optional, List

from ..core.config import settings
from ..core.mao_persona_v2 import (
    generate_system_prompt_v2,
    parse_reasoning_to_stream,
    extract_cognitive_nodes,
    match_quotes,
    CognitiveStructure,
    CognitiveNode,
)
from ..models.schemas import ChatMessage, ChatChunk, ThinkingStep

# 延迟导入openai
_openai_module = None
def _get_openai():
    global _openai_module
    if _openai_module is None:
        import openai
        _openai_module = openai
    return _openai_module

class KimiClientV2:
    """Kimi API客户端 v2 - 完整人格蒸馏引擎"""
    
    def __init__(self):
        self.mock_mode = settings.MOCK_MODE
        self.model = settings.MOONSHOT_MODEL
        self.system_prompt = generate_system_prompt_v2()
        self._client = None
        
        # 检查API key是否配置
        if not settings.MOONSHOT_API_KEY or settings.MOONSHOT_API_KEY == "":
            print("⚠️ API Key未配置，请设置环境变量MOONSHOT_API_KEY")
            print("   当前使用Mock模式（模拟响应）")
            self.mock_mode = True
            return
        
        if not self.mock_mode:
            try:
                openai = _get_openai()
                self._client = openai.AsyncOpenAI(
                    api_key=settings.MOONSHOT_API_KEY,
                    base_url=settings.MOONSHOT_BASE_URL,
                    timeout=settings.REQUEST_TIMEOUT
                )
                print(f"✅ API client: {self.model}")
            except Exception as e:
                print(f"⚠️ API fail, using mock: {e}")
                self.mock_mode = True
    
    def _build_messages(self, user_message: str, history: Optional[List[ChatMessage]] = None) -> list:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            for msg in history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})
        return messages
    
    async def _mock_stream(self, user_message: str) -> AsyncGenerator[ChatChunk, None]:
        """Mock模式"""
        mock_reasoning = f"让我想想...小同志问的是{user_message[:20]}...\n这个问题的主要矛盾是什么？\n对了，关键在于...\n本质是主观和客观之间的矛盾。"
        
        stream_events = parse_reasoning_to_stream(mock_reasoning)
        for event in stream_events:
            yield ChatChunk(
                type="thinking_stream",
                data=event["text"],
                thinking_step=ThinkingStep(
                    id=f"ts_{len(event['text'])}",
                    name=event["emotion"],
                    description=event["text"][:40],
                    percentage=25, mao_quote="", status="active",
                    content=event["text"]
                ),
                overall_percentage=25
            )
            await asyncio.sleep(0.3)
        
        # 认知结构
        cog = CognitiveStructure()
        cog.add_node(CognitiveNode(id="root", node_type="insight", content=f"问题：{user_message[:30]}", confidence=0.8, status="confirmed"))
        cog.add_node(CognitiveNode(id="mc", node_type="main_contradiction", content="主要矛盾：主观vs客观", confidence=0.9, status="confirmed", connections=["root"]))
        yield ChatChunk(
            type="cognitive_structure",
            data="",
            thinking_step=ThinkingStep(id="cog", name="认知结构", description="", percentage=60, mao_quote="", status="completed", content=json.dumps(cog.get_graph_data(), ensure_ascii=False)),
            overall_percentage=60
        )
        
        # 毛选引用
        quotes = match_quotes(mock_reasoning, 2)
        for q in quotes:
            yield ChatChunk(
                type="mao_quote",
                data=f"{q.text} ——{q.source}（{q.date}）",
                thinking_step=ThinkingStep(id=f"q_{q.source}", name="毛选原文", description=f"{q.source}·{q.date}", percentage=70, mao_quote=q.text, status="completed", content=q.context),
                overall_percentage=70
            )
        
        # 回答
        mock_answer = self._generate_mock_answer(user_message)
        for char in mock_answer:
            yield ChatChunk(type="content", data=char)
            await asyncio.sleep(0.02)
        yield ChatChunk(type="done", final_message=mock_answer)
    
    def _generate_mock_answer(self, msg: str) -> str:
        msg_l = msg.lower()
        if any(k in msg_l for k in ["困难","压力","累"]):
            return "小同志，我们的同志在困难的时候，要看到成绩，要看到光明，要提高我们的勇气。你说压力大，先要调查研究——是什么让你压力大？抓住了主要矛盾，问题就解决了一半。"
        elif any(k in msg_l for k in ["迷茫","选择","换"]):
            return "小同志，没有调查就没有发言权。你首先要调查研究——用矛盾分析法，列出利弊，实事求是。道路是曲折的，前途是光明的。"
        elif any(k in msg_l for k in ["批评","错"]):
            return "小同志，惩前毖后，治病救人嘛。有错误不怕，怕的是不承认。房子应该经常打扫，思想也要经常打扫。"
        elif any(k in msg_l for k in ["学习","读书"]):
            return "小同志，学习、学习、再学习！人的正确思想只能从实践中来。读书是学习，使用也是学习，而且是更重要的学习。"
        return f"小同志，你这个问题提得好。'{msg[:30]}...'没有调查就没有发言权嘛。关键是实事求是。道路是曲折的，前途是光明的。"
    
    # P1 Fix #7: 句子分隔符
    _SENTENCE_ENDS = ('。', '！', '？', '\n', '；', '.', '!', '?')
    
    async def stream_chat(self, user_message: str, history: Optional[List[ChatMessage]] = None) -> AsyncGenerator[ChatChunk, None]:
        """流式聊天 - v2完整引擎（含动态更新 + 句子缓冲）"""
        if self.mock_mode or not self._client:
            async for chunk in self._mock_stream(user_message):
                yield chunk
            return
        
        try:
            messages = self._build_messages(user_message, history)
            reasoning_buffer = ""
            sentence_buffer = ""  # P1 Fix #7: 句子缓冲
            content_buffer = ""
            last_structure_len = 0   # P1 Fix #5: 上次发送认知结构时的buffer长度
            last_quotes_len = 0      # P1 Fix #6: 上次发送毛选时的buffer长度
            stream_idx = 0
            sent_quote_texts = set() # 去重
            
            stream = await self._client.chat.completions.create(
                model=self.model, messages=messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS, stream=True
            )
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta: continue
                
                # === P1 Fix #7: 句子缓冲解析思考流 ===
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    reasoning_buffer += delta.reasoning_content
                    sentence_buffer += delta.reasoning_content
                    
                    # 提取完整句子后解析（避免截断）
                    while True:
                        end_idx = -1
                        for sep in self._SENTENCE_ENDS:
                            idx = sentence_buffer.find(sep)
                            if idx >= 0 and (end_idx < 0 or idx < end_idx):
                                end_idx = idx
                        if end_idx < 0:
                            break
                        
                        sentence = sentence_buffer[:end_idx + 1].strip()
                        sentence_buffer = sentence_buffer[end_idx + 1:]
                        
                        if sentence:
                            stream_events = parse_reasoning_to_stream(sentence)
                            for event in stream_events:
                                yield ChatChunk(
                                    type="thinking_stream", data=event["text"],
                                    thinking_step=ThinkingStep(
                                        id=f"ts_{stream_idx}", name=event["emotion"],
                                        description=event["text"][:40],
                                        percentage=min(50, int(len(reasoning_buffer) / 20)),
                                        mao_quote="",
                                        status="completed" if event.get("is_revert") else "active",
                                        content=event["text"]
                                    ),
                                    overall_percentage=min(50, int(len(reasoning_buffer) / 20))
                                )
                                stream_idx += 1
                    
                    # P1 Fix #5: 认知结构动态更新（每新增150字符重新提取）
                    if len(reasoning_buffer) - last_structure_len >= 150:
                        last_structure_len = len(reasoning_buffer)
                        nodes = extract_cognitive_nodes(reasoning_buffer)
                        if nodes:
                            cog = CognitiveStructure()
                            for n in nodes:
                                cog.add_node(CognitiveNode(
                                    id=f"n{len(cog.nodes)}",
                                    node_type=n["type"],
                                    content=n["content"],
                                    confidence=0.7,
                                    status="forming"
                                ))
                            yield ChatChunk(
                                type="cognitive_structure", data="",
                                thinking_step=ThinkingStep(
                                    id="cog", name="认知结构", description="",
                                    percentage=60, mao_quote="", status="completed",
                                    content=json.dumps(cog.get_graph_data(), ensure_ascii=False)
                                ),
                                overall_percentage=60
                            )
                    
                    # P1 Fix #6: 毛选引用动态匹配（每新增100字符重新匹配）
                    if len(reasoning_buffer) - last_quotes_len >= 100:
                        last_quotes_len = len(reasoning_buffer)
                        quotes = match_quotes(reasoning_buffer, 2)
                        for q in quotes:
                            if q.text not in sent_quote_texts:
                                sent_quote_texts.add(q.text)
                                yield ChatChunk(
                                    type="mao_quote",
                                    data=f"{q.text} ——{q.source}（{q.date}）",
                                    thinking_step=ThinkingStep(
                                        id=f"q_{q.source}", name="毛选原文",
                                        description=f"{q.source}·{q.date}",
                                        percentage=70, mao_quote=q.text,
                                        status="completed", content=q.context
                                    ),
                                    overall_percentage=70
                                )
                
                # 内容输出
                if hasattr(delta, 'content') and delta.content:
                    content_buffer += delta.content
                    yield ChatChunk(
                        type="content", data=delta.content,
                        overall_percentage=50 + min(50, int(len(content_buffer) / 10))
                    )
            
            # 最终认知结构
            nodes = extract_cognitive_nodes(reasoning_buffer)
            if nodes:
                cog = CognitiveStructure()
                for n in nodes:
                    cog.add_node(CognitiveNode(
                        id=f"n_final_{len(cog.nodes)}",
                        node_type=n["type"], content=n["content"],
                        confidence=0.9, status="confirmed"
                    ))
                yield ChatChunk(
                    type="cognitive_structure", data="",
                    thinking_step=ThinkingStep(
                        id="cog_final", name="认知结构", description="最终",
                        percentage=90, mao_quote="", status="completed",
                        content=json.dumps(cog.get_graph_data(), ensure_ascii=False)
                    ),
                    overall_percentage=90
                )
            
            # 最终毛选引用
            quotes = match_quotes(reasoning_buffer + "\n" + content_buffer, 3)
            for q in quotes:
                if q.text not in sent_quote_texts:
                    sent_quote_texts.add(q.text)
                    yield ChatChunk(
                        type="mao_quote",
                        data=f"{q.text} ——{q.source}（{q.date}）",
                        thinking_step=ThinkingStep(
                            id=f"q_final_{q.source}", name="毛选原文",
                            description=f"{q.source}·{q.date}",
                            percentage=95, mao_quote=q.text,
                            status="completed", content=q.context
                        ),
                        overall_percentage=95
                    )
            
            yield ChatChunk(type="done", final_message=content_buffer)
            
        except Exception as e:
            yield ChatChunk(
                type="error",
                data=f"请求失败: {str(e)}",
                thinking_step=ThinkingStep(
                    id="error", name="错误", description=str(e)[:40],
                    percentage=0, mao_quote="", status="completed", content=str(e)
                )
            )

def get_kimi_client_v2():
    """获取KimiClientV2实例（单例）"""
    return KimiClientV2()
