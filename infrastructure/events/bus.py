"""
事件总线模块

提供发布-订阅模式的事件系统，用于解耦各个模块之间的通信。
"""

from typing import Dict, Any, Callable, List, Optional
import asyncio
import logging
from datetime import datetime

from infrastructure.events.types import EventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    事件总线实现
    
    支持同步和异步事件处理，提供发布-订阅模式的通信机制。
    """
    
    def __init__(self):
        """初始化事件总线"""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.async_subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
    
    def subscribe(self, event_type: str, handler: Callable):
        """
        订阅同步事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        if handler not in self.subscribers[event_type]:
            self.subscribers[event_type].append(handler)
            logger.info(f"Subscribed to event '{event_type}'")
    
    def subscribe_async(self, event_type: str, handler: Callable):
        """
        订阅异步事件
        
        Args:
            event_type: 事件类型
            handler: 异步事件处理函数
        """
        if event_type not in self.async_subscribers:
            self.async_subscribers[event_type] = []
        if handler not in self.async_subscribers[event_type]:
            self.async_subscribers[event_type].append(handler)
            logger.info(f"Subscribed to async event '{event_type}'")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """
        取消订阅同步事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
        """
        if event_type in self.subscribers:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from event '{event_type}'")
    
    def unsubscribe_async(self, event_type: str, handler: Callable):
        """
        取消订阅异步事件
        
        Args:
            event_type: 事件类型
            handler: 异步事件处理函数
        """
        if event_type in self.async_subscribers:
            if handler in self.async_subscribers[event_type]:
                self.async_subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from async event '{event_type}'")
    
    def publish(self, event_type: str, data: Any):
        """
        发布同步事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self._record_event(event_type, data)
        
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error handling event '{event_type}': {e}")
    
    async def publish_async(self, event_type: str, data: Any):
        """
        发布异步事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self._record_event(event_type, data)
        
        if event_type in self.async_subscribers:
            tasks = []
            for handler in self.async_subscribers[event_type]:
                try:
                    task = asyncio.create_task(handler(data))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error creating task for async event '{event_type}': {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    def _record_event(self, event_type: str, data: Any):
        """
        记录事件历史
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        event = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
        self.event_history.append(event)
        
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
    
    def get_event_history(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取事件历史
        
        Args:
            event_type: 可选，指定事件类型
            
        Returns:
            事件历史记录
        """
        if event_type:
            return [event for event in self.event_history if event["event_type"] == event_type]
        return self.event_history
    
    def clear_event_history(self):
        """
        清空事件历史
        """
        self.event_history.clear()
        logger.info("Cleared event history")


global_event_bus = EventBus()
