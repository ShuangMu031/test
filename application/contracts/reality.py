"""
现实素材相关 Schema

V6 统一字段体系：
- RealitySignal: 现实素材（唯一正式定义）
- RealitySignalType: 素材类型枚举

注意：全项目只能保留这一份 RealitySignal 定义。
domain/reality_feed/models.py 中的定义应废弃并重定向到此文件。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class RealitySignalType(Enum):
    """
    现实素材类型
    
    - WEATHER: 天气数据
    - NEWS: 新闻数据
    - HOLIDAY: 节日数据
    - TIME: 时间信息
    - LOCATION: 地点信息
    """
    WEATHER = "weather"
    NEWS = "news"
    HOLIDAY = "holiday"
    TIME = "time"
    LOCATION = "location"


@dataclass
class RealitySignal:
    """
    现实素材
    
    代表从现实世界采集的一条原始素材。
    这些素材将被转译器转换为虚拟世界内容。
    
    重要：现实素材只用于生成世界内容，不直接影响 Agent 状态。
    
    统一字段说明：
    - signal_id: 唯一标识符
    - signal_type: 素材类型（RealitySignalType 枚举）
    - title: 标题
    - raw_text: 原始文本
    - payload: 负载数据
    - collected_at: 采集时间戳
    - source: 来源
    - metadata: 元数据
    """
    signal_id: str = field(default_factory=lambda: f"rs_{uuid.uuid4().hex[:8]}")
    signal_type: RealitySignalType = RealitySignalType.NEWS
    title: str = ""
    raw_text: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    collected_at: float = field(default_factory=lambda: datetime.now().timestamp())
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "title": self.title,
            "raw_text": self.raw_text,
            "payload": self.payload,
            "collected_at": self.collected_at,
            "source": self.source,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RealitySignal":
        return cls(
            signal_id=data.get("signal_id", f"rs_{uuid.uuid4().hex[:8]}"),
            signal_type=RealitySignalType(data.get("signal_type", "news")),
            title=data.get("title", ""),
            raw_text=data.get("raw_text", ""),
            payload=data.get("payload", {}),
            collected_at=data.get("collected_at", datetime.now().timestamp()),
            source=data.get("source", "unknown"),
            metadata=data.get("metadata", {})
        )


@dataclass
class WeatherSignal(RealitySignal):
    """
    天气素材
    
    特化的天气数据素材。
    """
    signal_type: RealitySignalType = field(default=RealitySignalType.WEATHER, init=False)
    
    @property
    def weather(self) -> str:
        return self.payload.get("weather", "unknown")
    
    @property
    def temperature(self) -> Optional[float]:
        return self.payload.get("temperature")
    
    @property
    def humidity(self) -> Optional[float]:
        return self.payload.get("humidity")
    
    @property
    def city(self) -> str:
        return self.payload.get("city", "unknown")


@dataclass
class NewsSignal(RealitySignal):
    """
    新闻素材
    
    特化的新闻数据素材。
    """
    signal_type: RealitySignalType = field(default=RealitySignalType.NEWS, init=False)
    
    @property
    def category(self) -> str:
        return self.payload.get("category", "general")
    
    @property
    def url(self) -> Optional[str]:
        return self.payload.get("url")


@dataclass
class HolidaySignal(RealitySignal):
    """
    节日素材
    
    特化的节日数据素材。
    """
    signal_type: RealitySignalType = field(default=RealitySignalType.HOLIDAY, init=False)
    
    @property
    def holiday_name(self) -> str:
        return self.payload.get("name", "")
    
    @property
    def date(self) -> str:
        return self.payload.get("date", "")


@dataclass
class TimeSignal(RealitySignal):
    """
    时间素材
    
    特化的时间信息素材。
    """
    signal_type: RealitySignalType = field(default=RealitySignalType.TIME, init=False)
    
    @property
    def current_time(self) -> str:
        return self.payload.get("time", "")
    
    @property
    def day_of_week(self) -> str:
        return self.payload.get("day_of_week", "")
    
    @property
    def is_weekend(self) -> bool:
        return self.payload.get("is_weekend", False)


@dataclass
class ProactiveMessageCandidate:
    """
    主动消息候选
    
    用于主动交互系统的消息候选。
    
    统一字段说明：
    - candidate_id: 候选 ID
    - trigger_type: 触发类型
    - content: 消息内容
    - priority: 优先级 (1-10)
    - scheduled_time: 计划发送时间
    - conditions: 发送条件
    - metadata: 元数据
    """
    candidate_id: str = field(default_factory=lambda: f"pm_{uuid.uuid4().hex[:8]}")
    trigger_type: str = "time_based"
    content: str = ""
    priority: int = 5
    scheduled_time: Optional[float] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "trigger_type": self.trigger_type,
            "content": self.content,
            "priority": self.priority,
            "scheduled_time": self.scheduled_time,
            "conditions": self.conditions,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProactiveMessageCandidate":
        return cls(
            candidate_id=data.get("candidate_id", f"pm_{uuid.uuid4().hex[:8]}"),
            trigger_type=data.get("trigger_type", "time_based"),
            content=data.get("content", ""),
            priority=data.get("priority", 5),
            scheduled_time=data.get("scheduled_time"),
            conditions=data.get("conditions", {}),
            metadata=data.get("metadata", {})
        )
