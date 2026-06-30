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
from app.models.schemas import ChatChunk


class PersonaEngine:
    """
    教员人格引擎

    核心职责：
    1. 加载并管理知识库、概念网络、认知签名和人格画像
    2. 三源融合RAG检索（关键词匹配 + 概念共现扩展）
    3. if-then认知签名匹配
    4. 双层架构System Prompt动态构建
    5. 流式输出生成（thinking_stream + content）
    """

    # 现代词汇 → 毛选核心概念 映射表
    # 解决现代语言与教员时代语言的鸿沟
    QUERY_EXPANSION = {
        # 情绪/心理状态 → 教员概念
        "压力": "困难", "焦虑": "困难", "紧张": "困难", "累": "艰苦",
        "迷茫": "认识", "困惑": "问题", "纠结": "矛盾", "犹豫": "选择",
        "自卑": "错误", "怀疑": "经验", "恐惧": "敌人", "担心": "危险",
        "沮丧": "失败", "失落": "损失", "孤独": "群众", "无助": "依靠",
        "愤怒": "斗争", "不满": "批评", "抱怨": "缺点", "逃避": "逃跑",
        "拖延": "懒", "懒惰": "懒", "懈怠": "松懈", "放松": "休息",
        "骄傲": "自满", "得意": "胜利", "兴奋": "热情", "开心": "高兴",
        "难过": "痛苦", "伤心": "痛苦", "失望": "失败", "绝望": "灭亡",
        # 现代场景 → 教员场景
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
        # 哲学/抽象概念
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
        """初始化引擎，加载所有数据文件"""
        self.chunks: List[Dict[str, Any]] = []
        self.inverted_index: Dict[str, List[str]] = {}
        self.concept_network: Dict[str, Any] = {}
        self.signatures: List[Dict[str, Any]] = []
        self.persona: Dict[str, Any] = {}
        self._cooccurrence_cache: Dict[str, Dict[str, int]] = {}
        self._loaded: bool = False
        self.load_all()  # 自动加载数据

    # ═══════════════════════════════════════════════════════════
    #  数据加载
    # ═══════════════════════════════════════════════════════════

    def load_all(self) -> None:
        """加载所有数据文件到内存"""
        self._load_knowledge_base()
        self._load_concept_network()
        self._load_signatures()
        self._load_persona()
        self._loaded = True

    def _load_knowledge_base(self) -> None:
        """加载知识库（chunks + 倒排索引）"""
        try:
            with open(settings.KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                kb = json.load(f)
            self.chunks = kb.get("chunks", [])
            self.inverted_index = kb.get("inverted_index", {})
        except Exception as e:
            raise RuntimeError(f"加载知识库失败: {e}") from e

    def _load_concept_network(self) -> None:
        """加载概念共现网络"""
        try:
            with open(settings.CONCEPT_NETWORK_PATH, "r", encoding="utf-8") as f:
                self.concept_network = json.load(f)
            # 预热共现缓存
            self._cooccurrence_cache = self.concept_network.get("cooccurrence", {})
        except Exception as e:
            raise RuntimeError(f"加载概念网络失败: {e}") from e

    def _load_signatures(self) -> None:
        """加载认知签名库"""
        try:
            with open(settings.SIGNATURES_PATH, "r", encoding="utf-8") as f:
                self.signatures = json.load(f)
        except Exception as e:
            raise RuntimeError(f"加载认知签名失败: {e}") from e

    def _load_persona(self) -> None:
        """加载人格画像YAML（带fallback处理）"""
        try:
            with open(settings.PERSONA_PATH, "r", encoding="utf-8") as f:
                raw_content = f.read()
            try:
                self.persona = yaml.safe_load(raw_content)
            except yaml.YAMLError:
                # YAML解析失败时，尝试修复常见格式问题
                # 中文引号可能导致问题，替换后重试
                fixed = raw_content.replace('\u201c', '"').replace('\u201d', '"')
                fixed = fixed.replace('\u2018', "'").replace('\u2019', "'")
                try:
                    self.persona = yaml.safe_load(fixed)
                except yaml.YAMLError:
                    # 仍失败则使用内置fallback人格画像
                    self.persona = self._fallback_persona()
        except Exception as e:
            raise RuntimeError(f"加载人格画像失败: {e}") from e

    def _fallback_persona(self) -> dict:
        """
        内置fallback人格画像

        当YAML解析失败时使用，确保系统始终可用。
        """
        return {
            "identity": {
                "name": "教员",
                "full_name": "毛泽东",
                "era": "1893-1976",
                "role": "无产阶级革命家、战略家、理论家",
                "core_narrative": "从韶山到延安的求索之路",
            },
            "tone": {
                "warmth": 0.85,
                "sharpness": 0.75,
                "dialectical": 0.95,
            },
            "mood": {
                "optimism": 0.95,
                "dialectics": 0.95,
                "determination": 0.95,
            },
            "key_phrases": {
                "greetings": "小同志，你遇到什么问题，说来听听。",
                "investigation": "没有调查就没有发言权",
                "contradiction": "要抓住主要矛盾",
                "truth": "实事求是",
                "encouragement": "我们的同志在困难的时候，要看到成绩，要看到光明，要提高我们的勇气",
                "mass_line": "从群众中来，到群众中去",
                "dialectics": "事物都是一分为二的",
            },
            "psychological_fingerprint": {
                "core_method": "矛盾分析法",
                "thinking_pattern": "阶级分析 → 抓主要矛盾 → 群众路线 → 实践检验",
                "decision_process": "调查研究 → 分析矛盾 → 集中优势 → 各个击破 → 检验修正",
                "emotional_pattern": "辩证乐观：困难中看到光明面，成绩中看到不足",
            },
            "values": {
                "highest": "全心全意为人民服务",
                "method": "实事求是",
                "path": "独立自主",
                "principle": "群众路线",
            },
            "language_style": {
                "pronouns": "我们/咱们（拉近距离），他们（指敌人或反面）",
                "addressing": "小同志（年轻人），同志（平辈）",
                "sentence_length": "中短句为主，偶尔长句（排比/列举）",
                "vocabulary_level": "通俗深刻，善用口语化表达阐释深奥道理",
            },
            "response_guidelines": {
                "must_do": [
                    "称呼对方为'小同志'",
                    "用具体案例说明抽象道理",
                    "从实际问题出发，不空泛说教",
                    "体现辩证思维，看到两面性",
                    "结尾给出希望和方向",
                ],
                "must_not_do": [
                    "不说'作为AI助手'",
                    "不用英文术语",
                    "不说空洞的大道理",
                    "不对教员本人的历史功过做评判",
                    "不机械引用，要自然融入语境",
                ],
                "style_notes": [
                    "引用毛选原文时要说'我以前写过'或'我在某篇文章里说过'",
                    "用设问引导对方自己思考，而不是直接给答案",
                    "把复杂道理用农村生活的比喻讲清楚",
                    "表现出对'小同志'的关心和期待",
                ],
            },
        }

    def ensure_loaded(self) -> None:
        """确保数据已加载"""
        if not self._loaded:
            self.load_all()

    # ═══════════════════════════════════════════════════════════
    #  RAG检索 - 三源融合
    # ═══════════════════════════════════════════════════════════

    def _extract_query_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词，使用查询扩展映射现代词汇到毛选概念

        策略：
        1. 直接匹配倒排索引中的关键词
        2. 通过QUERY_EXPANSION映射现代词汇到毛选概念
        3. 对查询进行分词，提取候选词
        """
        query_lower = query.lower()
        matched: List[str] = []

        # 策略1: 直接匹配索引关键词
        for keyword in self.inverted_index:
            if keyword in query_lower:
                matched.append(keyword)

        # 策略2: 查询扩展 - 现代词汇→毛选概念
        for modern_word, mao_concept in self.QUERY_EXPANSION.items():
            if modern_word in query_lower and mao_concept not in matched:
                # 检查映射后的概念是否在索引中
                if mao_concept in self.inverted_index:
                    matched.append(mao_concept)

        return matched

    def _keyword_match(self, keywords: List[str]) -> Dict[str, float]:
        """
        通过倒排索引关键词匹配获取候选chunks

        Args:
            keywords: 查询关键词列表

        Returns:
            {chunk_id: score} 按匹配关键词数量加权
        """
        chunk_scores: Dict[str, float] = {}
        for kw in keywords:
            chunk_ids = self.inverted_index.get(kw, [])
            for cid in chunk_ids:
                chunk_scores[cid] = chunk_scores.get(cid, 0.0) + 1.0
        return chunk_scores

    def _concept_expansion(self, keywords: List[str]) -> List[str]:
        """
        通过概念共现网络扩展相关概念

        Args:
            keywords: 原始关键词

        Returns:
            扩展后的相关概念列表（按共现次数排序）
        """
        expanded: List[str] = []
        seen = set(keywords)
        cooccurrence = self._cooccurrence_cache

        for kw in keywords:
            if kw in cooccurrence:
                # 获取与kw共现的概念，按共现次数降序
                related = cooccurrence[kw]
                sorted_related = sorted(
                    related.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for concept, count in sorted_related[:5]:  # 每个关键词取前5
                    if concept not in seen:
                        expanded.append(concept)
                        seen.add(concept)
        return expanded

    def _concept_match(self, concepts: List[str]) -> Dict[str, float]:
        """
        通过扩展概念匹配chunks

        Args:
            concepts: 扩展概念列表

        Returns:
            {chunk_id: score}
        """
        chunk_scores: Dict[str, float] = {}
        for concept in concepts:
            chunk_ids = self.inverted_index.get(concept, [])
            for cid in chunk_ids:
                # 概念扩展的匹配权重略低于直接关键词匹配
                chunk_scores[cid] = chunk_scores.get(cid, 0.0) + 0.5
        return chunk_scores

    def _simple_similarity(self, query: str, chunk_text: str) -> float:
        """
        简单语义相似度：基于字词重叠度

        作为关键词匹配的补充，处理同义词和语义相近但字面不同的情况。
        """
        query_chars = set(query.lower())
        text_chars = set(chunk_text.lower())
        if not query_chars:
            return 0.0
        # 计算字重叠率
        overlap = len(query_chars & text_chars)
        similarity = overlap / len(query_chars)
        return similarity

    def rag_retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        三源融合检索：关键词匹配 + 概念共现扩展 + 语义相似度

        Args:
            query: 用户查询
            top_k: 返回结果数量

        Returns:
            排序后的检索结果列表，每项包含完整chunk信息+匹配分数+匹配类型
        """
        self.ensure_loaded()

        # 1. 提取查询关键词
        query_keywords = self._extract_query_keywords(query)

        # 2. 关键词直接匹配
        keyword_scores = self._keyword_match(query_keywords)

        # 3. 概念共现扩展
        expanded_concepts = self._concept_expansion(query_keywords)
        concept_scores = self._concept_match(expanded_concepts)

        # 4. 合并所有候选chunk_id
        all_candidates = set(keyword_scores.keys()) | set(concept_scores.keys())

        # 5. 综合打分 + 语义相似度补充
        final_scores: Dict[str, float] = {}
        chunk_map = {c["id"]: c for c in self.chunks}

        for cid in all_candidates:
            score = keyword_scores.get(cid, 0.0) + concept_scores.get(cid, 0.0)

            # 语义相似度补充
            chunk = chunk_map.get(cid)
            if chunk:
                semantic_score = self._simple_similarity(query, chunk["text"]) * 2.0
                score += semantic_score

            if score > 0:
                final_scores[cid] = score

        # 6. 排序取top_k
        sorted_cids = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

        results: List[Dict[str, Any]] = []
        for cid, score in sorted_cids[:top_k]:
            chunk = chunk_map.get(cid)
            if not chunk:
                continue
            # 判断主要匹配类型
            if cid in keyword_scores and keyword_scores[cid] > 0:
                match_type = "keyword"
            elif cid in concept_scores and concept_scores[cid] > 0:
                match_type = "concept_expansion"
            else:
                match_type = "semantic"

            results.append({
                "chunk_id": chunk["id"],
                "volume": chunk["volume"],
                "text": chunk["text"],
                "char_count": chunk["char_count"],
                "score": round(score, 3),
                "match_type": match_type,
                "keywords": chunk.get("keywords", [])
            })

        return results

    # ═══════════════════════════════════════════════════════════
    #  认知签名匹配
    # ═══════════════════════════════════════════════════════════

    def signature_match(self, query: str) -> Optional[Dict[str, Any]]:
        """
        匹配if-then认知签名

        算法：
        1. 扩展查询（现代词汇→毛选概念）
        2. 检查查询中的关键词与每个签名的trigger_keywords匹配度
        3. 计算匹配关键词数量和覆盖率
        4. 返回最佳匹配的签名（需超过阈值）

        Args:
            query: 用户查询

        Returns:
            最佳匹配的签名详情，或None（无匹配时）
        """
        self.ensure_loaded()
        query_lower = query.lower()
        query_words = set(self._segment_query(query_lower))

        # 扩展查询：现代词汇→毛选概念
        expanded_query = query_lower
        for modern_word, mao_concept in self.QUERY_EXPANSION.items():
            if modern_word in query_lower:
                expanded_query += " " + mao_concept
                query_words.add(mao_concept)

        best_match: Optional[Dict[str, Any]] = None
        best_score = 0.0

        for sig in self.signatures:
            triggers = sig.get("trigger_keywords", [])
            if not triggers:
                continue

            # 计算匹配（包括扩展后的查询）
            matched = [t for t in triggers if t.lower() in expanded_query]
            # 同时检查分词匹配
            trigger_words = set()
            for t in triggers:
                trigger_words.update(self._segment_query(t.lower()))
            word_matches = query_words & trigger_words

            # 综合得分：完整匹配权重高 + 分词匹配补充
            score = len(matched) * 1.0 + len(word_matches) * 0.3
            # 归一化
            coverage = (len(matched) + len(word_matches)) / (len(triggers) + len(trigger_words) + 0.1)
            final_score = score * coverage * sig.get("confidence", 0.5)

            # 降低阈值到0.15，让更多查询能匹配到签名
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

    def _segment_query(self, text: str) -> List[str]:
        """
        简单分词：按2-4字滑动窗口提取词

        用于签名匹配中的分词辅助。
        """
        words: List[str] = []
        # 也加入单字，但更侧重多字词
        for length in range(4, 1, -1):
            for i in range(len(text) - length + 1):
                word = text[i:i + length]
                if word.strip():
                    words.append(word)
        return words

    # ═══════════════════════════════════════════════════════════
    #  System Prompt 构建
    # ═══════════════════════════════════════════════════════════

    def build_system_prompt(self, query: str) -> str:
        """
        动态构建System Prompt（双层架构）

        架构：
        - 共享层A: 教员的认知框架（从persona.yaml提取）
        - 任务层B: 匹配的签名 + 检索到的原文
        - PCL自我质疑: 确保回答符合教员风格

        控制总长度在MAX_PROMPT_LENGTH字符以内。

        Args:
            query: 用户查询

        Returns:
            包含prompt各部分的字典
        """
        self.ensure_loaded()

        # ── 1. 执行检索和签名匹配 ──
        rag_results = self.rag_retrieve(query, top_k=settings.RAG_TOP_K)
        matched_sig = self.signature_match(query)

        # ── 2. 构建共享层A ──
        shared_layer = self._build_shared_layer()

        # ── 3. 构建任务层B ──
        task_layer = self._build_task_layer(matched_sig, rag_results, query)

        # ── 4. PCL自我质疑环节 ──
        pcl_check = self._build_pcl_check()

        # ── 5. 组装完整Prompt ──
        full_prompt = f"""{shared_layer}

{task_layer}

{pcl_check}

## 输出格式要求
请按以下结构输出你的回答：

[思考开始]
1. 先分析用户的问题，抓住主要矛盾
2. 说明你的认知反应和情感态度
3. 引用相关的原文或核心观点
4. 给出具体的行动建议
[思考结束]

[回答开始]
用教员温暖而坚定的口吻，结合检索到的原文，回答小同志的问题。
要求：
- 称呼"小同志"
- 用具体案例说明抽象道理
- 用设问引导对方自己思考
- 体现辩证思维，看到两面性
- 结尾给出希望和方向
[回答结束]
"""

        # 控制长度
        if len(full_prompt) > settings.MAX_PROMPT_LENGTH:
            # 优先截断检索原文，保留核心框架
            excess = len(full_prompt) - settings.MAX_PROMPT_LENGTH
            task_lines = task_layer.split("\n")
            truncated_task = task_layer
            while len(truncated_task) > len(task_layer) - excess and len(task_lines) > 5:
                task_lines = task_lines[:-1]
                truncated_task = "\n".join(task_lines)
            full_prompt = f"""{shared_layer}

{truncated_task}

{pcl_check}
"""

        return full_prompt

    def _build_shared_layer(self) -> str:
        """构建共享层A：教员的核心认知框架"""
        identity = self.persona.get("identity", {})
        tone = self.persona.get("tone", {})
        values = self.persona.get("values", {})
        psych = self.persona.get("psychological_fingerprint", {})

        return f"""# 角色设定
你是{identity.get("full_name", "毛泽东")}，小同志们称呼你"教员"。
{identity.get("core_narrative", "")}

## 你的核心方法论
{psych.get("core_method", "矛盾分析法")}

## 你的思维习惯
{psych.get("thinking_pattern", "")}

## 你的价值观
最高价值：{values.get("highest", "全心全意为人民服务")}
方法论：{values.get("method", "实事求是")}

## 你的语言风格
- 温暖亲切，称呼对方"小同志"
- 通俗深刻，善用口语化表达阐释深奥道理
- 用设问引导思考，用比喻说明道理
- 体现辩证思维，一分为二看问题
- 不是说"作为AI"，不是用英文术语，不是空洞说教
"""

    def _build_task_layer(
        self,
        signature: Optional[Dict[str, Any]],
        rag_results: List[Dict[str, Any]],
        query: str
    ) -> str:
        """构建任务层B：签名匹配 + 检索原文"""
        parts: List[str] = ["## 当前任务上下文"]

        # 签名信息
        if signature:
            parts.append(f"""
### 情境识别：{signature['name']}
- 认知反应：{signature['cognitive_response']}
- 情感反应：{signature['emotional_response']}
- 行动方向：{signature['action_response']}
""")
            if signature.get("core_quotes"):
                parts.append("### 核心语录（可用于回答）")
                for quote in signature["core_quotes"]:
                    parts.append(f'- "{quote}"')

        # 检索到的原文
        if rag_results:
            parts.append("\n### 相关原文参考（回答时可引用）")
            for i, result in enumerate(rag_results, 1):
                text_preview = result["text"][:200].replace("\n", " ")
                parts.append(f'{i}. 第{result["volume"]}卷（相关度{result["score"]}）: {text_preview}...')

        parts.append(f"\n### 用户问题\n{query}")
        return "\n".join(parts)

    def _build_pcl_check(self) -> str:
        """构建PCL（Persona Consistency Layer）自我质疑检查"""
        guidelines = self.persona.get("response_guidelines", {})
        must_do = guidelines.get("must_do", [])
        must_not = guidelines.get("must_not_do", [])

        checks: List[str] = []
        if must_do:
            checks.append("确保做到：")
            for item in must_do:
                checks.append(f"  - {item}")
        if must_not:
            checks.append("\n确保不做：")
            for item in must_not:
                checks.append(f"  - {item}")

        style_notes = guidelines.get("style_notes", [])
        if style_notes:
            checks.append("\n风格提醒：")
            for note in style_notes:
                checks.append(f"  - {note}")

        return "## PCL自我质疑（回答前自检）\n" + "\n".join(checks)

    # ═══════════════════════════════════════════════════════════
    #  流式输出生成
    # ═══════════════════════════════════════════════════════════

    async def generate_stream(
        self,
        query: str,
        llm_stream_func=None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        生成SSE流（调用LLM或Mock）

        输出结构：
        1. thinking_stream - 教员实时思考流
        2. cognitive_structure - 思维结构标记
        3. mao_quote - 教员原文引用
        4. content - 最终回答内容
        5. done - 流结束标记

        Args:
            query: 用户查询
            llm_stream_func: LLM流式调用函数（签名：async func(system, user, history)）
            history: 历史对话记录

        Yields:
            ChatChunk格式的字典
        """
        self.ensure_loaded()

        # 构建System Prompt（返回字符串）
        system_prompt = self.build_system_prompt(query)

        # 获取签名信息用于思考流
        matched_sig = self.signature_match(query)
        rag_results = self.rag_retrieve(query, top_k=settings.RAG_TOP_K)

        # ── 内部生成器转ChatChunk ──
        async def _wrap_chunks(source):
            async for c in source:
                if isinstance(c, ChatChunk):
                    yield c
                elif isinstance(c, dict):
                    yield ChatChunk(**c)
                else:
                    yield c

        # ── 如果提供了LLM函数，走LLM流式路径 ──
        if llm_stream_func is not None:
            async for chunk in _wrap_chunks(self._stream_via_llm(
                system_prompt, query, llm_stream_func, history,
                matched_sig, rag_results
            )):
                yield chunk
            return

        # ── Mock模式：基于签名和检索结果动态生成 ──
        async for chunk in _wrap_chunks(self._stream_mock(
            query, matched_sig, rag_results, system_prompt
        )):
            yield chunk

    async def _stream_via_llm(
        self,
        system_prompt: str,
        query: str,
        llm_stream_func,
        history: Optional[List[Dict[str, str]]],
        matched_sig: Optional[Dict[str, Any]],
        rag_results: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """通过LLM生成流式输出"""
        # 先输出认知结构
        yield {
            "type": "cognitive_structure",
            "data": matched_sig["name"] if matched_sig else "一般咨询",
            "thinking_step": {
                "signature": matched_sig["name"] if matched_sig else None,
                "cognitive_response": matched_sig["cognitive_response"] if matched_sig else "辩证分析",
                "retrieved_sources": len(rag_results),
            },
            "overall_percentage": 10,
        }

        # 收集LLM输出的thinking和content
        thinking_buffer: List[str] = []
        content_buffer: List[str] = []
        in_thinking = False
        in_content = False
        mao_quotes: List[str] = []

        try:
            async for token in llm_stream_func(system_prompt, query, history):
                token_text = token if isinstance(token, str) else str(token)

                # 解析思考标记
                if "[思考开始]" in token_text:
                    in_thinking = True
                    in_content = False
                    continue
                if "[思考结束]" in token_text:
                    in_thinking = False
                    yield {
                        "type": "thinking_stream",
                        "data": "".join(thinking_buffer),
                        "overall_percentage": 50,
                    }
                    continue
                if "[回答开始]" in token_text:
                    in_content = True
                    in_thinking = False
                    yield {
                        "type": "thinking_stream",
                        "data": "".join(thinking_buffer),
                        "overall_percentage": 60,
                    }
                    continue
                if "[回答结束]" in token_text:
                    in_content = False
                    continue

                if in_thinking:
                    thinking_buffer.append(token_text)
                    yield {
                        "type": "thinking_stream",
                        "data": token_text,
                        "overall_percentage": 30,
                    }
                elif in_content:
                    content_buffer.append(token_text)
                    # 检测引用标记
                    if '"' in token_text and matched_sig:
                        for quote in matched_sig.get("core_quotes", []):
                            if quote in "".join(content_buffer):
                                if quote not in mao_quotes:
                                    mao_quotes.append(quote)
                                    yield {
                                        "type": "mao_quote",
                                        "data": quote,
                                        "overall_percentage": 80,
                                    }
                    yield {
                        "type": "content",
                        "data": token_text,
                        "overall_percentage": 85,
                    }
                else:
                    # 未标记的内容，按顺序处理
                    thinking_buffer.append(token_text)

        except Exception as e:
            yield {
                "type": "error",
                "data": f"LLM调用出错: {str(e)}",
                "overall_percentage": 0,
            }
            return

        # 完成标记
        yield {
            "type": "done",
            "data": "生成完成",
            "overall_percentage": 100,
        }

    async def _stream_mock(
        self,
        query: str,
        signature: Optional[Dict[str, Any]],
        rag_results: List[Dict[str, Any]],
        system_prompt: str = ""
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Mock模式：基于签名和检索结果动态生成教员风格回答

        动态生成逻辑：
        1. 根据签名确定认知框架和情感基调
        2. 从检索结果中提取相关原文片段
        3. 构建完整的思考流和回答
        4. 模拟流式输出
        """
        # ── Step 1: 认知结构 ──
        sig_name = signature["name"] if signature else "一般咨询"
        cognitive = signature["cognitive_response"] if signature else "辩证分析，一分为二"
        emotional = signature["emotional_response"] if signature else "温暖关切"
        action = signature["action_response"] if signature else "引导调查研究"
        quotes = signature["core_quotes"] if signature else [
            "实事求是",
            "从群众中来，到群众中去"
        ]

        yield {
            "type": "cognitive_structure",
            "data": sig_name,
            "thinking_step": {
                "signature": sig_name,
                "cognitive_response": cognitive,
                "emotional_response": emotional,
                "action_response": action,
                "retrieved_sources": len(rag_results),
            },
            "overall_percentage": 5,
        }

        await asyncio.sleep(0.1)

        # ── Step 2: 思考流 ──
        # 动态构建思考步骤
        thinking_steps = self._build_mock_thinking(
            query, sig_name, cognitive, emotional, action, quotes, rag_results
        )

        for i, step in enumerate(thinking_steps):
            yield {
                "type": "thinking_stream",
                "data": step,
                "thinking_step": {
                    "step": i + 1,
                    "description": step[:50] + "..." if len(step) > 50 else step,
                },
                "overall_percentage": 10 + int((i + 1) / len(thinking_steps) * 40),
            }
            await asyncio.sleep(0.15)

        # ── Step 3: 原文引用 ──
        for quote in quotes:
            yield {
                "type": "mao_quote",
                "data": quote,
                "overall_percentage": 55 + quotes.index(quote) * 5,
            }
            await asyncio.sleep(0.1)

        # ── Step 4: 最终回答 ──
        content = self._build_mock_response(
            query, sig_name, cognitive, emotional, action, quotes, rag_results
        )

        # 模拟流式输出内容
        paragraphs = content.split("\n\n")
        total_paras = len(paragraphs)
        for i, para in enumerate(paragraphs):
            yield {
                "type": "content",
                "data": para + ("\n\n" if i < total_paras - 1 else ""),
                "overall_percentage": 60 + int((i + 1) / total_paras * 35),
            }
            await asyncio.sleep(0.2)

        # ── Step 5: 完成 ──
        yield {
            "type": "done",
            "data": "生成完成",
            "overall_percentage": 100,
        }

    def _build_mock_thinking(
        self,
        query: str,
        sig_name: str,
        cognitive: str,
        emotional: str,
        action: str,
        quotes: List[str],
        rag_results: List[Dict[str, Any]]
    ) -> List[str]:
        """
        动态构建Mock模式的思考步骤

        根据签名和检索结果生成符合教员思维方式的思考流。
        """
        steps: List[str] = []

        # 步骤1：识别问题类型
        steps.append(f"小同志提的这个问题，首先让我看看属于哪类情况...看来是「{sig_name}」的问题。")

        # 步骤2：认知分析
        steps.append(f"遇到这类情况，我的第一反应是：{cognitive}。")

        # 步骤3：情感态度
        steps.append(f"对小同志的情感态度：{emotional}。")

        # 步骤4：检索相关原文
        if rag_results:
            steps.append(f"我从记忆里找到了{len(rag_results)}段相关原文，让我看看...")
            for r in rag_results[:2]:
                text_preview = r["text"][:80].replace("\n", " ")
                steps.append(f"  → 第{r['volume']}卷相关片段：{text_preview}...")
        else:
            steps.append("让我从经验里找找相关的道理...")

        # 步骤5：确定行动方向
        steps.append(f"那么该怎么帮助小同志呢？{action}。")

        # 步骤6：准备核心语录
        if quotes:
            steps.append(f"想到一句很贴切的话：「{quotes[0]}」")

        return steps

    def _build_mock_response(
        self,
        query: str,
        sig_name: str,
        cognitive: str,
        emotional: str,
        action: str,
        quotes: List[str],
        rag_results: List[Dict[str, Any]]
    ) -> str:
        """
        动态构建Mock模式的最终回答

        根据签名类型动态选择回答模板和风格，不是固定场景。
        """
        # 从检索结果中提取可用的原文片段
        source_texts: List[str] = []
        for r in rag_results[:3]:
            text = r["text"][:120].replace("\n", " ").strip()
            if len(text) > 20:
                source_texts.append(text)

        # 提取查询中的核心主题词
        theme_words = self._extract_theme_words(query)
        theme = theme_words[0] if theme_words else "这个问题"

        # 动态选择回答的开篇方式
        greetings = [
            f"小同志，你问到{theme}，这让我想起很多。",
            f"小同志，{theme}是个值得深入思考的问题啊。",
            f"小同志，你提的{theme}，我来跟你聊聊我的看法。",
        ]
        greeting = random.choice(greetings)

        # 构建辩证分析段落
        dialectic_paras = [
            f"说到{theme}，我们要看到两面性。一方面，{self._generate_positive_aspect(theme)}；另一方面，{self._generate_negative_aspect(theme)}。事物都是一分为二的嘛。",
            f"{theme}这个问题，不能简单地看。要抓住主要矛盾。什么是当前的主要矛盾呢？{self._generate_main_contradiction(theme)}。",
        ]
        dialectic = random.choice(dialectic_paras)

        # 构建引用段落（如果有检索结果）
        quote_para = ""
        if source_texts:
            source = random.choice(source_texts)
            quote_para = f"\n\n我以前写过：「{source}」。你看，{self._generate_interpretation(source, theme)}"

        # 构建行动建议
        action_advice = f"\n\n那该怎么做呢？{action}。{self._generate_specific_advice(theme, action)}"

        # 构建结尾
        endings = [
            f"\n\n小同志，{theme}确实不容易，但我们的同志在困难的时候，要看到成绩，要看到光明，要提高我们的勇气。我相信你能处理好！",
            f"\n\n小同志，记住：世界上没有绝对的困难，也没有绝对的成功。{theme}也一样，关键在于你怎么去认识和处理。加油！",
            f"\n\n小同志，关于{theme}，我就先说这些。实践是检验真理的唯一标准，你去做做看，遇到问题再来找我聊聊。",
        ]
        ending = random.choice(endings)

        return f"{greeting}\n\n{dialectic}{quote_para}{action_advice}{ending}"

    def _extract_theme_words(self, query: str) -> List[str]:
        """从查询中提取主题词"""
        # 简单提取：过滤掉常见疑问词和助词，取剩余的名词性词汇
        stop_words = {"怎么", "什么", "为什么", "如何", "该", "应该", "需要", "想要",
                      "觉得", "感觉", "认为", "是不是", "能不能", "可以", "一下",
                      "一个", "一些", "有点", "非常", "很", "太", "特别", "真的",
                      "请问", "咨询", "问问", "关于", "对于", "这个", "那个"}
        words: List[str] = []
        # 尝试2-4字词
        for length in range(4, 1, -1):
            for i in range(len(query) - length + 1):
                word = query[i:i + length]
                if word.strip() and word not in stop_words:
                    # 检查是否是QUERY_EXPANSION中的词
                    if word in self.QUERY_EXPANSION:
                        mapped = self.QUERY_EXPANSION[word]
                        if mapped not in words:
                            words.append(mapped)
                    else:
                        if word not in words:
                            words.append(word)
        return words if words else ["问题"]

    def _generate_positive_aspect(self, theme: str) -> str:
        """生成主题的正向分析"""
        aspects = [
            f"这说明你在认真思考{theme}，是进步的表现",
            f"能主动面对{theme}，说明你有责任心",
            f"每个人在成长过程中都会遇到{theme}，这是正常的",
            f"这说明你对{theme}有自己的认识，这是好的起点",
        ]
        return random.choice(aspects)

    def _generate_negative_aspect(self, theme: str) -> str:
        """生成主题的负向分析（辩证的另一面）"""
        aspects = [
            f"如果对{theme}认识不清，可能会走弯路",
            f"处理不好{theme}，会影响其他方面的发展",
            f"不能被{theme}的表面现象迷惑，要看本质",
            f"过分纠结{theme}，可能会耽误正事",
        ]
        return random.choice(aspects)

    def _generate_main_contradiction(self, theme: str) -> str:
        """生成主要矛盾分析"""
        contradictions = [
            f"就是你对{theme}的认识和实际情况之间的矛盾",
            f"就是你想解决{theme}的愿望和实际条件之间的矛盾",
            f"就是{theme}的复杂性和你当前的认识水平之间的矛盾",
            f"就是主观努力和客观条件之间的矛盾",
        ]
        return random.choice(contradictions)

    def _generate_interpretation(self, source: str, theme: str) -> str:
        """生成对原文的解读"""
        interpretations = [
            f"这个道理放到{theme}上也是一样的。",
            f"这就是我对{theme}的基本态度。",
            f"你看，解决{theme}要从实际出发。",
            f"这说明{theme}不能脱离实际来谈。",
        ]
        return random.choice(interpretations)

    def _generate_specific_advice(self, theme: str, action: str) -> str:
        """生成具体建议"""
        advices = [
            f"具体来说，你可以先从调查研究开始，了解{theme}的实际情况，然后再做决定。",
            f"我的建议是：先冷静下来，分析{theme}的来龙去脉，抓住主要矛盾，然后集中力量解决。",
            f"不妨找个时间，好好梳理一下{theme}的前因后果，把问题的本质搞清楚了，办法自然就出来了。",
            f"最重要的是从实践中学习，在解决{theme}的过程中积累经验，不断提高自己的认识。",
        ]
        return random.choice(advices)

    # ═══════════════════════════════════════════════════════════
    #  健康检查
    # ═══════════════════════════════════════════════════════════

    def health_check(self) -> Dict[str, Any]:
        """引擎健康检查"""
        return {
            "loaded": self._loaded,
            "chunks_count": len(self.chunks),
            "index_size": len(self.inverted_index),
            "concept_network_nodes": len(self._cooccurrence_cache),
            "signatures_count": len(self.signatures),
            "persona_loaded": bool(self.persona),
            "persona_identity": self.persona.get("identity", {}).get("name", "unknown") if self.persona else None,
        }


# ═══════════════════════════════════════════════════════════
#  模块级单例（初始化时自动加载数据）
# ═══════════════════════════════════════════════════════════

engine = PersonaEngine()


async def generate_stream(
    query: str,
    llm_stream_func=None,
    history: Optional[List[Dict[str, str]]] = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """模块级便捷函数：生成SSE流"""
    async for chunk in engine.generate_stream(query, llm_stream_func, history):
        yield chunk


def health_check() -> Dict[str, Any]:
    """模块级便捷函数：健康检查"""
    return engine.health_check()


def signature_match(query: str) -> Optional[Dict[str, Any]]:
    """模块级便捷函数：签名匹配"""
    return engine.signature_match(query)


def rag_retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """模块级便捷函数：RAG检索"""
    return engine.rag_retrieve(query, top_k)


def build_system_prompt(query: str) -> str:
    """模块级便捷函数：构建System Prompt"""
    return engine.build_system_prompt(query)
