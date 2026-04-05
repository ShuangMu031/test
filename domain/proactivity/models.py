"""
主动交互领域模型

V9 改版：从随机提醒改成条件触发

定义主动交互相关的数据结构和接口。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TriggerType(Enum):
    """触发类型"""
    IDLE = "idle"
    EMOTION = "emotion"
    TIME = "time"
    VIRTUAL_EVENT = "virtual_event"
    TYPING = "typing"
    WORLD_EVENT = "world_event"
    PROMISE_FOLLOWUP = "promise_followup"
    RELATIONSHIP_PUSH = "relationship_push"


class ProactivePriority(Enum):
    """主动消息优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


@dataclass
class ProactiveContext:
    """
    V10: 主动交互上下文
    
    包含判断是否应该主动交互所需的所有信息
    """
    idle_seconds: float = 0.0
    
    last_emotion: Optional[str] = None
    last_emotion_valence: float = 0.0
    last_support_need: str = "none"
    
    last_world_event: Optional[str] = None
    last_world_event_time: Optional[datetime] = None
    
    last_commit_summary: str = ""
    
    cooldowns: Dict[str, float] = field(default_factory=dict)
    
    pending_promises: List[str] = field(default_factory=list)
    
    recent_npc_interactions: List[str] = field(default_factory=list)
    
    world_snapshot_available: bool = False
    
    def is_in_cooldown(self, trigger_type: str) -> bool:
        """检查是否在冷却中"""
        if trigger_type not in self.cooldowns:
            return False
        return self.cooldowns[trigger_type] > 0
    
    def get_cooldown_remaining(self, trigger_type: str) -> float:
        """获取剩余冷却时间"""
        return self.cooldowns.get(trigger_type, 0.0)


@dataclass
class ProactiveDecision:
    """
    V10: 主动交互决策
    
    表示主动交互的决策结果
    """
    should_send: bool = False
    
    priority: float = 0.0
    
    reason: str = ""
    
    trigger_type: TriggerType = TriggerType.IDLE
    
    needs_world_context: bool = False
    
    needs_emotional_style: bool = False
    
    suggested_content: str = ""
    
    target_npc_id: Optional[str] = None
    
    cooldown_seconds: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_send": self.should_send,
            "priority": self.priority,
            "reason": self.reason,
            "trigger_type": self.trigger_type.value,
            "needs_world_context": self.needs_world_context,
            "needs_emotional_style": self.needs_emotional_style,
            "suggested_content": self.suggested_content,
            "target_npc_id": self.target_npc_id,
            "cooldown_seconds": self.cooldown_seconds
        }


@dataclass
class ProactiveMessage:
    """
    主动消息
    
    Attributes:
        content: 消息内容
        trigger_type: 触发类型
        priority: 优先级
        timestamp: 时间戳
        decision: 关联的决策
    """
    content: str
    trigger_type: TriggerType
    priority: int
    timestamp: float
    decision: Optional[ProactiveDecision] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "trigger_type": self.trigger_type.value,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "decision": self.decision.to_dict() if self.decision else None
        }


@dataclass
class TriggerCondition:
    """
    触发条件
    
    Attributes:
        trigger_type: 触发类型
        priority: 优先级
        cooldown: 冷却时间（秒）
        last_trigger_time: 上次触发时间
    """
    trigger_type: TriggerType
    priority: int
    cooldown: int
    last_trigger_time: float = 0.0
    
    def should_trigger(self, context: ProactiveContext) -> bool:
        """
        判断是否应该触发
        
        Args:
            context: 主动交互上下文
            
        Returns:
            是否应该触发
        """
        if context.is_in_cooldown(self.trigger_type.value):
            return False
        
        if self.trigger_type == TriggerType.IDLE:
            return context.idle_seconds >= 1800
        
        if self.trigger_type == TriggerType.EMOTION:
            if context.last_support_need == "high":
                return context.idle_seconds >= 600
            if context.last_support_need == "medium":
                return context.idle_seconds >= 1200
            return False
        
        if self.trigger_type == TriggerType.WORLD_EVENT:
            return context.world_snapshot_available and context.last_world_event is not None
        
        if self.trigger_type == TriggerType.PROMISE_FOLLOWUP:
            return len(context.pending_promises) > 0
        
        if self.trigger_type == TriggerType.RELATIONSHIP_PUSH:
            return len(context.recent_npc_interactions) > 0
        
        return False


@dataclass
class ProactiveCandidate:
    """
    V10: 主动交互候选
    
    表示一个可能的主动交互候选
    """
    trigger_type: TriggerType
    priority: float
    reason: str
    suggested_content: str = ""
    needs_world_context: bool = False
    needs_emotional_style: bool = False
    target_npc_id: Optional[str] = None
    cooldown_seconds: int = 300
    
    def to_decision(self, should_send: bool = True) -> ProactiveDecision:
        """转换为决策"""
        return ProactiveDecision(
            should_send=should_send,
            priority=self.priority,
            reason=self.reason,
            trigger_type=self.trigger_type,
            needs_world_context=self.needs_world_context,
            needs_emotional_style=self.needs_emotional_style,
            suggested_content=self.suggested_content,
            target_npc_id=self.target_npc_id,
            cooldown_seconds=self.cooldown_seconds
        )
