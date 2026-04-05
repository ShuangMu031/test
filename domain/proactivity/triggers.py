"""
触发器模块

包含各种主动交互触发器的实现。
"""

from typing import Dict, Any
from datetime import datetime

from domain.proactivity.models import TriggerCondition, TriggerType


def get_valence(emotional_state: Any) -> float:
    """
    安全获取情绪效价值
    
    Args:
        emotional_state: 情绪状态对象或字典
        
    Returns:
        效价值
    """
    if emotional_state is None:
        return 0.0
    
    if hasattr(emotional_state, 'valence'):
        return emotional_state.valence
    
    if isinstance(emotional_state, dict):
        return emotional_state.get('valence', 0.0)
    
    return 0.0


class IdleTrigger(TriggerCondition):
    """
    空闲触发器
    """
    
    def __init__(self, cooldown: int = 300, priority: int = 5):
        """
        初始化空闲触发器
        
        Args:
            cooldown: 冷却时间
            priority: 优先级
        """
        super().__init__(TriggerType.IDLE, priority, cooldown)
        self.idle_threshold = 300
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        判断是否应该触发
        
        Args:
            context: 上下文信息
            
        Returns:
            是否应该触发
        """
        last_interaction_time = context.get('last_interaction_time', datetime.now().timestamp())
        current_time = datetime.now().timestamp()
        
        if current_time - self.last_trigger_time < self.cooldown:
            return False
        
        if current_time - last_interaction_time > self.idle_threshold:
            return True
        
        return False


class EmotionTrigger(TriggerCondition):
    """
    情绪触发器
    """
    
    def __init__(self, cooldown: int = 600, priority: int = 7):
        """
        初始化情绪触发器
        
        Args:
            cooldown: 冷却时间
            priority: 优先级
        """
        super().__init__(TriggerType.EMOTION, priority, cooldown)
        self.valence_threshold = -0.5
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        判断是否应该触发
        
        Args:
            context: 上下文信息
            
        Returns:
            是否应该触发
        """
        if datetime.now().timestamp() - self.last_trigger_time < self.cooldown:
            return False
        
        emotional_state = context.get('emotional_state')
        valence = get_valence(emotional_state)
        
        if valence < self.valence_threshold:
            return True
        
        return False


class TimeTrigger(TriggerCondition):
    """
    时间触发器
    """
    
    def __init__(self, cooldown: int = 3600, priority: int = 3):
        """
        初始化时间触发器
        
        Args:
            cooldown: 冷却时间
            priority: 优先级
        """
        super().__init__(TriggerType.TIME, priority, cooldown)
        self.trigger_hours = [9, 12, 18, 22]
        self.last_triggered_hour = None
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        判断是否应该触发
        
        Args:
            context: 上下文信息
            
        Returns:
            是否应该触发
        """
        now = datetime.now()
        current_hour = now.hour
        
        if current_hour not in self.trigger_hours:
            return False
        
        if self.last_triggered_hour == current_hour:
            return False
        
        if datetime.now().timestamp() - self.last_trigger_time < self.cooldown:
            return False
        
        self.last_triggered_hour = current_hour
        return True


class VirtualEventTrigger(TriggerCondition):
    """
    虚拟事件触发器
    """
    
    def __init__(self, cooldown: int = 1800, priority: int = 6):
        """
        初始化虚拟事件触发器
        
        Args:
            cooldown: 冷却时间
            priority: 优先级
        """
        super().__init__(TriggerType.VIRTUAL_EVENT, priority, cooldown)
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        判断是否应该触发
        
        Args:
            context: 上下文信息
            
        Returns:
            是否应该触发
        """
        if datetime.now().timestamp() - self.last_trigger_time < self.cooldown:
            return False
        
        recent_events = context.get('recent_events', [])
        
        if recent_events:
            return True
        
        return False


class TypingTrigger(TriggerCondition):
    """
    打字触发器
    """
    
    def __init__(self, cooldown: int = 120, priority: int = 4):
        """
        初始化打字触发器
        
        Args:
            cooldown: 冷却时间
            priority: 优先级
        """
        super().__init__(TriggerType.TYPING, priority, cooldown)
        self.last_typing_time = None
        self.typing_duration_threshold = 30
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """
        判断是否应该触发
        
        Args:
            context: 上下文信息
            
        Returns:
            是否应该触发
        """
        if datetime.now().timestamp() - self.last_trigger_time < self.cooldown:
            return False
        
        is_typing = context.get('is_typing', False)
        
        if is_typing and self.last_typing_time:
            current_time = datetime.now().timestamp()
            if current_time - self.last_typing_time > self.typing_duration_threshold:
                return True
        
        return False
