"""
V5 统一 Schema 层

所有 V5 主线组件的数据结构定义。
不再让 dataclass 散在各 brain 和 orchestration 里。

职责：
1. 定义所有核心数据结构
2. 提供统一的类型导入点
3. 保证字段一致性

第二次整改：
- 成为"唯一结构源"
- 所有跨模块数据结构必须在此定义
- 禁止在其他目录临时定义"差不多的 dataclass"
"""

from .emotion import EmotionInsight
from .memory import MemoryDecision
from .world import WorldUpdateProposal, WorldContentProposal, WorldBrainOutput
from .behavior import ActionPlanV2
from .execution import ExecutablePlan, ExecutionResult, InvalidLevel
from .policy import FallbackDecision
from .npc import NPCInteractionHint
from .supervisor import SupervisorDecision
from .action_types import ActionType
from .reality import (
    RealitySignal,
    RealitySignalType,
    WeatherSignal,
    NewsSignal,
    HolidaySignal,
    TimeSignal,
    ProactiveMessageCandidate
)

__all__ = [
    "EmotionInsight",
    "MemoryDecision",
    "WorldUpdateProposal",
    "WorldContentProposal",
    "WorldBrainOutput",
    "ActionPlanV2",
    "ExecutablePlan",
    "ExecutionResult",
    "InvalidLevel",
    "FallbackDecision",
    "NPCInteractionHint",
    "SupervisorDecision",
    "ActionType",
    "RealitySignal",
    "RealitySignalType",
    "WeatherSignal",
    "NewsSignal",
    "HolidaySignal",
    "TimeSignal",
    "ProactiveMessageCandidate",
]
