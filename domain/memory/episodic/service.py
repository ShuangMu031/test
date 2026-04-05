"""
事件层记忆

V9 三层记忆 - 第二层

职责：
- 世界重大事件
- 用户强刺激互动
- 高情绪阈值事件
- 持续影响 NPC 的事

特点：
- 有权重
- 有保留期
- 可衰减
- 会进时间轴
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math


class EpisodicEventType(Enum):
    """事件类型"""
    WORLD_EVENT = "world_event"
    USER_INTERACTION = "user_interaction"
    EMOTIONAL_PEAK = "emotional_peak"
    RELATIONSHIP_CHANGE = "relationship_change"
    LEARNING = "learning"


@dataclass
class EpisodicMemoryEntry:
    """事件记忆条目"""
    event_id: str
    event_type: EpisodicEventType
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 0.5
    emotional_impact: float = 0.0
    decay_rate: float = 0.01
    retention_days: int = 30
    participants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "emotional_impact": self.emotional_impact,
            "decay_rate": self.decay_rate,
            "retention_days": self.retention_days,
            "participants": self.participants,
            "metadata": self.metadata
        }
    
    def get_current_importance(self) -> float:
        """获取当前重要性（考虑衰减）"""
        days_passed = (datetime.now() - self.timestamp).days
        decayed = self.importance * math.exp(-self.decay_rate * days_passed)
        return max(0, decayed)


class EpisodicMemoryService:
    """
    事件记忆服务
    
    管理角色的事件层记忆
    """
    
    def __init__(self):
        self._entries: List[EpisodicMemoryEntry] = []
    
    def add_event(
        self,
        event_type: EpisodicEventType,
        description: str,
        importance: float = 0.5,
        emotional_impact: float = 0.0,
        participants: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> EpisodicMemoryEntry:
        """添加事件"""
        event_id = f"epi_{datetime.now().timestamp()}"
        entry = EpisodicMemoryEntry(
            event_id=event_id,
            event_type=event_type,
            description=description,
            importance=importance,
            emotional_impact=emotional_impact,
            participants=participants or [],
            metadata=metadata or {}
        )
        self._entries.append(entry)
        return entry
    
    def get_recent_events(self, limit: int = 10) -> List[EpisodicMemoryEntry]:
        """获取最近事件"""
        sorted_entries = sorted(self._entries, key=lambda x: x.timestamp, reverse=True)
        return sorted_entries[:limit]
    
    def get_important_events(self, threshold: float = 0.5) -> List[EpisodicMemoryEntry]:
        """获取重要事件"""
        return [e for e in self._entries if e.get_current_importance() >= threshold]
    
    def get_events_by_type(self, event_type: EpisodicEventType) -> List[EpisodicMemoryEntry]:
        """按类型获取事件"""
        return [e for e in self._entries if e.event_type == event_type]
    
    def cleanup_expired(self) -> int:
        """清理过期事件"""
        now = datetime.now()
        before = len(self._entries)
        self._entries = [
            e for e in self._entries
            if (now - e.timestamp).days < e.retention_days
        ]
        return before - len(self._entries)
    
    def to_prompt_context(self, limit: int = 5) -> str:
        """生成 Prompt 上下文"""
        recent = self.get_recent_events(limit)
        if not recent:
            return ""
        
        parts = ["最近重要事件:"]
        for event in recent:
            time_str = event.timestamp.strftime("%m-%d %H:%M")
            parts.append(f"- [{time_str}] {event.description}")
        
        return "\n".join(parts)
    
    def add_memory_event(
        self,
        description: str,
        importance: float = 0.5,
        emotional_impact: float = 0.0,
        event_type: EpisodicEventType = None,
        metadata: Dict[str, Any] = None
    ) -> EpisodicMemoryEntry:
        """添加记忆事件（V9 主链接口）"""
        return self.add_event(
            event_type=event_type or EpisodicEventType.USER_INTERACTION,
            description=description,
            importance=importance,
            emotional_impact=emotional_impact,
            metadata=metadata
        )
    
    def search_events(self, query: str, limit: int = 5) -> List[EpisodicMemoryEntry]:
        """
        搜索事件
        
        V9 修复：添加搜索方法供 MemoryFacade 使用
        
        Args:
            query: 查询文本
            limit: 返回数量限制
            
        Returns:
            匹配的事件列表
        """
        query_lower = query.lower()
        matches = []
        
        for entry in self._entries:
            if query_lower in entry.description.lower():
                matches.append(entry)
            elif query_lower in str(entry.event_type.value).lower():
                matches.append(entry)
            elif any(query_lower in str(p).lower() for p in entry.participants):
                matches.append(entry)
        
        sorted_matches = sorted(matches, key=lambda x: x.timestamp, reverse=True)
        return sorted_matches[:limit]
    
    def get_all_entries(self) -> List[EpisodicMemoryEntry]:
        """获取所有条目"""
        return list(self._entries)
    
    def get_context_for_prompt(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取用于 prompt 的上下文（V9 主链接口）"""
        recent = self.get_recent_events(limit)
        return [e.to_dict() for e in recent]
