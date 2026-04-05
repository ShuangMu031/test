"""
消息模块

V5 核心组件：消息管理。
"""

from .outbound_queue import OutboundQueue, OutboundMessage
from .response_models import AgentResponse

__all__ = [
    "OutboundQueue",
    "OutboundMessage",
    "AgentResponse"
]
