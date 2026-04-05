"""
监督者相关 Schema

V6 统一字段体系：
- conflict_detected: 是否检测到冲突
- conflict_resolution: 冲突解决策略
- override_action_type: 覆盖动作类型（ActionType）
- suppress_tool_execution: 是否抑制工具执行
- suppress_npc: 是否抑制 NPC 交互
- final_model_tier: 最终模型档位
- should_run_final_review: 是否需要最终审查
- reasoning: 推理说明
- confidence: 置信度

已删除字段：
- override_action: 被 override_action_type 替代
- suppressed_actions: 被 suppress_tool_execution/suppress_npc 替代
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass

from .action_types import ActionType


@dataclass
class SupervisorDecision:
    """
    监督者决策
    
    来自 SupervisorBrain 的输出，包含冲突解决和抑制决策。
    
    统一字段说明：
    - conflict_detected: 是否检测到冲突
    - conflict_resolution: 冲突解决策略 (none/prioritize_comfort/balance_comfort_and_task/follow_behavior_plan)
    - override_action_type: 覆盖动作类型（ActionType 枚举）
    - suppress_tool_execution: 是否抑制工具执行
    - suppress_npc: 是否抑制 NPC 交互
    - final_model_tier: 最终模型档位
    - should_run_final_review: 是否需要最终审查
    - override_world_expression_mode: 覆盖世界表达级别 (V7 新增)
    - reasoning: 推理说明
    - confidence: 置信度 (0.0-1.0)
    """
    conflict_detected: bool = False
    conflict_resolution: str = ""
    override_action_type: Optional[ActionType] = None
    suppress_tool_execution: bool = False
    suppress_npc: bool = False
    final_model_tier: str = "standard"
    should_run_final_review: bool = False
    override_world_expression_mode: Optional[str] = None
    reasoning: str = ""
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        override_type_value = None
        if self.override_action_type is not None:
            override_type_value = self.override_action_type.value
        
        return {
            "conflict_detected": self.conflict_detected,
            "conflict_resolution": self.conflict_resolution,
            "override_action_type": override_type_value,
            "suppress_tool_execution": self.suppress_tool_execution,
            "suppress_npc": self.suppress_npc,
            "final_model_tier": self.final_model_tier,
            "should_run_final_review": self.should_run_final_review,
            "override_world_expression_mode": self.override_world_expression_mode,
            "reasoning": self.reasoning,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SupervisorDecision":
        override_type = None
        override_type_value = data.get("override_action_type")
        if override_type_value:
            if isinstance(override_type_value, str):
                override_type = ActionType(override_type_value)
            else:
                override_type = override_type_value
        
        return cls(
            conflict_detected=data.get("conflict_detected", False),
            conflict_resolution=data.get("conflict_resolution", ""),
            override_action_type=override_type,
            suppress_tool_execution=data.get("suppress_tool_execution", False),
            suppress_npc=data.get("suppress_npc", False),
            final_model_tier=data.get("final_model_tier", "standard"),
            should_run_final_review=data.get("should_run_final_review", False),
            override_world_expression_mode=data.get("override_world_expression_mode"),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 0.5)
        )
