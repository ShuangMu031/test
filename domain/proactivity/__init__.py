"""
主动交互模块

V5 核心组件：主动消息生成。

V9 修复：修正导出名称
"""

from .service import ProactiveInteractionService
from .models import ProactiveMessage, TriggerType, TriggerCondition, ProactiveCandidate, ProactiveContext, ProactiveDecision

__all__ = [
    "ProactiveInteractionService",
    "ProactiveCandidate",
    "ProactiveMessage",
    "TriggerType",
    "TriggerCondition",
    "ProactiveContext",
    "ProactiveDecision",
]
