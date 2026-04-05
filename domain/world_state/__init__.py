"""
世界状态模块

V9 改版：domain/world_state/

职责：
- 世界状态管理
- 世界运行时接口
- 本地世界适配器
- 世界时钟
- 世界状态持久化
"""

from domain.world_state.port import WorldRuntimePort, WorldSnapshot, WorldEvent
from domain.world_state.local_adapter import LocalWorldAdapter
from domain.world_state.clock import WorldClock
from domain.world_state.store import WorldStore, WorldStateData

__all__ = [
    "WorldRuntimePort",
    "WorldSnapshot",
    "WorldEvent",
    "LocalWorldAdapter",
    "WorldClock",
    "WorldStore",
    "WorldStateData",
]
