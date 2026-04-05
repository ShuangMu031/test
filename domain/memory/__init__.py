"""
记忆模块

V9 三层记忆体系

目录结构：
- core/：原生层记忆（身份、经历、偏好、关系底稿）
- episodic/：事件层记忆（重大事件、深刻互动）
- working/：上下文层记忆（最近对话、临时上下文）
- consolidation/：固化、遗忘、衰减
"""

from domain.memory.core import CoreMemoryEntry, CoreMemoryService
from domain.memory.episodic import EpisodicEventType, EpisodicMemoryEntry, EpisodicMemoryService
from domain.memory.working import WorkingMemoryType, WorkingMemoryEntry, WorkingMemoryService
from domain.memory.consolidation import ConsolidationRule, ConsolidationService

__all__ = [
    "CoreMemoryEntry",
    "CoreMemoryService",
    "EpisodicEventType",
    "EpisodicMemoryEntry",
    "EpisodicMemoryService",
    "WorkingMemoryType",
    "WorkingMemoryEntry",
    "WorkingMemoryService",
    "ConsolidationRule",
    "ConsolidationService",
]
