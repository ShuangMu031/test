"""
记忆脑

V9 三层记忆系统：
从"单条存储判断器"改成"三层记忆路由决策器"

核心变化：
- 使用 MemoryRouter 生成 MemoryAnalysisDocument
- 产出 short_term_candidates, episodic_candidates, long_term_candidates
- 为每层生成 payload

三层记忆定义：
- 短期记忆: 当前会话态工作记忆，5-10分钟，会话结束后清空
- 事件记忆: 带情绪、情境、后果的事件档案，动态衰减
- 长期记忆: 稳定偏好、关系、身份事实，近永久保留
"""

from typing import Any, Dict, List, Optional
import logging

from .base import BaseBrain
from application.contracts import MemoryDecision
from application.memory import (
    MemoryRouter,
    MemoryAnalysisDocument,
    ShortTermCandidate,
    EpisodicCandidate,
    LongTermCandidate
)

logger = logging.getLogger(__name__)


class MemoryBrain(BaseBrain):
    """
    记忆脑 V9
    
    三层记忆路由决策器。
    
    职责：
    1. 使用 MemoryRouter 分析输入
    2. 生成 MemoryAnalysisDocument
    3. 转换为 MemoryDecision 供主链使用
    4. 为每层生成 payload
    
    判断规则：
    - short_term: 当前会话上下文，默认写入
    - episodic: 高情感影响 / 高重要性 / 明确事件
    - long_term: 用户明确要求记住 / 偏好声明 / 关系变化
    """
    
    EPISODIC_KEYWORDS = ["重要", "关键", "第一次", "终于", "没想到", "震惊"]
    CORE_KEYWORDS = ["记住", "别忘了", "以后记住", "永远记住"]
    PREFERENCE_KEYWORDS = ["我喜欢", "我讨厌", "我爱", "我最爱", "我最讨厌"]
    RELATIONSHIP_KEYWORDS = ["是我朋友", "是我敌人", "是我家人", "是我同事"]
    
    def __init__(
        self,
        llm=None,
        core_memory=None,
        episodic_memory=None,
        working_memory=None
    ):
        self.llm = llm
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
        
        self.router = MemoryRouter(
            core_memory=core_memory,
            episodic_memory=episodic_memory,
            working_memory=working_memory
        )
    
    @property
    def name(self) -> str:
        return "memory"
    
    async def process(self, context: Any) -> MemoryDecision:
        """
        处理记忆路由决策
        
        V9 改版：使用 MemoryRouter 生成 MemoryAnalysisDocument
        
        Args:
            context: TurnContext，包含 user_input, emotion_insight 等
            
        Returns:
            MemoryDecision: 三层记忆路由决策
        """
        user_input = getattr(context, "user_input", "")
        emotion_insight = getattr(context, "emotion_insight", None)
        session_id = getattr(context, "session_id", "default_session")
        turn_id = getattr(context, "turn_id", f"turn_{id(context)}")
        
        emotion_dict = self._emotion_to_dict(emotion_insight)
        
        analysis_doc = self.router.analyze(
            turn_id=turn_id,
            session_id=session_id,
            user_input=user_input,
            emotion_insight=emotion_dict
        )
        
        context.memory_analysis_document = analysis_doc
        
        context.record_telemetry(
            "memory",
            short_term_count=len(analysis_doc.short_term_candidates),
            episodic_count=len(analysis_doc.episodic_candidates),
            long_term_count=len(analysis_doc.long_term_candidates),
            has_consolidation=len(analysis_doc.episodic_candidates) > 0 or len(analysis_doc.long_term_candidates) > 0
        )
        
        actions = []
        interactions = []
        
        if analysis_doc.short_term_candidates:
            actions.append("写入短期记忆")
            interactions.append("→ working_memory")
        
        if analysis_doc.episodic_candidates:
            for c in analysis_doc.episodic_candidates:
                actions.append(f"升级到事件记忆(类型={c.event_type.value})")
            interactions.append("→ episodic_memory")
        
        if analysis_doc.long_term_candidates:
            for c in analysis_doc.long_term_candidates:
                actions.append(f"写入长期记忆(类别={c.category.value})")
            interactions.append("→ core_memory")
        
        context.record_monologue(
            "memory",
            monologue=f"分析用户输入，生成 {len(analysis_doc.short_term_candidates)} 短期、{len(analysis_doc.episodic_candidates)} 事件、{len(analysis_doc.long_term_candidates)} 长期记忆候选",
            actions=actions,
            interactions=interactions
        )
        
        decision = self._convert_to_decision(analysis_doc, user_input, emotion_insight)
        
        return decision
    
    def _emotion_to_dict(self, emotion_insight: Any) -> Dict[str, Any]:
        """转换情绪洞察为字典"""
        if not emotion_insight:
            return {}
        
        return {
            "primary_emotion": getattr(emotion_insight, "primary_emotion", "neutral"),
            "intensity": getattr(emotion_insight, "intensity", 0.0),
            "valence": getattr(emotion_insight, "valence", 0.0),
            "arousal": getattr(emotion_insight, "arousal", 0.5),
            "support_need": getattr(emotion_insight, "support_need", "none")
        }
    
    def _convert_to_decision(
        self,
        analysis_doc: MemoryAnalysisDocument,
        user_input: str,
        emotion_insight: Any
    ) -> MemoryDecision:
        """
        将 MemoryAnalysisDocument 转换为 MemoryDecision
        
        保持与主链的兼容性
        """
        has_short_term = len(analysis_doc.short_term_candidates) > 0
        has_episodic = len(analysis_doc.episodic_candidates) > 0
        has_long_term = len(analysis_doc.long_term_candidates) > 0
        
        importance = self._calculate_importance(analysis_doc)
        emotional_impact = self._calculate_emotional_impact(analysis_doc)
        
        working_payload = self._build_working_payload(analysis_doc) if has_short_term else {}
        episodic_payload = self._build_episodic_payload(analysis_doc) if has_episodic else {}
        core_payload = self._build_core_payload(analysis_doc) if has_long_term else None
        
        reasoning = self._build_reasoning(analysis_doc)
        
        return MemoryDecision(
            write_working=has_short_term,
            write_episodic=has_episodic,
            write_core=has_long_term,
            should_consolidate=has_episodic or has_long_term,
            working_payload=working_payload,
            episodic_payload=episodic_payload,
            core_payload=core_payload,
            importance=importance,
            emotional_impact=emotional_impact,
            reasoning=reasoning
        )
    
    def _calculate_importance(self, analysis_doc: MemoryAnalysisDocument) -> float:
        """从分析文档计算重要性"""
        if analysis_doc.episodic_candidates:
            return max(c.importance for c in analysis_doc.episodic_candidates)
        return 0.5
    
    def _calculate_emotional_impact(self, analysis_doc: MemoryAnalysisDocument) -> float:
        """从分析文档计算情感影响"""
        if analysis_doc.episodic_candidates:
            return max(c.emotional_weight for c in analysis_doc.episodic_candidates)
        
        emotion = analysis_doc.emotion_insight
        if emotion:
            return emotion.get("intensity", 0.0)
        return 0.0
    
    def _build_working_payload(self, analysis_doc: MemoryAnalysisDocument) -> Dict[str, Any]:
        """构建 working memory payload"""
        if analysis_doc.short_term_candidates:
            candidate = analysis_doc.short_term_candidates[0]
            return {
                "content": analysis_doc.raw_input,
                "role": "user",
                "memory_type": "dialogue",
                "topic": candidate.topic,
                "salience": candidate.salience
            }
        return {
            "content": analysis_doc.raw_input,
            "role": "user",
            "memory_type": "dialogue"
        }
    
    def _build_episodic_payload(self, analysis_doc: MemoryAnalysisDocument) -> Dict[str, Any]:
        """构建 episodic memory payload"""
        if analysis_doc.episodic_candidates:
            candidate = analysis_doc.episodic_candidates[0]
            return {
                "description": candidate.summary,
                "event_type": candidate.event_type.value,
                "importance": candidate.importance,
                "emotional_impact": candidate.emotional_weight,
                "relationship_impact": candidate.relationship_impact,
                "followup_needed": candidate.followup_needed,
                "participants": candidate.participants
            }
        return {
            "description": analysis_doc.raw_input[:200],
            "event_type": "user_interaction",
            "importance": 0.5
        }
    
    def _build_core_payload(self, analysis_doc: MemoryAnalysisDocument) -> Dict[str, Any]:
        """构建 core memory payload"""
        if analysis_doc.long_term_candidates:
            candidate = analysis_doc.long_term_candidates[0]
            return {
                "category": candidate.category.value,
                "key": f"{candidate.entity}_{candidate.slot}",
                "value": candidate.value,
                "confidence": candidate.confidence
            }
        return {
            "category": "instruction",
            "key": "user_instruction",
            "value": analysis_doc.raw_input
        }
    
    def _build_reasoning(self, analysis_doc: MemoryAnalysisDocument) -> str:
        """构建推理说明"""
        parts = []
        
        if analysis_doc.short_term_candidates:
            parts.append("写入短期记忆")
        
        if analysis_doc.episodic_candidates:
            for c in analysis_doc.episodic_candidates:
                parts.append(
                    f"升级到事件记忆(类型={c.event_type.value}, "
                    f"重要性={c.importance:.2f}, 情绪权重={c.emotional_weight:.2f})"
                )
        
        if analysis_doc.long_term_candidates:
            for c in analysis_doc.long_term_candidates:
                parts.append(
                    f"写入长期记忆(类别={c.category.value}, 置信度={c.confidence:.2f})"
                )
        
        if not parts:
            parts.append("无需特殊记忆处理")
        
        return "; ".join(parts)
    
    def get_analysis_document(self, context: Any) -> Optional[MemoryAnalysisDocument]:
        """获取上下文中的分析文档"""
        return getattr(context, "memory_analysis_document", None)
