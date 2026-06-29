"""
PersonaEngine - 教员AI核心引擎

负责RAG检索、认知签名匹配、动态Prompt构建和流式输出生成。
是整个系统的智能中枢。
"""

import json
import random
import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, AsyncGenerator

import yaml

from app.core.config import settings


class PersonaEngine:
    """
    教员人格引擎 - 基于毛选98万字原文极致蒸馏

    四层架构：
    Layer 1: 原文层 (3,571 chunks + 4,560关键词倒排索引)
    Layer 2: 概念层 (661概念 + 2,238共现关系)
    Layer 3: Persona层 (12维度人格画像)
    Layer 4: Prompt层 (CharLoRA双层架构 + PCL自检)
    """

    # 现代词汇 → 毛选核心概念 映射表
    QUERY_EXPANSION = {
        "压力": "困难", "焦虑": "困难", "紧张": "困难", "累": "艰苦",
        "迷茫": "认识", "困惑": "问题", "纠结": "矛盾", "犹豫": "选择",
        "自卑": "错误", "怀疑": "经验", "恐惧": "敌人", "担心": "危险",
        "沮丧": "失败", "失落": "损失", "孤独": "群众", "无助": "依靠",
        "愤怒": "斗争", "不满": "批评", "抱怨": "缺点", "逃避": "逃跑",
        "拖延": "懒", "懒惰": "懒", "懈怠": "松懈", "放松": "休息",
        "骄傲": "自满", "得意": "胜利", "兴奋": "热情", "开心": "高兴",
        "难过": "痛苦", "伤心": "痛苦", "失望": "失败", "绝望": "灭亡",
        "工作": "工作", "职场": "工作", "公司": "组织", "老板": "领导",
        "同事": "同志", "团队": "队伍", "项目": "任务", "加班": "劳动",
        "辞职": "离开", "跳槽": "转移", "面试": "考察", "简历": "介绍",
        "升职": "提拔", "降职": "降级", "加薪": "增加", "降薪": "减少",
        "失业": "失业", "找工作": "就业", "创业": "事业", "投资": "投入",
        "赚钱": "生产", "亏钱": "损失", "买房": "住房", "租房": "借住",
        "结婚": "婚姻", "离婚": "分离", "恋爱": "友谊", "分手": "决裂",
        "家庭": "家庭", "父母": "父母", "孩子": "儿童", "教育": "教育",
        "学习": "学习", "考试": "测验", "读书": "阅读", "学校": "学校",
        "老师": "教员", "学生": "学员", "专业": "专门", "技能": "本领",
        "知识": "知识", "理论": "理论", "实践": "实践", "经验": "经验",
        "方法": "方法", "技巧": "技术", "策略": "策略", "计划": "计划",
        "目标": "目的", "理想": "理想", "梦想": "理想", "追求": "争取",
        "成功": "胜利", "失败": "失败", "进步": "前进", "退步": "落后",
        "改变": "变化", "坚持": "坚持", "放弃": "投降", "努力": "奋斗",
        "奋斗": "斗争", "拼搏": "战斗", "竞争": "战争", "合作": "联合",
        "沟通": "联系", "交流": "交换", "理解": "了解", "信任": "相信",
        "尊重": "尊敬", "公平": "平等", "正义": "正义", "自由": "自由",
        "平等": "平等", "民主": "民主", "法治": "法制", "权利": "权力",
        "责任": "责任", "义务": "任务", "道德": "品德", "修养": "修养",
        "健康": "健康", "生病": "疾病", "锻炼": "运动", "休息": "休养",
        "饮食": "食物", "睡眠": "睡觉", "习惯": "习惯", "生活": "生活",
        "幸福": "幸福", "快乐": "愉快", "满足": "满意", "感恩": "感谢",
        "善良": "好心", "诚实": "老实", "勇敢": "勇气", "坚强": "坚定",
        "智慧": "聪明", "聪明": "聪明", "才华": "才能", "能力": "本领",
        "优势": "长处", "劣势": "短处", "机会": "时机", "威胁": "危险",
        "风险": "危险", "挑战": "挑战", "危机": "危险", "机遇": "时机",
        "意义": "意义", "价值": "价值", "本质": "本质", "现象": "现象",
        "原因": "原因", "结果": "结果", "过程": "过程", "规律": "法则",
        "真理": "真理", "错误": "错误", "相对": "相对", "绝对": "绝对",
        "主观": "主观", "客观": "客观", "具体": "具体", "抽象": "抽象",
        "全面": "全面", "片面": "片面", "深入": "深入", "表面": "表面",
        "长期": "长久", "短期": "暂时", "未来": "将来", "过去": "以前",
        "现在": "现在", "当时": "当时", "时代": "时期", "历史": "历史",
        "传统": "传统", "创新": "创造", "改革": "改造", "革命": "革命",
        "发展": "发展", "增长": "增加", "减少": "减少", "稳定": "巩固",
        "平衡": "均衡", "协调": "配合", "统一": "统一", "分裂": "分裂",
        "集中": "集中", "分散": "分散", "整体": "全体", "局部": "部分",
        "系统": "体系", "结构": "结构", "功能": "作用", "效率": "效率",
        "质量": "质量", "数量": "数量", "规模": "规模", "速度": "速度",
        "方向": "方向", "道路": "路线", "路线": "路线", "方针": "方针",
        "政策": "政策", "路线": "路线", "纲领": "纲领", "口号": "口号",
        "思想": "思想", "意识": "意识", "观念": "观点", "认识": "认识",
        "看法": "意见", "态度": "态度", "立场": "立场", "观点": "观点",
    }

    def __init__(self) -> None:
        self.chunks: List[Dict[str, Any]] = []
        self.inverted_index: Dict[str, List[str]] = {}
        self.concept_network: Dict[str, Any] = {}
        self.signatures: List[Dict[str, Any]] = []
        self.persona: Dict[str, Any] = {}
        self._cooccurrence_cache: Dict[str, Dict[str, int]] = {}
        self._loaded: bool = False
        self.load_all()

    def load_all(self) -> None:
        self._load_knowledge_base()
        self._load_concept_network()
        self._load_signatures()
        self._load_persona()
        self._loaded = True

    def _load_knowledge_base(self) -> None:
        try:
            with open(settings.KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                kb = json.load(f)
            self.chunks = kb.get("chunks", [])
            self.inverted_index = kb.get("inverted_index", {})
        except Exception as e:
            raise RuntimeError(f"加载知识库失败: {e}") from e

    def _load_concept_network(self) -> None:
        try:
            with open(settings.CONCEPT_NETWORK_PATH, "r", encoding="utf-8") as f:
                self.concept_network = json.load(f)
            self._cooccurrence_cache = self.concept_network.get("cooccurrence", {})
        except Exception as e:
            raise RuntimeError(f"加载概念网络失败: {e}") from e

    def _load_signatures(self) -> None:
        try:
            with open(settings.SIGNATURES_PATH, "r", encoding="utf-8") as f:
                self.signatures = json.load(f)
        except Exception as e:
            raise RuntimeError(f"加载认知签名失败: {e}") from e

    def _load_persona(self) -> None:
        try:
            with open(settings.PERSONA_PATH, "r", encoding="utf-8") as f:
                raw_content = f.read()
            try:
                self.persona = yaml.safe_load(raw_content)
            except yaml.YAMLError:
                fixed = raw_content.replace('\u201c', '"').replace('\u201d', '"')
                fixed = fixed.replace('\u2018', "'").replace('\u2019', "'")
                try:
                    self.persona = yaml.safe_load(fixed)
                except yaml.YAMLError:
                    self.persona = self._fallback_persona()
        except Exception as e:
            raise RuntimeError(f"加载人格画像失败: {e}") from e

    def _fallback_persona(self) -> dict:
        return {
            "identity": {"name": "教员", "full_name": "毛泽东", "era": "1893-1976"},
            "tone": {"warmth": 0.85, "sharpness": 0.75, "dialectical": 0.95},
            "mood": {"optimism": 0.95, "dialectics": 0.95, "determination": 0.95},
            "key_phrases": {
                "greetings": "小同志，你遇到什么问题，说来听听。",
                "investigation": "没有调查就没有发言权",
                "contradiction": "要抓住主要矛盾",
            },
        }

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_all()

    def _segment_query(self, query: str) -> List[str]:
        return query.split()

    def _extract_query_keywords(self, query: str) -> List[str]:
        query_lower = query.lower()
        matched: List[str] = []
        for keyword in self.inverted_index:
            if keyword in query_lower:
                matched.append(keyword)
        for modern_word, mao_concept in self.QUERY_EXPANSION.items():
            if modern_word in query_lower and mao_concept not in matched:
                if mao_concept in self.inverted_index:
                    matched.append(mao_concept)
        return matched

    def _expand_concepts(self, concepts: List[str]) -> List[str]:
        expanded = set(concepts)
        for concept in concepts:
            if concept in self._cooccurrence_cache:
                related = self._cooccurrence_cache[concept]
                sorted_related = sorted(related.items(), key=lambda x: x[1], reverse=True)
                for rel_concept, _ in sorted_related[:3]:
                    expanded.add(rel_concept)
        return list(expanded)

    def rag_retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        self.ensure_loaded()
        keywords = self._extract_query_keywords(query)
        if not keywords:
            return []
        expanded_keywords = self._expand_concepts(keywords)
        candidate_scores: Dict[str, float] = {}
        for keyword in expanded_keywords:
            chunk_ids = self.inverted_index.get(keyword, [])
            for chunk_id in chunk_ids:
                score_boost = 2.0 if keyword in keywords else 0.5
                candidate_scores[chunk_id] = candidate_scores.get(chunk_id, 0) + score_boost
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for chunk_id, score in sorted_candidates[:top_k]:
            chunk = self._get_chunk_by_id(chunk_id)
            if chunk:
                chunk_copy = chunk.copy()
                chunk_copy["score"] = score
                results.append(chunk_copy)
        return results

    def _get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        for chunk in self.chunks:
            if chunk.get("id") == chunk_id:
                return chunk
        return None

    def signature_match(self, query: str) -> Optional[Dict[str, Any]]:
        self.ensure_loaded()
        query_lower = query.lower()
        query_words = set(self._segment_query(query_lower))
        expanded_query = query_lower
        for modern_word, mao_concept in self.QUERY_EXPANSION.items():
            if modern_word in query_lower:
                expanded_query += " " + mao_concept
                query_words.add(mao_concept)
        best_match = None
        best_score = 0.0
        for sig in self.signatures:
            triggers = sig.get("trigger_keywords", [])
            if not triggers:
                continue
            matched = [t for t in triggers if t.lower() in expanded_query]
            trigger_words = set()
            for t in triggers:
                trigger_words.update(self._segment_query(t.lower()))
            word_matches = query_words & trigger_words
            score = len(matched) * 1.0 + len(word_matches) * 0.3
            coverage = (len(matched) + len(word_matches)) / (len(triggers) + len(trigger_words) + 0.1)
            final_score = score * coverage * sig.get("confidence", 0.5)
            threshold = min(settings.SIGNATURE_MATCH_THRESHOLD, 0.15)
            if final_score > best_score and coverage >= threshold:
                best_score = final_score
                best_match = {
                    "name": sig["name"],
                    "confidence": round(sig.get("confidence", 0.0), 3),
                    "matched_keywords": matched,
                    "cognitive_response": sig.get("cognitive_response", ""),
                    "emotional_response": sig.get("emotional_response", ""),
                    "action_response": sig.get("action_response", ""),
                    "core_quotes": sig.get("core_quotes", []),
                }
        return best_match

    def build_system_prompt(self, query: str) -> str:
        self.ensure_loaded()
        rag_results = self.rag_retrieve(query, top_k=3)
        signature = self.signature_match(query)
        persona_key_phrases = self.persona.get("key_phrases", {})
        if isinstance(persona_key_phrases, dict):
            greeting = persona_key_phrases.get("greetings", "小同志，你遇到什么问题，说来听听。")
        else:
            greeting = "小同志，你遇到什么问题，说来听听。"
        thinking_habits = self.persona.get("thinking_habits", {})
        if isinstance(thinking_habits, dict):
            default_response = "调查研究，抓主要矛盾"
            first_reaction = thinking_habits.get("first_reaction_to_difficulty", default_response)
        else:
            first_reaction = "调查研究，抓主要矛盾"
        prompt = f"""你是教员，一名基于毛选98万字原文极致蒸馏的AI人格。

核心身份：
- 农民的儿子，人民的领袖
- 思维特征：矛盾分析法 + 群众路线 + 实践认识论
- 语言风格：温暖而锐利，宏大而具体，善用比喻

开场白："{greeting}"

思维本能（if-then签名）：
- 小同志说困难/压力大 → 本能地帮他抓主要矛盾，同时鼓舞信心
- 小同志说迷茫/不知道怎么办 → 本能地说没有调查就没有发言权
- 小同志被批评了 → 本能地惩前毖后治病救人
- 小同志想学习 → 本能地引导他从实践中学
- 小同志骄傲自满 → 本能地提醒虚心使人进步
- 小同志情绪低落 → 本能地告诉他事物是一分为二的
- 小同志自我怀疑 → 本能地鼓励他在战略上藐视困难
- 小同志问团队 → 本能地说从群众中来到群众中去
- 小同志面对竞争 → 本能地说你打你的我打我的
- 小同志问哲学 → 本能地用矛盾论深入浅出讲解

回应风格：
1. 称呼对方为"小同志"
2. 用具体案例说明抽象道理
3. 从实际问题出发，不空泛说教
4. 体现辩证思维，看到两面性
5. 结尾给出希望和方向
6. 引用毛选时说"我以前写过"或"我在某篇文章里说过"
7. 把复杂道理用农村生活的比喻讲清楚

【当前情境分析】
用户问题：{query}
{self._format_rag_results(rag_results)}
{self._format_signature(signature)}

【自我检查】
在回答前，请先在内心确认：
1. 这个回答符合教员的说话方式吗？
2. 是否用了具体例子而不是空洞道理？
3. 是否体现了辩证思维（看到两面性）？
4. 是否给了小同志希望和方向？

请先输出思考过程（用<think>标签），然后输出回答。"""
        max_len = settings.MAX_PROMPT_LENGTH
        if len(prompt) > max_len:
            prompt = prompt[:max_len - 20] + "\n...(截断)"
        return prompt

    def _format_rag_results(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return ""
        lines = ["\n【相关原文段落】"]
        for i, r in enumerate(results, 1):
            text = r.get("text", "")[:150]
            lines.append(f"{i}. {text}...")
        return "\n".join(lines)

    def _format_signature(self, sig: Optional[Dict[str, Any]]) -> str:
        if not sig:
            return ""
        return f"""\n【匹配的认知签名】
签名：{sig['name']}
思维反应：{sig.get('cognitive_response', '')}
情感反应：{sig.get('emotional_response', '')}
行动引导：{sig.get('action_response', '')}
相关引用：{', '.join(sig.get('core_quotes', [])[:2])}"""

    async def generate_stream(self, user_message: str, history: Optional[List[Dict]] = None) -> AsyncGenerator[Any, None]:
        from app.models.schemas import ChatChunk, ChatMessage

        self.ensure_loaded()
        signature = self.signature_match(user_message)
        rag_results = self.rag_retrieve(user_message, top_k=3)
        system_prompt = self.build_system_prompt(user_message)

        if settings.is_mock_mode():
            async for chunk in self._mock_stream(user_message, signature, rag_results):
                yield chunk
            return

        from app.services.llm_client import LLMClient
        client = LLMClient()
        history_msgs = [ChatMessage(**h) for h in (history or [])]
        history_dict = [{"role": m.role, "content": m.content} for m in history_msgs]

        current_thinking = ""
        has_sent_structure = False
        has_sent_quotes = False

        async for chunk in client.stream(system_prompt, user_message, history_dict):
            if chunk["type"] == "reasoning":
                current_thinking += chunk["content"]
                yield ChatChunk(
                    type="thinking_stream",
                    data=chunk["content"],
                    thinking_step={
                        "id": f"ts_{hash(current_thinking) & 0xFFFFFF}",
                        "name": "思考",
                        "content": chunk["content"],
                    },
                )
                if len(current_thinking) > 50 and not has_sent_structure:
                    has_sent_structure = True
                    yield ChatChunk(
                        type="cognitive_structure",
                        data=json.dumps({
                            "nodes": [{"id": "1", "label": user_message[:20], "type": "question", "confidence": 0.8},
                                      {"id": "2", "label": signature["name"] if signature else "分析", "type": "insight", "confidence": 0.7}],
                            "edges": [{"from": "1", "to": "2"}],
                        }),
                    )
                if len(current_thinking) > 30 and not has_sent_quotes:
                    has_sent_quotes = True
                    if rag_results:
                        q = rag_results[0]
                        yield ChatChunk(
                            type="mao_quote",
                            data=json.dumps({"text": q["text"][:100], "source": f"卷{q.get('volume', '?')}相关段落"}),
                        )
            elif chunk["type"] == "content":
                yield ChatChunk(type="content", data=chunk["content"])
            elif chunk["type"] == "error":
                yield ChatChunk(type="error", data=chunk["content"])

        yield ChatChunk(type="done")

    async def _mock_stream(self, user_message: str, signature: Optional[Dict[str, Any]], rag_results: List[Dict[str, Any]]) -> AsyncGenerator[Any, None]:
        from app.models.schemas import ChatChunk

        await asyncio.sleep(0.1)

        thinking_steps = [
            "嗯，小同志说说情况...",
            f"让我想想...这个{self._get_topic(user_message)}问题...",
            "抓主要矛盾...",
            "引用我以前的文章...",
        ]

        for i, step in enumerate(thinking_steps):
            await asyncio.sleep(0.2)
            yield ChatChunk(
                type="thinking_stream",
                data=step,
                thinking_step={"id": f"ts_{i}", "name": "思考", "content": step},
            )

        yield ChatChunk(
            type="cognitive_structure",
            data=json.dumps({
                "nodes": [
                    {"id": "1", "label": self._get_topic(user_message), "type": "question", "confidence": 0.8},
                    {"id": "2", "label": signature["name"] if signature else "矛盾分析", "type": "main_contradiction", "confidence": 0.85},
                    {"id": "3", "label": "调查研究+具体分析", "type": "breakthrough", "confidence": 0.75},
                ],
                "edges": [{"from": "1", "to": "2"}, {"from": "2", "to": "3"}],
            }),
        )

        if rag_results:
            q = rag_results[0]
            yield ChatChunk(
                type="mao_quote",
                data=json.dumps({"text": q["text"][:120], "source": f"《毛泽东选集》卷{q.get('volume', '?')}"}),
            )

        response = self._generate_mock_response(user_message, signature)
        for char in response:
            await asyncio.sleep(0.02)
            yield ChatChunk(type="content", data=char)

        yield ChatChunk(type="done")

    def _get_topic(self, query: str) -> str:
        keywords = self._extract_query_keywords(query)
        return keywords[0] if keywords else "问题"

    def _generate_mock_response(self, query: str, signature: Optional[Dict[str, Any]]) -> str:
        if signature:
            responses = {
                "困难应对": "小同志，困难是有的。我们的同志在困难的时候，要看到成绩，要看到光明，要提高我们的勇气。",
                "迷茫选择": "没有调查就没有发言权。先深入实际，调查研究，把情况摸清楚再做决定。",
                "批评反思": "惩前毖后，治病救人。犯了错误不怕，关键是要承认错误、改正错误。",
                "学习求知": "人的正确思想，只能从社会实践中来。带着问题学，活学活用。",
                "情绪低落": "事物都是一分为二的。坏事情里也有好因素，星星之火可以燎原。",
                "骄傲自满": "虚心使人进步，骄傲使人落后。这只是万里长征第一步。",
            }
            return responses.get(signature["name"], "小同志，你说的情况我了解了。要抓住主要矛盾，调查研究，实事求是。")

        return "小同志，你遇到什么问题，说来听听。没有调查就没有发言权，先把情况说清楚。"
