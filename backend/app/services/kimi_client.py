"""Kimi API客户端 - 支持kimi-k2.6推理模型的reasoning_content特性
优化：边收reasoning边推送thinking步骤，降低首token延迟
"""
import os
import json
import asyncio
from typing import AsyncGenerator, Optional, List
from openai import AsyncOpenAI, OpenAIError

from ..core.config import settings
from ..core.mao_system_prompt import get_full_system_prompt, get_thinking_steps
from ..core.mao_persona_v2 import (
    generate_system_prompt_v2,
    parse_reasoning_to_stream,
    extract_cognitive_nodes,
    match_quotes,
    CognitiveStructure, CognitiveNode,
)
from ..models.schemas import ChatMessage, ChatChunk, ThinkingStep

class KimiClient:
    """Kimi API客户端 - 适配kimi-k2.6推理模型"""
    
    def __init__(self):
        self.mock_mode = settings.MOCK_MODE
        self.model = settings.MOONSHOT_MODEL
        self.system_prompt = generate_system_prompt_v2()
        
        if not self.mock_mode:
            try:
                self.client = AsyncOpenAI(
                    api_key=settings.MOONSHOT_API_KEY,
                    base_url=settings.MOONSHOT_BASE_URL,
                    timeout=settings.REQUEST_TIMEOUT
                )
                print(f"✅ Kimi API客户端初始化成功 (模型: {self.model})")
            except Exception as e:
                print(f"⚠️ Kimi API初始化失败，切换到Mock模式: {e}")
                self.mock_mode = True
        
        if self.mock_mode:
            print("🎭 运行在Mock模式（模拟响应）")
    
    def _build_messages(self, user_message: str, history: Optional[List[ChatMessage]] = None) -> list:
        """构建消息列表"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            for msg in history[-10:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})
        return messages
    
    def _extract_step_from_reasoning(self, reasoning: str, step_idx: int) -> str:
        """从reasoning中提取指定步骤的内容"""
        steps_def = get_thinking_steps()
        if step_idx >= len(steps_def):
            return ""
        
        # 按段落分割
        paragraphs = [p.strip() for p in reasoning.split('\n') if p.strip()]
        if not paragraphs:
            return steps_def[step_idx]["description"]
        
        # 计算该步骤对应的段落范围
        start = int(step_idx * len(paragraphs) / 5)
        end = int((step_idx + 1) * len(paragraphs) / 5)
        step_paras = paragraphs[start:end]
        
        content = ' '.join(step_paras)
        if len(content) > 200:
            content = content[:200] + "..."
        
        return content if content else steps_def[step_idx]["description"]
    
    async def _mock_stream_response(self, user_message: str) -> AsyncGenerator[ChatChunk, None]:
        """Mock模式：模拟流式响应"""
        from ..core.mao_system_prompt import get_thinking_steps
        
        thinking_steps_def = get_thinking_steps()
        
        for i, step_def in enumerate(thinking_steps_def):
            step = ThinkingStep(
                id=step_def["id"],
                name=step_def["name"],
                description=step_def["description"],
                percentage=step_def["percentage"],
                mao_quote=step_def["mao_quote"],
                status="completed",
                content=self._generate_mock_thinking(step_def["id"], user_message)
            )
            yield ChatChunk(type="thinking", thinking_step=step, overall_percentage=step_def["percentage"])
            await asyncio.sleep(0.3)
        
        mock_response = self._generate_mock_response(user_message)
        buffer = ""
        for char in mock_response:
            buffer += char
            if len(buffer) >= settings.STREAM_CHUNK_SIZE:
                yield ChatChunk(type="content", data=buffer)
                buffer = ""
                await asyncio.sleep(settings.STREAM_DELAY_MS / 1000)
        
        if buffer:
            yield ChatChunk(type="content", data=buffer)
        yield ChatChunk(type="done", final_message=mock_response)
    
    def _generate_mock_thinking(self, step_id: str, user_message: str) -> str:
        thinkings = {
            "deconstruct": f"这个问题——'{user_message[:30]}...'属于什么性质？从实际出发分析。",
            "contradiction": "主要矛盾是什么？矛盾的主要方面在哪？",
            "deep_analysis": "有利条件和不利条件各是什么？",
            "strategy": "战略上藐视，战术上重视，找到突破口。",
            "conclusion": "本质是认识和实践的关系，在实践中检验。"
        }
        return thinkings.get(step_id, "正在思考...")
    
    def _generate_mock_response(self, user_message: str) -> str:
        message_lower = user_message.lower()
        
        if any(kw in message_lower for kw in ["困难", "难", "压力", "累", "苦"]):
            return """小同志，我们的同志在困难的时候，要看到成绩，要看到光明，要提高我们的勇气。

