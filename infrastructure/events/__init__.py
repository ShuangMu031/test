"""
事件基础设施模块

提供事件总线和事件类型定义。
"""

from infrastructure.events.bus import EventBus, global_event_bus
from infrastructure.events.types import EventType, EVENT_CATEGORIES, get_events_by_category

__all__ = [
    "EventBus",
    "global_event_bus",
    "EventType",
    "EVENT_CATEGORIES",
    "get_events_by_category"
]
