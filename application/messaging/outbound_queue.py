"""
出站消息队列

V5 核心组件：管理待发送消息。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    RESPONSE = "response"
    PROACTIVE = "proactive"
    NOTIFICATION = "notification"


@dataclass
class OutboundMessage:
    """
    出站消息
    
    统一字段说明：
    - id: 消息 ID
    - message_type: 消息类型（MessageType 枚举）
    - content: 消息内容
    - metadata: 元数据
    - created_at: 创建时间
    - delivered: 是否已发送
    - delivered_at: 发送时间
    """
    id: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    delivered: bool = False
    delivered_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered": self.delivered,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None
        }


class OutboundQueue:
    """
    出站消息队列
    
    管理待发送的消息。
    """
    
    def __init__(self, memory_service=None, max_size: int = 100):
        self.memory_service = memory_service
        self.max_size = max_size
        self._queue: List[OutboundMessage] = []
    
    async def enqueue(self, message: OutboundMessage) -> None:
        """入队"""
        self._queue.append(message)
        
        if len(self._queue) > self.max_size:
            self._queue = self._queue[-self.max_size:]
        
        logger.debug(f"消息入队: {message.id}")
    
    def get_pending(self, limit: int = 20) -> List[OutboundMessage]:
        """获取待发送消息"""
        return [m for m in self._queue if not m.delivered][:limit]
    
    async def mark_delivered(self, message_id: str) -> bool:
        """标记已发送"""
        for msg in self._queue:
            if msg.id == message_id:
                msg.delivered = True
                msg.delivered_at = datetime.now()
                logger.debug(f"消息已发送: {message_id}")
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        total = len(self._queue)
        delivered = sum(1 for m in self._queue if m.delivered)
        pending = total - delivered
        
        return {
            "total": total,
            "delivered": delivered,
            "pending": pending
        }
