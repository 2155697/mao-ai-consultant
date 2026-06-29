"""Kimi API客户端 - 支持kimi-k2.6推理模型的reasoning_content特性"""
import os
import json
import asyncio
from typing import AsyncGenerator, Optional, List
from openai import AsyncOpenAI, OpenAIError

from ..core.config import settings
from ..core.mao_system_prompt import get_full_system_prompt, get_thinking_steps
from ..models.schemas import ChatMessage, ChatChunk, ThinkingStep

class KimiClient:
    """Kimi API客户端 - 适配kimi-k2.6推理模型"""
    
    def __init__(self):
        self.mock_mode = settings.MOCK_MODE
        self.model = settings.MOONSHOT_MODEL
        self.system_prompt = get_full_system_prompt()
        
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
    
    def _parse_reasoning_to_steps(self, reasoning: str) -> List[ThinkingStep]:
        """将模型的reasoning_content解析为5步思考链"""
        steps_def = get_thinking_steps()
        steps = []
        
        # 按段落分割reasoning
        paragraphs = [p.strip() for p in reasoning.split('\n') if p.strip()]
        
        for i, step_def in enumerate(steps_def):
            # 为每个步骤分配对应的reasoning段落
            start_idx = int(i * len(paragraphs) / 5)
            end_idx = int((i + 1) * len(paragraphs) / 5)
            step_content = '\n'.join(paragraphs[start_idx:end_idx]) if paragraphs else step_def["description"]
            
            # 截断过长的内容
            if len(step_content) > 200:
                step_content = step_content[:200] + "..."
            
            steps.append(ThinkingStep(
                id=step_def["id"],
                name=step_def["name"],
                description=step_def["description"],
                percentage=step_def["percentage"],
                mao_quote=step_def["mao_quote"],
                status="completed",
                content=step_content if step_content else step_def["description"]
            ))
        
        return steps
    
    async def _mock_stream_response(self, user_message: str) -> AsyncGenerator[ChatChunk, None]:
        """Mock模式：模拟流式响应"""
        from ..core.mao_system_prompt import get_thinking_steps
        
        thinking_steps_def = get_thinking_steps()
        
        # 阶段1：思考过程
        for i, step_def in enumerate(thinking_steps_def):
            step = ThinkingStep(
                id=step_def["id"],
                name=step_def["name"],
                description=step_def["description"],
                percentage=step_def["percentage"],
                mao_quote=step_def["mao_quote"],
                status="completed"
            )
            step.content = self._generate_mock_thinking(step_def["id"], user_message)
            
            yield ChatChunk(
                type="thinking",
                thinking_step=step,
                overall_percentage=step_def["percentage"]
            )
            await asyncio.sleep(0.5)
        
        # 阶段2：生成回答
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
            "deconstruct": f"让我先看看这个问题——'{user_message[:30]}...'这属于什么问题？从性质上看，这是关于实际工作中遇到的具体矛盾。",
            "contradiction": "这里面的主要矛盾是什么？是主观愿望和客观条件之间的矛盾，还是方法论问题？矛盾的主要方面在哪里？",
            "deep_analysis": "从实际情况出发，有利条件是——当事人有改变的意愿；不利条件是——可能缺乏经验或方法。要具体问题具体分析。",
            "strategy": "战略上要藐视困难，相信问题一定能解决；战术上要重视困难，一步一步来，调查研究，找到具体方法。",
            "conclusion": "本质是认识和实践的关系问题。要在实践中检验，在实践中调整，在实践中成长。"
        }
        return thinkings.get(step_id, "正在深入思考...")
    
    def _generate_mock_response(self, user_message: str) -> str:
        message_lower = user_message.lower()
        
        if any(kw in message_lower for kw in ["困难", "难", "压力", "累", "苦"]):
            return """小同志，我们的同志在困难的时候，要看到成绩，要看到光明，要提高我们的勇气。

你说压力大，这个问题先要调查研究——是什么让你压力大？是任务太多？是方法不对？还是身体需要休息？

用矛盾分析法来看，这是你的主观能力和客观任务之间的矛盾。主要矛盾是什么？如果是任务和能力不匹配，那就分析：哪些任务可以分解，哪些可以求助，哪些需要学习新方法来提高效率。

记住，星星之火，可以燎原。再大的困难，分解开来，一件一件解决，总能找到出路。关键是不要脱离实际，要实事求是。

没有调查就没有发言权。你先做个"调查"——把让你压力大的事情一条条写下来，分分类，看看哪些是主要的，哪些是次要的。抓住了主要矛盾，问题就解决了一半。"""
        
        elif any(kw in message_lower for kw in ["选择", "决定", "换", "辞职", "选"]):
            return """小同志，没有调查就没有发言权。你首先要调查研究——

你现在的情况，主要矛盾是什么？是这个选择本身的问题，还是你对问题认识不清的问题？

要用矛盾分析法：列出两种选择各自的有利条件和不利条件，一一对照。看看哪种选择能让主要矛盾朝着有利的方向转化。

关键是实事求是，从实际情况出发，不要凭主观想象做决定。"""
        
        elif any(kw in message_lower for kw in ["批评", "被骂", "错", "失误"]):
            return """小同志，惩前毖后，治病救人嘛。批评是为了帮助，不是为了打击。

有错误不怕，怕的是不承认错误，不改正错误。房子是应该经常打扫的，不打扫就会积满了灰尘。思想也是一样，经常打扫打扫，才能保持清醒。"""
        
        elif any(kw in message_lower for kw in ["学习", "读书", "进步", "成长", "提升"]):
            return """小同志，学习、学习、再学习！人的正确思想，只能从社会实践中来。

学习要同实际相结合。读书是学习，使用也是学习，而且是更重要的学习。

你现在的学习，要抓住主要矛盾——你最缺的是什么？是理论知识？是实践经验？还是方法论？"""
        
        else:
            return f"""小同志，你这个问题提得好。让我用实事求是的态度来分析一下。

你说'{user_message[:50]}'，这个问题首先我要调查研究清楚。没有调查就没有发言权嘛。

从矛盾论的角度来看，任何问题都有它的主要矛盾和次要矛盾。关键是实事求是，从实际情况出发。

道路是曲折的，前途是光明的。小同志，不要被眼前的困难吓倒，办法总比困难多。"""
    
    async def stream_chat(self, user_message: str, history: Optional[List[ChatMessage]] = None) -> AsyncGenerator[ChatChunk, None]:
        """流式聊天 - 利用kimi-k2.6的reasoning_content展示思考过程"""
        if self.mock_mode:
            async for chunk in self._mock_stream_response(user_message):
                yield chunk
            return
        
        # 真实API调用
        try:
            messages = self._build_messages(user_message, history)
            
            reasoning_buffer = ""
            content_buffer = ""
            has_sent_thinking = False
            
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
                
                # 收集reasoning_content（思考过程）
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    reasoning_buffer += delta.reasoning_content
                
                # 收集content（最终回答）
                if delta.content:
                    # 当content开始时，说明reasoning结束了，发送思考步骤
                    if not has_sent_thinking and reasoning_buffer:
                        has_sent_thinking = True
                        thinking_steps = self._parse_reasoning_to_steps(reasoning_buffer)
                        for step in thinking_steps:
                            yield ChatChunk(
                                type="thinking",
                                thinking_step=step,
                                overall_percentage=step.percentage
                            )
                    
                    content_buffer += delta.content
                    yield ChatChunk(type="content", data=delta.content)
            
            # 如果只有reasoning没有content（模型把所有token都用在了思考上）
            if not has_sent_thinking and reasoning_buffer:
                thinking_steps = self._parse_reasoning_to_steps(reasoning_buffer)
                for step in thinking_steps:
                    yield ChatChunk(
                        type="thinking",
                        thinking_step=step,
                        overall_percentage=step.percentage
                    )
            
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