你说压力大，先要调查研究——是什么让你压力大？是任务太多？是方法不对？还是身体需要休息？

用矛盾分析法：这是你的主观能力和客观任务之间的矛盾。抓住了主要矛盾，问题就解决了一半。

星星之火，可以燎原。再大的困难，分解开来，一件一件解决。关键是实事求是，不要脱离实际。

没有调查就没有发言权。你把让你压力大的事情一条条写下来，分分类，看看哪些是主要的，哪些是次要的。"""
        
        elif any(kw in message_lower for kw in ["选择", "决定", "换", "辞职", "选", "迷茫"]):
            return """小同志，没有调查就没有发言权。你首先要调查研究——

你现在的情况，主要矛盾是什么？是这个选择本身的问题，还是你对问题认识不清？

用矛盾分析法：列出两种选择各自的有利条件和不利条件，一一对照。哪种选择能让主要矛盾朝着有利的方向转化？

关键是实事求是，从实际情况出发，不要凭主观想象做决定。道路是曲折的，前途是光明的。"""
        
        elif any(kw in message_lower for kw in ["批评", "被骂", "错", "失误"]):
            return """小同志，惩前毖后，治病救人嘛。批评是为了帮助，不是为了打击。

用矛盾分析法：批评的内容，哪些是对的？对的就接受。不对的也要想一想为什么会这样看。

有错误不怕，怕的是不承认错误，不改正错误。房子是应该经常打扫的，不打扫就会积满了灰尘。思想也是一样，经常打扫才能保持清醒。"""
        
        elif any(kw in message_lower for kw in ["学习", "读书", "进步", "成长", "提升"]):
            return """小同志，学习、学习、再学习！人的正确思想，只能从社会实践中来。

学习要同实际相结合。读书是学习，使用也是学习，而且是更重要的学习。

抓住主要矛盾——你最缺的是什么？是理论知识？是实践经验？还是方法论？学习要从感性认识上升到理性认识，再回到实践中去检验。"""
        
        else:
            return f"""小同志，你这个问题提得好。让我用实事求是的态度来分析一下。

你说'{user_message[:50]}'，没有调查就没有发言权嘛。

从矛盾论来看，任何问题都有主要矛盾和次要矛盾。关键是实事求是，从实际情况出发。

