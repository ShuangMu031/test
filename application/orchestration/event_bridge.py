"""
事件桥接器

V5 核心组件：只负责事件订阅和发布。
从 coordinator 中分离出来，职责单一。

管理：
- 事件订阅
- 事件发布
- 事件处理器绑定
"""

from typing import Dict, Any, List, Callable, Optional
import logging

from infrastructure.events.bus import global_event_bus, EventType

logger = logging.getLogger(__name__)


class EventBridge:
    """
    事件桥接器
    
    只负责事件的订阅和发布：
    1. 管理事件处理器
    2. 绑定/解绑事件
    3. 发布事件
    
    不负责：
    - 业务逻辑
    - 后台任务
    - 对话编排
    """
    
    def __init__(self):
        self._handlers: List[tuple] = []
        self._is_bound = False
    
    def bind(self) -> None:
        """绑定所有事件处理器"""
        if self._is_bound:
            return
        
        for event_type, handler in self._handlers:
            global_event_bus.subscribe(event_type, handler)
        
        self._is_bound = True
        logger.info(f"EventBridge 已绑定 {len(self._handlers)} 个事件处理器")
    
    def unbind(self) -> None:
        """解绑所有事件处理器"""
        if not self._is_bound:
            return
        
        for event_type, handler in self._handlers:
            global_event_bus.unsubscribe(event_type, handler)
        
        self._handlers.clear()
        self._is_bound = False
        logger.info("EventBridge 已解绑所有事件处理器")
    
    def register(
        self,
        event_type: EventType,
        handler: Callable
    ) -> None:
        """注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        self._handlers.append((event_type, handler))
        logger.debug(f"注册事件处理器: {event_type}")
    
    def register_batch(
        self,
        handlers: List[tuple]
    ) -> None:
        """批量注册事件处理器
        
        Args:
            handlers: [(event_type, handler), ...]
        """
        for event_type, handler in handlers:
            self.register(event_type, handler)
    
    def publish(
        self,
        event_type: EventType,
        data: Any
    ) -> None:
        """发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        global_event_bus.publish(event_type, data)
    
    def get_handlers(self) -> List[tuple]:
        """获取所有已注册的处理器"""
        return self._handlers.copy()
    
    def is_bound(self) -> bool:
        """检查是否已绑定"""
        return self._is_bound
