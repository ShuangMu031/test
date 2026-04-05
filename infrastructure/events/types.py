"""
事件类型定义

定义系统中所有的事件类型常量。
"""

from enum import Enum


class EventType(str, Enum):
    """事件类型枚举"""
    
    EMOTION_UPDATED = "emotion_updated"
    EMOTION_DETECTED = "emotion_detected"
    
    MEMORY_STORED = "memory_stored"
    MEMORY_RETRIEVED = "memory_retrieved"
    
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    
    PROACTIVE_TRIGGERED = "proactive_triggered"
    PROACTIVE_MESSAGE_GENERATED = "proactive_message_generated"
    
    VIRTUAL_WORLD_UPDATED = "virtual_world_updated"
    VIRTUAL_EVENT_OCCURRED = "virtual_event_occurred"
    
    CHARACTER_UPDATED = "character_updated"
    CHARACTER_PERSONALITY_CHANGED = "character_personality_changed"
    
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    ERROR_OCCURRED = "error_occurred"
    
    AIRI_CONNECTED = "airi_connected"
    AIRI_DISCONNECTED = "airi_disconnected"
    
    @property
    def category(self) -> str:
        """
        获取事件类别
        
        Returns:
            事件类别名称
        """
        if self.name.startswith("EMOTION"):
            return "emotion"
        elif self.name.startswith("MEMORY"):
            return "memory"
        elif self.name.startswith("MESSAGE"):
            return "message"
        elif self.name.startswith("PROACTIVE"):
            return "proactive"
        elif self.name.startswith("VIRTUAL"):
            return "virtual_world"
        elif self.name.startswith("CHARACTER"):
            return "character"
        elif self.name.startswith("SYSTEM"):
            return "system"
        elif self.name.startswith("AIRI"):
            return "airi"
        return "other"


EVENT_CATEGORIES = {
    "emotion": [
        EventType.EMOTION_UPDATED,
        EventType.EMOTION_DETECTED
    ],
    "memory": [
        EventType.MEMORY_STORED,
        EventType.MEMORY_RETRIEVED
    ],
    "message": [
        EventType.MESSAGE_SENT,
        EventType.MESSAGE_RECEIVED
    ],
    "proactive": [
        EventType.PROACTIVE_TRIGGERED,
        EventType.PROACTIVE_MESSAGE_GENERATED
    ],
    "virtual_world": [
        EventType.VIRTUAL_WORLD_UPDATED,
        EventType.VIRTUAL_EVENT_OCCURRED
    ],
    "character": [
        EventType.CHARACTER_UPDATED,
        EventType.CHARACTER_PERSONALITY_CHANGED
    ],
    "system": [
        EventType.SYSTEM_STARTED,
        EventType.SYSTEM_STOPPED,
        EventType.ERROR_OCCURRED
    ],
    "airi": [
        EventType.AIRI_CONNECTED,
        EventType.AIRI_DISCONNECTED
    ]
}


def get_events_by_category(category: str) -> list:
    """
    获取指定类别的所有事件类型
    
    Args:
        category: 事件类别
        
    Returns:
        事件类型列表
    """
    return EVENT_CATEGORIES.get(category, [])
