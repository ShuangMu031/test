"""
策略模块

V5 核心组件：兜底策略。
"""

from .fallback_policy import FallbackPolicy, FallbackDecision

__all__ = [
    "FallbackPolicy",
    "FallbackDecision"
]
