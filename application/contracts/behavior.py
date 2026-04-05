"""
行为相关 Schema

V6 统一字段：
- primary_action: 使用 ActionType 枚举类型
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .action_types import ActionType


@dataclass
class ActionPlanV2:
    """
    行为计划 V2
    
    来自 BehaviorBrain 的输出，包含完整的执行计划。
    
    统一字段说明：
    - mode: 行为模式 (chat/tool/world_content/npc)
    - primary_action: 主动作类型，使用 ActionType 枚举
    - execution_mode: 执行模式 (respond_only/tool_first/mixed)
    - priority: 优先级 (1-10)
    - confidence: 置信度 (0.0-1.0)
    - tool_plan: 工具计划列表
    - npc_plan: NPC 交互计划
    - response_style: 回复风格
    - response_length: 回复长度
    - ask_followup: 是否追问
    - followup_goal: 追问目标
    - world_commit_needed: 是否需要世界提交
    - memory_commit_needed: 是否需要记忆提交
    - requires_tool_result: 是否需要工具结果
    - safety_flags: 安全标志列表
    - reasoning: 推理说明
    """
    mode: str = "chat"
    primary_action: ActionType = ActionType.RESPOND
    execution_mode: str = "respond_only"
    priority: int = 5
    confidence: float = 0.5
    
    tool_plan: List[Dict[str, Any]] = field(default_factory=list)
    npc_plan: Dict[str, Any] = field(default_factory=dict)
    
    response_style: str = "friendly"
    response_length: str = "medium"
    ask_followup: bool = False
    followup_goal: str = ""
    
    world_commit_needed: bool = False
    memory_commit_needed: bool = False
    requires_tool_result: bool = False
    safety_flags: List[str] = field(default_factory=list)
    
    world_expression_mode: str = "suppressed"
    
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "primary_action": self.primary_action.value,
            "execution_mode": self.execution_mode,
            "priority": self.priority,
            "confidence": self.confidence,
            "tool_plan": self.tool_plan,
            "npc_plan": self.npc_plan,
            "response_style": self.response_style,
            "response_length": self.response_length,
            "ask_followup": self.ask_followup,
            "followup_goal": self.followup_goal,
            "world_commit_needed": self.world_commit_needed,
            "memory_commit_needed": self.memory_commit_needed,
            "requires_tool_result": self.requires_tool_result,
            "safety_flags": self.safety_flags,
            "world_expression_mode": self.world_expression_mode,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionPlanV2":
        primary_action_value = data.get("primary_action", "respond")
        if isinstance(primary_action_value, str):
            primary_action = ActionType(primary_action_value)
        else:
            primary_action = primary_action_value
        
        return cls(
            mode=data.get("mode", "chat"),
            primary_action=primary_action,
            execution_mode=data.get("execution_mode", "respond_only"),
            priority=data.get("priority", 5),
            confidence=data.get("confidence", 0.5),
            tool_plan=data.get("tool_plan", []),
            npc_plan=data.get("npc_plan", {}),
            response_style=data.get("response_style", "friendly"),
            response_length=data.get("response_length", "medium"),
            ask_followup=data.get("ask_followup", False),
            followup_goal=data.get("followup_goal", ""),
            world_commit_needed=data.get("world_commit_needed", False),
            memory_commit_needed=data.get("memory_commit_needed", False),
            requires_tool_result=data.get("requires_tool_result", False),
            safety_flags=data.get("safety_flags", []),
            world_expression_mode=data.get("world_expression_mode", "suppressed"),
            reasoning=data.get("reasoning", "")
        )
