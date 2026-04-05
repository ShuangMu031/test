"""
记忆路由器

V9 三层记忆系统核心：
根据用户输入、情绪判断、关系上下文和世界上下文，生成统一的记忆分析文档，
再依据规则分别写入短期记忆、事件记忆和长期记忆。

三层记忆定义：
- 短期记忆: 当前会话态工作记忆，5-10分钟，会话结束后清空
- 事件记忆: 带情绪、情境、后果的事件档案，动态衰减
- 长期记忆: 稳定偏好、关系、身份事实，近永久保留
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class MemoryLayer(Enum):
    """记忆层级"""
    SHORT_TERM = "short_term"
    EPISODIC = "episodic"
    LONG_TERM = "long_term"


class EventType(Enum):
    """事件类型"""
    EMOTIONAL_INTERACTION = "emotional_interaction"
    RELATIONSHIP_CHANGE = "relationship_change"
    CONFLICT = "conflict"
    COMFORT = "comfort"
    DISAPPOINTMENT = "disappointment"
    PREFERENCE_EXPRESSION = "preference_expression"
    WORLD_IMPACT = "world_impact"
    PROMISE = "promise"
    USER_EXPERIENCE = "user_experience"


class LongTermCategory(Enum):
    """长期记忆类别"""
    PREFERENCE = "preference"
    DISLIKE = "dislike"
    HABIT = "habit"
    IDENTITY = "identity"
    RELATIONSHIP = "relationship"
    BOUNDARY = "boundary"


@dataclass
class ShortTermCandidate:
    """短期记忆候选"""
    topic: str
    salience: float = 0.5
    emotion: Optional[str] = None
    pending_followup: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodicCandidate:
    """事件记忆候选"""
    event_type: EventType
    summary: str
    importance: float = 0.5
    emotional_weight: float = 0.5
    relationship_impact: float = 0.0
    world_impact: float = 0.0
    followup_needed: bool = False
    followup_hint: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LongTermCandidate:
    """长期记忆候选"""
    category: LongTermCategory
    entity: str
    slot: str
    value: str
    confidence: float = 0.8
    source: str = "inferred"
    conflict_policy: str = "replace_or_merge"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryAnalysisDocument:
    """
    记忆分析文档
    
    每轮交互后生成的统一分析文档，包含三层记忆候选
    """
    turn_id: str
    session_id: str
    raw_input: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    emotion_insight: Dict[str, Any] = field(default_factory=dict)
    
    analysis: Dict[str, Any] = field(default_factory=dict)
    
    short_term_candidates: List[ShortTermCandidate] = field(default_factory=list)
    episodic_candidates: List[EpisodicCandidate] = field(default_factory=list)
    long_term_candidates: List[LongTermCandidate] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "raw_input": self.raw_input,
            "timestamp": self.timestamp.isoformat(),
            "emotion_insight": self.emotion_insight,
            "analysis": self.analysis,
            "short_term_candidates": [
                {
                    "topic": c.topic,
                    "salience": c.salience,
                    "emotion": c.emotion,
                    "pending_followup": c.pending_followup,
                    "metadata": c.metadata
                }
                for c in self.short_term_candidates
            ],
            "episodic_candidates": [
                {
                    "event_type": c.event_type.value,
                    "summary": c.summary,
                    "importance": c.importance,
                    "emotional_weight": c.emotional_weight,
                    "relationship_impact": c.relationship_impact,
                    "world_impact": c.world_impact,
                    "followup_needed": c.followup_needed,
                    "followup_hint": c.followup_hint,
                    "participants": c.participants,
                    "metadata": c.metadata
                }
                for c in self.episodic_candidates
            ],
            "long_term_candidates": [
                {
                    "category": c.category.value,
                    "entity": c.entity,
                    "slot": c.slot,
                    "value": c.value,
                    "confidence": c.confidence,
                    "source": c.source,
                    "conflict_policy": c.conflict_policy,
                    "metadata": c.metadata
                }
                for c in self.long_term_candidates
            ]
        }


class MemoryRouter:
    """
    记忆路由器
    
    根据用户输入、情绪判断、关系上下文和世界上下文，生成记忆分析文档。
    
    路由规则：
    
    短期记忆写入条件：
    - 当前会话上下文
    - 最近对话窗口
    - 当前情绪轨迹
    - 未完成问题/承诺
    
    事件记忆写入条件：
    - 情绪强度 >= 0.65
    - 重要性 >= 0.70
    - 关系变化
    - 后续需要跟进
    - 世界/NPC事件影响角色
    
    长期记忆写入条件：
    - 明确稳定事实（我喜欢/讨厌/习惯）
    - 重复出现的偏好
    - 对以后回复有持续影响
    """
    
    EPISODIC_KEYWORDS = [
        "重要", "关键", "第一次", "终于", "没想到", "震惊",
        "难过", "开心", "生气", "害怕", "担心", "失望"
    ]
    
    LONG_TERM_PATTERNS = [
        (r"我(喜欢|爱|最爱)", LongTermCategory.PREFERENCE, "likes"),
        (r"我(讨厌|恨|最讨厌)", LongTermCategory.DISLIKE, "dislikes"),
        (r"我(习惯|总是|经常)", LongTermCategory.HABIT, "habits"),
        (r"记住[，,]?", LongTermCategory.PREFERENCE, "explicit"),
        (r"以后(别|不要|不要)", LongTermCategory.BOUNDARY, "boundaries"),
        (r"我是", LongTermCategory.IDENTITY, "identity"),
    ]
    
    RELATIONSHIP_PATTERNS = [
        r"是我(朋友|兄弟|姐妹|家人|同事)",
        r"我和.*是(朋友|恋人|敌人)",
        r"我们(关系|感情)",
    ]
    
    def __init__(
        self,
        core_memory=None,
        episodic_memory=None,
        working_memory=None
    ):
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
    
    def analyze(
        self,
        turn_id: str,
        session_id: str,
        user_input: str,
        emotion_insight: Optional[Dict[str, Any]] = None,
        world_context: Optional[Dict[str, Any]] = None,
        npc_context: Optional[Dict[str, Any]] = None
    ) -> MemoryAnalysisDocument:
        """
        分析并生成记忆分析文档
        
        Args:
            turn_id: 轮次ID
            session_id: 会话ID
            user_input: 用户输入
            emotion_insight: 情绪洞察
            world_context: 世界上下文
            npc_context: NPC上下文
            
        Returns:
            MemoryAnalysisDocument: 记忆分析文档
        """
        emotion_insight = emotion_insight or {}
        
        doc = MemoryAnalysisDocument(
            turn_id=turn_id,
            session_id=session_id,
            raw_input=user_input,
            emotion_insight=emotion_insight
        )
        
        doc.analysis = self._analyze_input(user_input, emotion_insight)
        
        doc.short_term_candidates = self._generate_short_term_candidates(
            user_input, emotion_insight, world_context, npc_context
        )
        
        doc.episodic_candidates = self._generate_episodic_candidates(
            user_input, emotion_insight, doc.analysis
        )
        
        doc.long_term_candidates = self._generate_long_term_candidates(
            user_input, emotion_insight
        )
        
        logger.debug(
            f"记忆分析完成: short_term={len(doc.short_term_candidates)}, "
            f"episodic={len(doc.episodic_candidates)}, "
            f"long_term={len(doc.long_term_candidates)}"
        )
        
        return doc
    
    def _analyze_input(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析输入内容"""
        has_emotion = emotion_insight.get("intensity", 0) >= 0.5
        has_event_keywords = any(kw in user_input for kw in self.EPISODIC_KEYWORDS)
        has_long_term_signal = any(
            re.search(pattern, user_input)
            for pattern, _, _ in self.LONG_TERM_PATTERNS
        )
        has_relationship = any(
            re.search(pattern, user_input)
            for pattern in self.RELATIONSHIP_PATTERNS
        )
        
        return {
            "has_short_term_value": True,
            "has_event_value": has_emotion or has_event_keywords,
            "has_long_term_value": has_long_term_signal,
            "has_relationship_change": has_relationship,
            "topic": self._extract_topic(user_input),
            "followup_needed": self._check_followup_needed(user_input)
        }
    
    def _extract_topic(self, user_input: str) -> str:
        """提取主题"""
        if len(user_input) <= 20:
            return user_input
        return user_input[:50] + "..." if len(user_input) > 50 else user_input
    
    def _check_followup_needed(self, user_input: str) -> bool:
        """检查是否需要后续跟进"""
        followup_patterns = [
            r"以后", r"下次", r"之后", r"待会", r"一会儿",
            r"还没", r"正在", r"准备"
        ]
        return any(re.search(p, user_input) for p in followup_patterns)
    
    def _generate_short_term_candidates(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any],
        world_context: Optional[Dict[str, Any]],
        npc_context: Optional[Dict[str, Any]]
    ) -> List[ShortTermCandidate]:
        """生成短期记忆候选"""
        candidates = []
        
        topic = self._extract_topic(user_input)
        salience = self._calculate_salience(user_input, emotion_insight)
        
        candidates.append(ShortTermCandidate(
            topic=topic,
            salience=salience,
            emotion=emotion_insight.get("primary_emotion"),
            pending_followup=self._check_followup_needed(user_input),
            metadata={
                "world_context": world_context is not None,
                "npc_context": npc_context is not None
            }
        ))
        
        return candidates
    
    def _generate_episodic_candidates(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> List[EpisodicCandidate]:
        """生成事件记忆候选"""
        candidates = []
        
        if not analysis.get("has_event_value"):
            return candidates
        
        emotion_intensity = emotion_insight.get("intensity", 0)
        importance = self._calculate_importance(user_input, emotion_insight)
        emotional_weight = self._calculate_emotional_weight(emotion_insight)
        
        if emotion_intensity < 0.65 and importance < 0.70:
            return candidates
        
        event_type = self._determine_event_type(user_input, emotion_insight)
        
        participants = self._extract_participants(user_input)
        
        candidates.append(EpisodicCandidate(
            event_type=event_type,
            summary=self._generate_event_summary(user_input, emotion_insight),
            importance=importance,
            emotional_weight=emotional_weight,
            relationship_impact=0.5 if analysis.get("has_relationship_change") else 0.0,
            followup_needed=analysis.get("followup_needed", False),
            followup_hint=self._generate_followup_hint(user_input),
            participants=participants
        ))
        
        return candidates
    
    def _generate_long_term_candidates(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> List[LongTermCandidate]:
        """生成长期记忆候选"""
        candidates = []
        
        for pattern, category, slot in self.LONG_TERM_PATTERNS:
            match = re.search(pattern, user_input)
            if match:
                value = self._extract_value(user_input, match)
                confidence = self._calculate_confidence(user_input, emotion_insight)
                
                candidates.append(LongTermCandidate(
                    category=category,
                    entity="user",
                    slot=slot,
                    value=value,
                    confidence=confidence,
                    source="explicit_statement" if "记住" in user_input else "inferred"
                ))
                break
        
        for pattern in self.RELATIONSHIP_PATTERNS:
            match = re.search(pattern, user_input)
            if match:
                candidates.append(LongTermCandidate(
                    category=LongTermCategory.RELATIONSHIP,
                    entity="user",
                    slot="relationship",
                    value=match.group(0),
                    confidence=0.85,
                    source="explicit_statement"
                ))
                break
        
        return candidates
    
    def _calculate_salience(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> float:
        """计算显著性"""
        base = 0.5
        
        emotion_intensity = emotion_insight.get("intensity", 0)
        base += emotion_intensity * 0.3
        
        if any(kw in user_input for kw in self.EPISODIC_KEYWORDS):
            base += 0.1
        
        return min(1.0, base)
    
    def _calculate_importance(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> float:
        """计算重要性"""
        base = 0.5
        
        if any(kw in user_input for kw in ["重要", "关键", "必须"]):
            base += 0.2
        
        emotion_intensity = emotion_insight.get("intensity", 0)
        base += emotion_intensity * 0.2
        
        if any(kw in user_input for kw in ["第一次", "终于", "没想到"]):
            base += 0.1
        
        return min(1.0, base)
    
    def _calculate_emotional_weight(
        self,
        emotion_insight: Dict[str, Any]
    ) -> float:
        """计算情绪权重"""
        intensity = emotion_insight.get("intensity", 0)
        support_need = emotion_insight.get("support_need", "none")
        
        weight = intensity
        
        if support_need == "high":
            weight += 0.15
        elif support_need == "medium":
            weight += 0.08
        
        return min(1.0, weight)
    
    def _determine_event_type(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> EventType:
        """确定事件类型"""
        primary_emotion = emotion_insight.get("primary_emotion", "").lower()
        
        if any(kw in user_input for kw in ["冲突", "吵架", "矛盾"]):
            return EventType.CONFLICT
        if any(kw in user_input for kw in ["安慰", "支持", "陪伴"]):
            return EventType.COMFORT
        if any(kw in user_input for kw in ["失望", "难过", "伤心"]):
            return EventType.DISAPPOINTMENT
        if any(kw in user_input for kw in ["朋友", "关系", "感情"]):
            return EventType.RELATIONSHIP_CHANGE
        if primary_emotion in ["happy", "joy", "excited", "sad", "angry", "fear"]:
            return EventType.EMOTIONAL_INTERACTION
        
        return EventType.USER_EXPERIENCE
    
    def _extract_participants(self, user_input: str) -> List[str]:
        """提取参与者"""
        participants = ["user"]
        
        patterns = [
            r"朋友", r"家人", r"同事", r"兄弟", r"姐妹",
            r"他", r"她", r"他们"
        ]
        
        for pattern in patterns:
            if re.search(pattern, user_input):
                participants.append(pattern)
        
        return list(set(participants))
    
    def _generate_event_summary(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> str:
        """生成事件摘要"""
        emotion = emotion_insight.get("primary_emotion", "")
        intensity = emotion_insight.get("intensity", 0)
        
        if len(user_input) <= 100:
            return f"用户{emotion}情绪表达（强度{intensity:.2f}）：{user_input}"
        
        return f"用户{emotion}情绪表达（强度{intensity:.2f}）：{user_input[:100]}..."
    
    def _generate_followup_hint(self, user_input: str) -> Optional[str]:
        """生成跟进提示"""
        if "下次" in user_input:
            return "可在后续对话中跟进此事进展"
        if "还没" in user_input:
            return "可询问后续是否完成"
        return None
    
    def _extract_value(self, user_input: str, match) -> str:
        """提取值"""
        start = match.end()
        value = user_input[start:].strip()
        
        stop_words = ["，", "。", "！", "？", "但是", "不过", "可是"]
        for word in stop_words:
            if word in value:
                value = value[:value.index(word)]
        
        return value.strip() if value else user_input
    
    def _calculate_confidence(
        self,
        user_input: str,
        emotion_insight: Dict[str, Any]
    ) -> float:
        """计算置信度"""
        base = 0.8
        
        if "记住" in user_input or "别忘" in user_input:
            base = 0.95
        
        emotion_intensity = emotion_insight.get("intensity", 0)
        if emotion_intensity >= 0.7:
            base += 0.05
        
        return min(1.0, base)
