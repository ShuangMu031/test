"""
执行相关 Schema

V6 统一字段体系：
- ExecutablePlan: 可执行计划（唯一正式定义）
- ExecutionResult: 执行结果
- InvalidLevel: 无效级别枚举

注意：全项目只能保留这一份 ExecutablePlan 定义。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .action_types import ActionType


class InvalidLevel(str, Enum):
    """无效级别"""
    NONE = "none"
    MINOR = "minor"
    PARTIAL = "partial"
    CRITICAL = "critical"


@dataclass
class ExecutablePlan:
    """
    可执行计划
    
    编译后的执行结构，供 ActionExecutor 使用。
    
    统一字段说明：
    - action_type: 动作类型（ActionType 枚举）
    - priority: 优先级 (1-10)
    - confidence: 置信度 (0.0-1.0)
    - tool_calls: 工具调用列表
    - world_updates: 世界更新
    - memory_updates: 记忆更新
    - response_spec: 回复规格
    - npc_hint: NPC 提示
    - world_content_query: 世界内容查询
    - is_valid: 是否有效
    - invalid_level: 无效级别
    - validation_errors: 校验错误列表
    - supervisor_applied: 是否应用了 supervisor 裁决
    - suppressed_tools: 被抑制的工具列表
    - suppressed_npc: 是否抑制了 NPC 交互
    """
    action_type: ActionType
    priority: int = 5
    confidence: float = 0.5
    
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    world_updates: Dict[str, Any] = field(default_factory=dict)
    memory_updates: Dict[str, Any] = field(default_factory=dict)
    
    response_spec: Dict[str, Any] = field(default_factory=dict)
    
    npc_hint: Optional[Dict[str, Any]] = None
    world_content_query: Optional[Dict[str, Any]] = None
    
    is_valid: bool = True
    invalid_level: InvalidLevel = InvalidLevel.NONE
    validation_errors: List[str] = field(default_factory=list)
    
    supervisor_applied: bool = False
    suppressed_tools: List[str] = field(default_factory=list)
    suppressed_npc: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "priority": self.priority,
            "confidence": self.confidence,
            "tool_calls": self.tool_calls,
            "world_updates": self.world_updates,
            "memory_updates": self.memory_updates,
            "response_spec": self.response_spec,
            "npc_hint": self.npc_hint,
            "world_content_query": self.world_content_query,
            "is_valid": self.is_valid,
            "invalid_level": self.invalid_level.value,
            "validation_errors": self.validation_errors,
            "supervisor_applied": self.supervisor_applied,
            "suppressed_tools": self.suppressed_tools,
            "suppressed_npc": self.suppressed_npc
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutablePlan":
        action_type_value = data.get("action_type", "respond")
        if isinstance(action_type_value, str):
            action_type = ActionType(action_type_value)
        else:
            action_type = action_type_value
        
        invalid_level_value = data.get("invalid_level", "none")
        if isinstance(invalid_level_value, str):
            invalid_level = InvalidLevel(invalid_level_value)
        else:
            invalid_level = invalid_level_value
        
        return cls(
            action_type=action_type,
            priority=data.get("priority", 5),
            confidence=data.get("confidence", 0.5),
            tool_calls=data.get("tool_calls", []),
            world_updates=data.get("world_updates", {}),
            memory_updates=data.get("memory_updates", {}),
            response_spec=data.get("response_spec", {}),
            npc_hint=data.get("npc_hint"),
            world_content_query=data.get("world_content_query"),
            is_valid=data.get("is_valid", True),
            invalid_level=invalid_level,
            validation_errors=data.get("validation_errors", []),
            supervisor_applied=data.get("supervisor_applied", False),
            suppressed_tools=data.get("suppressed_tools", []),
            suppressed_npc=data.get("suppressed_npc", False)
        )


@dataclass
class ExecutionResult:
    """
    执行结果
    
    统一字段说明：
    - success: 是否成功
    - action_type: 执行的动作类型
    - tool_results: 工具调用结果列表
    - world_content_result: 世界内容查询结果
    - world_update_result: 世界更新结果
    - npc_result: NPC 交互结果
    - error: 错误信息
    - degraded: 是否发生了降级
    - degradation_reason: 降级原因
    - warnings: 警告列表
    - trace: 执行追踪列表
    """
    success: bool
    action_type: ActionType
    tool_results: List[Any] = field(default_factory=list)
    world_content_result: Optional[Dict[str, Any]] = None
    world_update_result: Optional[Dict[str, Any]] = None
    npc_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    degraded: bool = False
    degradation_reason: str = ""
    warnings: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action_type": self.action_type.value,
            "tool_results": [r.to_dict() if hasattr(r, "to_dict") else r for r in self.tool_results],
            "world_content_result": self.world_content_result,
            "world_update_result": self.world_update_result,
            "npc_result": self.npc_result,
            "error": self.error,
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason,
            "warnings": self.warnings,
            "trace": self.trace
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        action_type_value = data.get("action_type", "respond")
        if isinstance(action_type_value, str):
            action_type = ActionType(action_type_value)
        else:
            action_type = action_type_value
        
        return cls(
            success=data.get("success", False),
            action_type=action_type,
            tool_results=data.get("tool_results", []),
            world_content_result=data.get("world_content_result"),
            world_update_result=data.get("world_update_result"),
            npc_result=data.get("npc_result"),
            error=data.get("error"),
            degraded=data.get("degraded", False),
            degradation_reason=data.get("degradation_reason", ""),
            warnings=data.get("warnings", []),
            trace=data.get("trace", [])
        )
    
    def has_tool_failures(self) -> bool:
        """是否有工具执行失败"""
        return any(not getattr(r, "success", True) for r in self.tool_results)
    
    def get_failed_tools(self) -> List[str]:
        """获取失败的工具名称"""
        return [getattr(r, "tool_name", "unknown") for r in self.tool_results if not getattr(r, "success", True)]
