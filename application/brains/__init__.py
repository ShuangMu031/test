"""
认知模块 V5

六脑系统：
- EmotionBrain: 情绪脑
- MemoryBrain: 记忆脑
- WorldBrain: 世界脑
- NPCBrain: NPC脑
- BehaviorBrain: 行为脑
- SupervisorBrain: 总控脑
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)

DEFAULT_EXECUTION_ORDER = [
    "emotion",
    "memory",
    "world",
    "npc",
    "behavior",
    "supervisor"
]


class BrainRegistry:
    """
    脑子注册表
    
    管理所有脑子的注册和执行。
    """
    
    def __init__(self):
        self._brains: Dict[str, Any] = {}
        self._priorities: Dict[str, int] = {}
    
    def register(self, brain: Any, priority: int = 50) -> None:
        """注册脑子"""
        name = brain.name
        self._brains[name] = brain
        self._priorities[name] = priority
        logger.debug(f"脑子注册: {name}, 优先级: {priority}")
    
    def get(self, name: str) -> Optional[Any]:
        """获取脑子"""
        return self._brains.get(name)
    
    def list_brains(self) -> List[str]:
        """列出所有脑子"""
        return sorted(self._brains.keys(), key=lambda x: self._priorities.get(x, 50))

    def get_execution_order(self) -> List[str]:
        """兼容旧示例接口，返回实际执行顺序。"""
        return self.list_brains()
    
    async def run_all(self, context: Any) -> Dict[str, Any]:
        """运行所有脑子"""
        results = {}
        
        sorted_brains = sorted(
            self._brains.items(),
            key=lambda x: self._priorities.get(x[0], 50)
        )
        
        for name, brain in sorted_brains:
            try:
                result = await brain.process(context)
                results[name] = result
                logger.debug(f"脑子 {name} 执行完成")
            except Exception as e:
                logger.error(f"脑子 {name} 执行失败: {e}")
        
        return results


from .base import BaseBrain
from .emotion_brain import EmotionBrain
from .memory_brain import MemoryBrain
from .world_brain import WorldBrain
from .npc_brain import NPCBrain
from .behavior_brain import BehaviorBrain
from .supervisor_brain import SupervisorBrain

from application.contracts.emotion import EmotionInsight
from application.contracts.memory import MemoryDecision
from application.contracts.world import WorldUpdateProposal
from application.contracts.npc import NPCInteractionHint
from application.contracts.behavior import ActionPlanV2
from application.contracts.supervisor import SupervisorDecision

__all__ = [
    "BrainRegistry",
    "BaseBrain",
    "EmotionBrain",
    "MemoryBrain",
    "WorldBrain",
    "NPCBrain",
    "BehaviorBrain",
    "SupervisorBrain",
    "EmotionInsight",
    "MemoryDecision",
    "WorldUpdateProposal",
    "NPCInteractionHint",
    "ActionPlanV2",
    "SupervisorDecision",
    "DEFAULT_EXECUTION_ORDER"
]
