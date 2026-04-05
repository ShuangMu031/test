"""
记忆文档存储

V9 三层记忆系统：
统一读写短期记忆、事件记忆、长期记忆文档。

文档结构：
- 短期记忆: 会话态文档，5-10分钟TTL，会话结束后清空
- 事件记忆: 事件档案，动态衰减，情绪越重删得越慢
- 长期记忆: 角色事实库，近永久保留，冲突/覆盖时更新
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class ShortTermSession:
    """
    短期记忆会话文档
    
    只服务当前这一次会话，保存时间约 5 到 10 分钟，本次对话结束后清空
    """
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    status: str = "active"
    
    active_topic: Optional[str] = None
    emotion_trace: List[Dict[str, Any]] = field(default_factory=list)
    dialogue_window: List[Dict[str, Any]] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)
    pending_promises: List[Dict[str, Any]] = field(default_factory=list)
    latent_world_hooks: List[Dict[str, Any]] = field(default_factory=list)
    salience: float = 0.5
    
    ttl_minutes: int = 10
    
    def __post_init__(self):
        if self.expires_at is None:
            self.expires_at = self.last_active_at + timedelta(minutes=self.ttl_minutes)
    
    def refresh(self) -> None:
        """刷新活跃时间"""
        self.last_active_at = datetime.now()
        self.expires_at = self.last_active_at + timedelta(minutes=self.ttl_minutes)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expires_at if self.expires_at else False
    
    def add_emotion_trace(
        self,
        turn_id: str,
        primary_emotion: str,
        intensity: float
    ) -> None:
        """添加情绪轨迹"""
        self.emotion_trace.append({
            "turn_id": turn_id,
            "primary_emotion": primary_emotion,
            "intensity": intensity,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_dialogue_entry(
        self,
        turn_id: str,
        role: str,
        content: str
    ) -> None:
        """添加对话条目"""
        self.dialogue_window.append({
            "turn_id": turn_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        max_window = 20
        if len(self.dialogue_window) > max_window:
            self.dialogue_window = self.dialogue_window[-max_window:]
    
    def add_pending_promise(self, content: str) -> None:
        """添加待跟进承诺"""
        self.pending_promises.append({
            "content": content,
            "created_at": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "active_topic": self.active_topic,
            "emotion_trace": self.emotion_trace,
            "dialogue_window": self.dialogue_window,
            "pending_questions": self.pending_questions,
            "pending_promises": self.pending_promises,
            "latent_world_hooks": self.latent_world_hooks,
            "salience": self.salience,
            "ttl_minutes": self.ttl_minutes
        }


@dataclass
class EpisodicEvent:
    """
    事件记忆文档
    
    记录"发生过什么"，带有情绪、情境、后果的事件档案
    """
    event_id: str
    event_type: str
    summary: str
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed_at: datetime = field(default_factory=datetime.now)
    
    participants: List[str] = field(default_factory=list)
    scene: Optional[str] = None
    source_session_id: Optional[str] = None
    
    emotion: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    emotional_weight: float = 0.5
    relationship_impact: float = 0.0
    world_impact: float = 0.0
    
    followup_needed: bool = False
    followup_hint: Optional[str] = None
    
    retention_score: float = 0.5
    decay_rate: float = 0.05
    status: str = "active"
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_retention_score(self) -> float:
        """
        计算保留分数
        
        公式: retention_score = 0.45 * importance + 0.45 * emotional_weight + 0.10 * revisit_bonus
        """
        revisit_bonus = 0.1 if self.last_accessed_at > datetime.now() - timedelta(days=7) else 0
        
        self.retention_score = (
            0.45 * self.importance +
            0.45 * self.emotional_weight +
            0.10 * revisit_bonus
        )
        
        return self.retention_score
    
    def apply_decay(self, days_passed: int) -> float:
        """
        应用衰减
        
        公式: current_score = retention_score - decay_rate * days_passed
        """
        current_score = self.retention_score - self.decay_rate * days_passed
        return max(0, current_score)
    
    def determine_decay_rate(self) -> None:
        """根据情绪权重确定衰减率"""
        if self.emotional_weight >= 0.8 and self.relationship_impact >= 0.5:
            self.decay_rate = 0.01
        elif self.emotional_weight >= 0.7:
            self.decay_rate = 0.015
        elif self.emotional_weight >= 0.5:
            self.decay_rate = 0.03
        else:
            self.decay_rate = 0.05
    
    def should_delete(self, days_passed: int) -> bool:
        """判断是否应该删除"""
        current_score = self.apply_decay(days_passed)
        return current_score < 0.20
    
    def should_compress(self, days_passed: int) -> bool:
        """判断是否应该压缩为摘要"""
        current_score = self.apply_decay(days_passed)
        return 0.20 <= current_score < 0.35
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "summary": self.summary,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "participants": self.participants,
            "scene": self.scene,
            "source_session_id": self.source_session_id,
            "emotion": self.emotion,
            "importance": self.importance,
            "emotional_weight": self.emotional_weight,
            "relationship_impact": self.relationship_impact,
            "world_impact": self.world_impact,
            "followup_needed": self.followup_needed,
            "followup_hint": self.followup_hint,
            "retention_score": self.retention_score,
            "decay_rate": self.decay_rate,
            "status": self.status,
            "metadata": self.metadata
        }


@dataclass
class LongTermMemory:
    """
    长期记忆文档
    
    保存"以后都应该记得的事实"，角色事实库
    """
    memory_id: str
    category: str
    entity: str
    slot: str
    value: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    confidence: float = 0.8
    source: str = "inferred"
    source_session_id: Optional[str] = None
    access_count: int = 0
    status: str = "active"
    conflict_policy: str = "replace_or_merge"
    nearly_permanent: bool = True
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_value(self, new_value: str, confidence: float = None) -> None:
        """更新值"""
        self.value = new_value
        if confidence is not None:
            self.confidence = confidence
        self.updated_at = datetime.now()
    
    def increment_access(self) -> None:
        """增加访问计数"""
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "category": self.category,
            "entity": self.entity,
            "slot": self.slot,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confidence": self.confidence,
            "source": self.source,
            "source_session_id": self.source_session_id,
            "access_count": self.access_count,
            "status": self.status,
            "conflict_policy": self.conflict_policy,
            "nearly_permanent": self.nearly_permanent,
            "metadata": self.metadata
        }


class MemoryDocumentStore:
    """
    记忆文档存储
    
    统一管理三层记忆文档的读写
    """
    
    def __init__(
        self,
        storage_dir: Optional[str] = None,
        core_memory=None,
        episodic_memory=None,
        working_memory=None
    ):
        self.storage_dir = storage_dir
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
        
        self._short_term_sessions: Dict[str, ShortTermSession] = {}
        self._episodic_events: Dict[str, EpisodicEvent] = {}
        self._long_term_memories: Dict[str, LongTermMemory] = {}
        
        self._event_counter = 0
        self._memory_counter = 0
    
    def create_session(
        self,
        session_id: str,
        ttl_minutes: int = 10
    ) -> ShortTermSession:
        """创建短期记忆会话"""
        session = ShortTermSession(
            session_id=session_id,
            ttl_minutes=ttl_minutes
        )
        self._short_term_sessions[session_id] = session
        logger.info(f"创建短期记忆会话: {session_id}, TTL={ttl_minutes}分钟")
        return session
    
    def get_session(self, session_id: str) -> Optional[ShortTermSession]:
        """获取短期记忆会话"""
        session = self._short_term_sessions.get(session_id)
        if session:
            session.refresh()
        return session
    
    def update_session(
        self,
        session_id: str,
        topic: Optional[str] = None,
        emotion_trace: Optional[Dict[str, Any]] = None,
        dialogue_entry: Optional[Dict[str, Any]] = None,
        pending_promise: Optional[str] = None
    ) -> Optional[ShortTermSession]:
        """更新短期记忆会话"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        if topic:
            session.active_topic = topic
        
        if emotion_trace:
            session.add_emotion_trace(
                turn_id=emotion_trace.get("turn_id", ""),
                primary_emotion=emotion_trace.get("primary_emotion", ""),
                intensity=emotion_trace.get("intensity", 0)
            )
        
        if dialogue_entry:
            session.add_dialogue_entry(
                turn_id=dialogue_entry.get("turn_id", ""),
                role=dialogue_entry.get("role", ""),
                content=dialogue_entry.get("content", "")
            )
        
        if pending_promise:
            session.add_pending_promise(pending_promise)
        
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """删除短期记忆会话"""
        if session_id in self._short_term_sessions:
            del self._short_term_sessions[session_id]
            logger.info(f"删除短期记忆会话: {session_id}")
            return True
        return False
    
    def get_expired_sessions(self) -> List[ShortTermSession]:
        """获取所有过期的会话"""
        return [
            session for session in self._short_term_sessions.values()
            if session.is_expired()
        ]
    
    def create_episodic_event(
        self,
        event_type: str,
        summary: str,
        importance: float = 0.5,
        emotional_weight: float = 0.5,
        relationship_impact: float = 0.0,
        participants: List[str] = None,
        source_session_id: str = None,
        followup_needed: bool = False,
        followup_hint: str = None,
        emotion: Dict[str, Any] = None
    ) -> EpisodicEvent:
        """创建事件记忆"""
        self._event_counter += 1
        event_id = f"evt_{datetime.now().strftime('%Y%m%d')}_{self._event_counter:04d}"
        
        event = EpisodicEvent(
            event_id=event_id,
            event_type=event_type,
            summary=summary,
            importance=importance,
            emotional_weight=emotional_weight,
            relationship_impact=relationship_impact,
            participants=participants or [],
            source_session_id=source_session_id,
            followup_needed=followup_needed,
            followup_hint=followup_hint,
            emotion=emotion or {}
        )
        
        event.determine_decay_rate()
        event.calculate_retention_score()
        
        self._episodic_events[event_id] = event
        logger.info(f"创建事件记忆: {event_id}, type={event_type}, importance={importance:.2f}")
        
        return event
    
    def get_event(self, event_id: str) -> Optional[EpisodicEvent]:
        """获取事件记忆"""
        event = self._episodic_events.get(event_id)
        if event:
            event.last_accessed_at = datetime.now()
        return event
    
    def search_events(
        self,
        query: str,
        limit: int = 10
    ) -> List[EpisodicEvent]:
        """搜索事件记忆"""
        results = []
        query_lower = query.lower()
        
        for event in self._episodic_events.values():
            if event.status != "active":
                continue
            
            if query_lower in event.summary.lower():
                results.append(event)
            elif any(query_lower in p.lower() for p in event.participants):
                results.append(event)
        
        results.sort(key=lambda e: e.retention_score, reverse=True)
        return results[:limit]
    
    def get_recent_events(self, limit: int = 10) -> List[EpisodicEvent]:
        """获取最近事件"""
        events = [
            e for e in self._episodic_events.values()
            if e.status == "active"
        ]
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:limit]
    
    def create_long_term_memory(
        self,
        category: str,
        entity: str,
        slot: str,
        value: str,
        confidence: float = 0.8,
        source: str = "inferred",
        source_session_id: str = None
    ) -> LongTermMemory:
        """创建长期记忆"""
        existing = self._find_conflicting_memory(category, entity, slot)
        
        if existing:
            return self._handle_conflict(existing, value, confidence, source)
        
        self._memory_counter += 1
        memory_id = f"ltm_{category[:3]}_{self._memory_counter:04d}"
        
        memory = LongTermMemory(
            memory_id=memory_id,
            category=category,
            entity=entity,
            slot=slot,
            value=value,
            confidence=confidence,
            source=source,
            source_session_id=source_session_id
        )
        
        self._long_term_memories[memory_id] = memory
        logger.info(f"创建长期记忆: {memory_id}, category={category}, value={value[:30]}...")
        
        return memory
    
    def _find_conflicting_memory(
        self,
        category: str,
        entity: str,
        slot: str
    ) -> Optional[LongTermMemory]:
        """查找冲突的长期记忆"""
        for memory in self._long_term_memories.values():
            if (memory.category == category and
                memory.entity == entity and
                memory.slot == slot):
                return memory
        return None
    
    def _handle_conflict(
        self,
        existing: LongTermMemory,
        new_value: str,
        confidence: float,
        source: str
    ) -> LongTermMemory:
        """处理冲突"""
        if existing.conflict_policy == "replace_or_merge":
            if confidence >= existing.confidence:
                existing.update_value(new_value, confidence)
                existing.source = source
                logger.info(f"更新长期记忆: {existing.memory_id}, 新值={new_value[:30]}...")
            else:
                logger.debug(f"保留现有长期记忆（置信度更高）: {existing.memory_id}")
        
        return existing
    
    def get_long_term_memories(
        self,
        category: str = None,
        entity: str = None
    ) -> List[LongTermMemory]:
        """获取长期记忆"""
        results = []
        
        for memory in self._long_term_memories.values():
            if memory.status != "active":
                continue
            
            if category and memory.category != category:
                continue
            if entity and memory.entity != entity:
                continue
            
            results.append(memory)
        
        return results
    
    def search_long_term(
        self,
        query: str,
        limit: int = 10
    ) -> List[LongTermMemory]:
        """搜索长期记忆"""
        results = []
        query_lower = query.lower()
        
        for memory in self._long_term_memories.values():
            if memory.status != "active":
                continue
            
            if query_lower in memory.value.lower():
                results.append(memory)
        
        results.sort(key=lambda m: m.confidence, reverse=True)
        return results[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "short_term_sessions": len(self._short_term_sessions),
            "episodic_events": len(self._episodic_events),
            "long_term_memories": len(self._long_term_memories),
            "active_events": len([e for e in self._episodic_events.values() if e.status == "active"]),
            "expired_sessions": len(self.get_expired_sessions())
        }