道路是曲折的，前途是光明的。不要被眼前的困难吓倒，办法总比困难多。"""
    
    async def stream_chat(self, user_message: str, history: Optional[List[ChatMessage]] = None) -> AsyncGenerator[ChatChunk, None]:
        """流式聊天 - 优化版：边收reasoning边推送thinking步骤"""
        if self.mock_mode:
            async for chunk in self._mock_stream_response(user_message):
                yield chunk
            return
        
        try:
            messages = self._build_messages(user_message, history)
            
            # 记录已推送的步骤，避免重复
            pushed_steps = set()
            reasoning_buffer = ""
            sentence_buffer = ""  # v2: sentence buffer
            stream_idx = 0  # v2: thinking stream index
            sent_quote_texts = set()  # v2: dedup quotes
            content_buffer = ""
            has_started_content = False
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                stream=True
            )
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                
                # 收集reasoning_content
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    reasoning_buffer += delta.reasoning_content

                    # ===== v2: 思考流事件（句子缓冲）=====
                    sentence_buffer += delta.reasoning_content
                    # 当遇到句子结束标记时，输出完整句子
                    while any(c in sentence_buffer for c in ['。', '！', '？', '\n', '.', '!', '?']):
                        end_idx = min((sentence_buffer.find(c) + 1 for c in ['。', '！', '？', '\n', '.', '!', '?'] if c in sentence_buffer), default=len(sentence_buffer))
                        sentence = sentence_buffer[:end_idx].strip()
                        sentence_buffer = sentence_buffer[end_idx:]
                        if len(sentence) > 5:
                            stream_events = parse_reasoning_to_stream(sentence)
                            for event in stream_events:
                                yield ChatChunk(
                                    type="thinking_stream", data=event["text"],
                                    thinking_step=ThinkingStep(
                                        id=f"ts_{stream_idx}", name=event["emotion"],
                                        description=event["text"][:40],
                                        percentage=min(50, int(len(reasoning_buffer)/20)),
                                        mao_quote="", status="active", content=event["text"]
                                    ),
                                    overall_percentage=min(50, int(len(reasoning_buffer)/20))
                                )
                                stream_idx += 1

                    # 🔥 关键优化：边收reasoning边尝试推送步骤
                    steps_def = get_thinking_steps()
                    total_steps = len(steps_def)
                    estimated_step = min(int(len(reasoning_buffer) / 250), total_steps - 1)

                    for i in range(estimated_step + 1):
                        if i in pushed_steps:
                            continue

                        step_def = steps_def[i]
                        step_content = self._extract_step_from_reasoning(reasoning_buffer, i)

                        step = ThinkingStep(
                            id=step_def["id"],
                            name=step_def["name"],
                            description=step_def["description"],
                            percentage=step_def["percentage"],
                            mao_quote=step_def["mao_quote"],
                            status="completed",
                            content=step_content
                        )

                        yield ChatChunk(
                            type="thinking",
                            thinking_step=step,
                            overall_percentage=step_def["percentage"]
                        )
                        pushed_steps.add(i)

                    # ===== v2: 认知结构 =====
                    if len(reasoning_buffer) > 300:
                        nodes = extract_cognitive_nodes(reasoning_buffer)
                        if nodes:
                            cog = CognitiveStructure()
                            for n in nodes:
                                cog.add_node(CognitiveNode(id=f"n{len(cog.nodes)}", node_type=n["type"], content=n["content"], confidence=0.7, status="forming"))
                            yield ChatChunk(
                                type="cognitive_structure", data="",
                                thinking_step=ThinkingStep(id="cog", name="认知结构", description="", percentage=60, mao_quote="", status="completed", content=str(cog.get_graph_data())),
                                overall_percentage=60
                            )

                    # ===== v2: 毛选引用（去重）=====
                    if len(reasoning_buffer) > 200:
                        quotes = match_quotes(reasoning_buffer, 2)
                        for q in quotes:
                            if q.text not in sent_quote_texts:
                                sent_quote_texts.add(q.text)
                                yield ChatChunk(
                                    type="mao_quote", data=f"{q.text} ——{q.source}（{q.date}）",
                                    thinking_step=ThinkingStep(id=f"q_{q.source}", name="毛选原文", description=f"{q.source}·{q.date}", percentage=70, mao_quote=q.text, status="completed", content=q.context),
                                    overall_percentage=70
                                )
                
                # 收集并推送content
                if delta.content:
                    if not has_started_content:
                        has_started_content = True
                        # 确保所有5个步骤都已推送
                        steps_def = get_thinking_steps()
                        for i in range(5):
                            if i not in pushed_steps:
                                step_def = steps_def[i]
                                step = ThinkingStep(
                                    id=step_def["id"],
                                    name=step_def["name"],
                                    description=step_def["description"],
                                    percentage=step_def["percentage"],
                                    mao_quote=step_def["mao_quote"],
                                    status="completed",
                                    content=self._extract_step_from_reasoning(reasoning_buffer, i)
                                )
                                yield ChatChunk(
                                    type="thinking",
                                    thinking_step=step,
                                    overall_percentage=step_def["percentage"]
                                )
                                pushed_steps.add(i)
                    
                    content_buffer += delta.content
                    yield ChatChunk(type="content", data=delta.content)
            
            yield ChatChunk(type="done", final_message=content_buffer)
            
        except OpenAIError as e:
            error_msg = f"API调用失败: {str(e)}"
            print(f"❌ {error_msg}")
            yield ChatChunk(type="error", error=error_msg)
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            print(f"❌ {error_msg}")
            yield ChatChunk(type="error", error=error_msg)

# 全局客户端实例
_kimi_client: Optional[KimiClient] = None

def get_kimi_client() -> KimiClient:
    """获取Kimi客户端单例"""
    global _kimi_client
    if _kimi_client is None:
        _kimi_client = KimiClient()
    return _kimi_client
