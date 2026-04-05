"""
最小世界接口

V9 改版：只保留 5 个只读方法

根据改版意见：
- 先别急着上观察对话、场景快照、坐标移动、双向绑定、混合模式
- 先缩成最小可用集
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorldSnapshot:
    """
    世界快照
    
    V9 改版：添加调试字段
    """
    snapshot_id: str
    world_time: str
    weather: str
    location: str
    npcs: List[Dict[str, Any]] = field(default_factory=list)
    recent_events: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    version: int = 1
    time_period: str = "白天"
    energy: float = 0.8
    hunger: float = 0.3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "world_time": self.world_time,
            "weather": self.weather,
            "location": self.location,
            "npcs": self.npcs,
            "recent_events": self.recent_events,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "time_period": self.time_period,
            "energy": self.energy,
            "hunger": self.hunger
        }


@dataclass
class WorldEvent:
    """世界事件"""
    event_id: str
    event_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    participants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "participants": self.participants,
            "metadata": self.metadata
        }


class WorldRuntimePort(ABC):
    """
    世界运行时端口 - 最小接口
    
    V9 改版：只保留 5 个只读方法
    """
    
    @abstractmethod
    async def get_world_snapshot(self) -> WorldSnapshot:
        """
        获取世界快照
        
        返回当前世界的完整状态
        """
        pass
    
    @abstractmethod
    async def get_recent_events(self, limit: int = 10) -> List[WorldEvent]:
        """
        获取最近事件
        
        返回最近发生的世界事件
        """
        pass
    
    @abstractmethod
    async def get_npcs_at_location(self, location: str) -> List[Dict[str, Any]]:
        """
        获取指定位置的 NPC
        
        返回当前在该位置的 NPC 列表
        """
        pass
    
    @abstractmethod
    async def inject_user_actor(self, user_id: str) -> str:
        """
        注入用户角色
        
        将用户角色注入到世界中
        返回角色 ID
        """
        pass
    
    @abstractmethod
    async def enqueue_world_action(self, action: Dict[str, Any]) -> bool:
        """
        提交世界动作
        
        将动作加入世界队列
        """
        pass
