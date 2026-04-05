"""
世界知识领域模型

V9 第五批新增：定义"虚拟世界内容"的正式模型

把现实素材（新闻、天气等）转成虚拟世界内容，
不直接把新闻原文塞进世界。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class WorldContentType(Enum):
    """世界内容类型"""
    BULLETIN = "bulletin"
    RUMOR = "rumor"
    BRIEF = "brief"
    WEATHER_FEED = "weather_feed"
    NEWS = "news"
    EVENT = "event"


class WorldTopicTag(Enum):
    """世界话题标签"""
    DAILY_LIFE = "daily_life"
    WEATHER = "weather"
    SOCIAL = "social"
    ECONOMY = "economy"
    CULTURE = "culture"
    SPORTS = "sports"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    LOCAL = "local"
    GLOBAL = "global"


class ImpactLevel(Enum):
    """影响级别"""
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class WorldContentImpact:
    """
    世界内容影响
    
    描述内容对世界的影响范围和程度
    """
    level: ImpactLevel = ImpactLevel.LOW
    affected_locations: List[str] = field(default_factory=list)
    affected_npcs: List[str] = field(default_factory=list)
    duration_hours: int = 24
    decay_rate: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "affected_locations": self.affected_locations,
            "affected_npcs": self.affected_npcs,
            "duration_hours": self.duration_hours,
            "decay_rate": self.decay_rate
        }


@dataclass
class WorldContentItem:
    """
    世界内容项
    
    虚拟世界中的正式内容单元
    """
    id: str
    content_type: WorldContentType
    title: str
    content: str
    summary: str = ""
    
    source_type: str = ""
    source_id: str = ""
    original_signal_id: str = ""
    
    topic_tags: List[WorldTopicTag] = field(default_factory=list)
    
    impact: Optional[WorldContentImpact] = None
    
    world_text: str = ""
    
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    expires_at: Optional[float] = None
    
    importance: float = 0.5
    confidence: float = 1.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now().timestamp() > self.expires_at
    
    def get_current_importance(self) -> float:
        """获取当前重要性（考虑衰减）"""
        if self.impact is None:
            return self.importance
        
        age_hours = (datetime.now().timestamp() - self.created_at) / 3600
        decayed = self.importance * (1 - self.impact.decay_rate * age_hours)
        return max(0.0, min(1.0, decayed))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content_type": self.content_type.value,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "original_signal_id": self.original_signal_id,
            "topic_tags": [tag.value for tag in self.topic_tags],
            "impact": self.impact.to_dict() if self.impact else None,
            "world_text": self.world_text,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "importance": self.importance,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldContentItem":
        """从字典创建"""
        impact_data = data.get("impact")
        impact = None
        if impact_data:
            impact = WorldContentImpact(
                level=ImpactLevel(impact_data.get("level", 1)),
                affected_locations=impact_data.get("affected_locations", []),
                affected_npcs=impact_data.get("affected_npcs", []),
                duration_hours=impact_data.get("duration_hours", 24),
                decay_rate=impact_data.get("decay_rate", 0.1)
            )
        
        topic_tags = []
        for tag_value in data.get("topic_tags", []):
            try:
                topic_tags.append(WorldTopicTag(tag_value))
            except ValueError:
                pass
        
        return cls(
            id=data.get("id", ""),
            content_type=WorldContentType(data.get("content_type", "brief")),
            title=data.get("title", ""),
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            source_type=data.get("source_type", ""),
            source_id=data.get("source_id", ""),
            original_signal_id=data.get("original_signal_id", ""),
            topic_tags=topic_tags,
            impact=impact,
            world_text=data.get("world_text", ""),
            created_at=data.get("created_at", datetime.now().timestamp()),
            expires_at=data.get("expires_at"),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 1.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class WorldKnowledgeQuery:
    """
    世界知识查询
    
    用于检索世界内容
    """
    query_text: str = ""
    content_types: List[WorldContentType] = field(default_factory=list)
    topic_tags: List[WorldTopicTag] = field(default_factory=list)
    min_importance: float = 0.0
    max_age_hours: Optional[float] = None
    limit: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "content_types": [ct.value for ct in self.content_types],
            "topic_tags": [tag.value for tag in self.topic_tags],
            "min_importance": self.min_importance,
            "max_age_hours": self.max_age_hours,
            "limit": self.limit
        }
