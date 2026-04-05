"""
计划编译器

V6 核心组件：只负责编译执行计划，不做规划判断。

V6 改进：
- 输入改为 resolved_action_plan（融合 supervisor 裁决后）
- 增加预处理步骤：override action, suppress tool, suppress npc
- response_spec 字段统一为 response_style, response_length
- 处理 supervisor_decision 的抑制指令
- ExecutablePlan 从 schemas/execution.py 导入（唯一正式定义）
"""

from typing import Dict, Any, List, Optional
import logging

from application.contracts.action_types import ActionType
from application.contracts.execution import ExecutablePlan, InvalidLevel

logger = logging.getLogger(__name__)


class PlanSanitizer:
    """
    计划清理器
    
    处理无效计划的分级：
    1. MINOR: 轻微无效，normalize 后继续
    2. PARTIAL: 局部无效，suppress 该部分
    3. CRITICAL: 整体无效，fallback 为 RESPOND
    """
    
    def sanitize(self, plan: ExecutablePlan) -> ExecutablePlan:
        """清理计划"""
        if plan.invalid_level == InvalidLevel.MINOR:
            return self._handle_minor(plan)
        elif plan.invalid_level == InvalidLevel.PARTIAL:
            return self._handle_partial(plan)
        elif plan.invalid_level == InvalidLevel.CRITICAL:
            return self._handle_critical(plan)
        
        return plan
    
    def _handle_minor(self, plan: ExecutablePlan) -> ExecutablePlan:
        """处理轻微无效"""
        plan.response_spec = self._normalize_response_spec(plan.response_spec)
        plan.is_valid = True
        plan.invalid_level = InvalidLevel.NONE
        return plan
    
    def _handle_partial(self, plan: ExecutablePlan) -> ExecutablePlan:
        """处理局部无效"""
        plan.tool_calls = [tc for tc in plan.tool_calls if tc.get("tool_name")]
        plan.is_valid = len(plan.tool_calls) > 0 or plan.action_type != ActionType.TOOL_USE
        
        if plan.action_type == ActionType.TOOL_USE and not plan.tool_calls:
            plan.action_type = ActionType.RESPOND
        
        plan.invalid_level = InvalidLevel.NONE
        return plan
    
    def _handle_critical(self, plan: ExecutablePlan) -> ExecutablePlan:
        """处理整体无效"""
        plan.action_type = ActionType.RESPOND
        plan.tool_calls = []
        plan.world_updates = {}
        plan.memory_updates = {}
        plan.is_valid = True
        plan.invalid_level = InvalidLevel.NONE
        plan.confidence = 0.3
        return plan
    
    def _normalize_response_spec(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """标准化回复规格"""
        valid_lengths = {"short", "medium", "long"}
        valid_styles = {"friendly", "empathetic", "supportive", "professional"}
        
        if spec.get("response_length") not in valid_lengths:
            spec["response_length"] = "medium"
        
        if spec.get("response_style") not in valid_styles:
            spec["response_style"] = "friendly"
        
        return spec


class PlanCompiler:
    """
    计划编译器
    
    只做编译，不做规划判断。
    
    输入：ActionPlanV2（来自 BehaviorBrain）+ SupervisorDecision
    输出：ExecutablePlan（给 ActionExecutor）
    
    核心原则：
    - 不做意图识别
    - 不做关键词匹配
    - 不做工具选择判断
    - 不做业务默认值填充
    - 只做格式转换和校验
    - 处理 supervisor 的覆盖和抑制指令
    """
    
    def __init__(self):
        self.compile_history: List[ExecutablePlan] = []
        self.sanitizer = PlanSanitizer()
    
    def compile(
        self,
        action_plan_v2: Any,
        context: Dict[str, Any],
        supervisor_decision: Optional[Any] = None
    ) -> ExecutablePlan:
        """
        编译行为计划
        
        Args:
            action_plan_v2: 来自 BehaviorBrain 的行为计划
            context: 上下文信息
            supervisor_decision: 来自 SupervisorBrain 的裁决
            
        Returns:
            ExecutablePlan
        """
        if action_plan_v2 is None:
            return self._create_fallback_plan("action_plan_v2 is None", InvalidLevel.CRITICAL)
        
        action_type = self._determine_action_type(action_plan_v2)
        
        executable = ExecutablePlan(
            action_type=action_type,
            priority=getattr(action_plan_v2, "priority", 5),
            confidence=getattr(action_plan_v2, "confidence", 0.5)
        )
        
        if supervisor_decision:
            executable = self._apply_supervisor_decision(executable, supervisor_decision)
        
        if action_type == ActionType.TOOL_USE and not executable.suppressed_tools:
            executable.tool_calls = self._compile_tool_calls(action_plan_v2)
            self._validate_tool_calls(executable)
        
        if action_type == ActionType.WORLD_CONTENT_READ:
            executable.world_content_query = self._compile_world_content_query(action_plan_v2, context)
        
        executable.response_spec = self._compile_response_spec(action_plan_v2)
        
        if hasattr(action_plan_v2, "world_commit_needed") and action_plan_v2.world_commit_needed:
            executable.world_updates = self._compile_world_updates(action_plan_v2, context)
        
        if hasattr(action_plan_v2, "memory_commit_needed") and action_plan_v2.memory_commit_needed:
            executable.memory_updates = self._compile_memory_updates(action_plan_v2, context)
        
        npc_hint = context.get("npc_interaction_hint")
        if npc_hint and getattr(npc_hint, "should_involve_npc", False) and not executable.suppressed_npc:
            executable.npc_hint = {
                "npc_id": getattr(npc_hint, "npc_id", None),
                "intervention_type": getattr(npc_hint, "intervention_type", "none"),
                "dialogue_hint": getattr(npc_hint, "dialogue_hint", "")
            }
        
        executable.invalid_level = self._determine_invalid_level(executable)
        executable.is_valid = executable.invalid_level in [InvalidLevel.NONE, InvalidLevel.MINOR]
        
        executable = self.sanitizer.sanitize(executable)
        
        self.compile_history.append(executable)
        if len(self.compile_history) > 100:
            self.compile_history = self.compile_history[-100:]
        
        return executable
    
    def _apply_supervisor_decision(
        self,
        executable: ExecutablePlan,
        supervisor_decision: Any
    ) -> ExecutablePlan:
        """应用 supervisor 裁决"""
        executable.supervisor_applied = True
        
        override_action_type = getattr(supervisor_decision, "override_action_type", None)
        if override_action_type is not None:
            executable.action_type = override_action_type
            logger.info(f"Supervisor override action: {override_action_type.value}")
        
        suppress_tool = getattr(supervisor_decision, "suppress_tool_execution", False)
        if suppress_tool:
            executable.tool_calls = []
            executable.suppressed_tools = ["all"]
            if executable.action_type == ActionType.TOOL_USE:
                executable.action_type = ActionType.RESPOND
            logger.info("Supervisor suppressed tool execution")
        
        suppress_npc = getattr(supervisor_decision, "suppress_npc", False)
        if suppress_npc:
            executable.npc_hint = None
            executable.suppressed_npc = True
            logger.info("Supervisor suppressed NPC interaction")
        
        return executable
    
    def _create_fallback_plan(self, reason: str, level: InvalidLevel = InvalidLevel.CRITICAL) -> ExecutablePlan:
        """创建降级计划"""
        plan = ExecutablePlan(
            action_type=ActionType.RESPOND,
            priority=5,
            confidence=0.3,
            is_valid=False,
            invalid_level=level
        )
        plan.validation_errors.append(reason)
        
        return self.sanitizer.sanitize(plan)
    
    def _determine_invalid_level(self, plan: ExecutablePlan) -> InvalidLevel:
        """确定无效级别"""
        if plan.validation_errors:
            for error in plan.validation_errors:
                if "action_type" in error.lower() or "critical" in error.lower():
                    return InvalidLevel.CRITICAL
        
        if not plan.tool_calls and plan.action_type == ActionType.TOOL_USE:
            return InvalidLevel.PARTIAL
        
        minor_errors = [
            "response_length" in e.lower() or
            "response_style" in e.lower() or
            "followup_goal" in e.lower()
            for e in plan.validation_errors
        ]
        if any(minor_errors):
            return InvalidLevel.MINOR
        
        return InvalidLevel.NONE
    
    def _determine_action_type(self, action_plan_v2: Any) -> ActionType:
        """确定动作类型"""
        primary_action = getattr(action_plan_v2, "primary_action", ActionType.RESPOND)
        
        if isinstance(primary_action, ActionType):
            return primary_action
        
        mode = getattr(action_plan_v2, "mode", "chat")
        
        mode_to_action = {
            "tool": ActionType.TOOL_USE,
            "comfort": ActionType.COMFORT,
            "task": ActionType.RESPOND,
            "npc": ActionType.RESPOND,
            "mixed": ActionType.RESPOND
        }
        
        if mode in mode_to_action:
            return mode_to_action[mode]
        
        action_to_type = {
            "respond": ActionType.RESPOND,
            "ask": ActionType.RESPOND,
            "comfort": ActionType.COMFORT,
            "use_tool": ActionType.TOOL_USE,
            "shift_scene": ActionType.EXPLORE
        }
        
        return action_to_type.get(primary_action, ActionType.RESPOND)
    
    def _compile_tool_calls(self, action_plan_v2: Any) -> List[Dict[str, Any]]:
        """编译工具调用"""
        tool_calls = []
        
        tool_plan = getattr(action_plan_v2, "tool_plan", None)
        if tool_plan:
            for tool_spec in tool_plan:
                tool_call = {
                    "tool_name": tool_spec.get("tool_name", ""),
                    "args": tool_spec.get("args", {})
                }
                tool_calls.append(tool_call)
        
        return tool_calls
    
    def _validate_tool_calls(self, executable: ExecutablePlan) -> None:
        """校验工具调用"""
        for tool_call in executable.tool_calls:
            tool_name = tool_call.get("tool_name", "")
            args = tool_call.get("args", {})
            
            if not tool_name:
                executable.validation_errors.append("tool_name is empty")
                continue
            
            if not isinstance(args, dict):
                executable.validation_errors.append(f"tool args is not dict: {tool_name}")
    
    def _compile_world_content_query(
        self,
        action_plan_v2: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """编译世界内容查询"""
        world_brain_output = context.get("world_brain_output")
        
        if world_brain_output:
            world_content_proposal = getattr(world_brain_output, "world_content_proposal", None)
            if world_content_proposal:
                return {
                    "content_types": getattr(world_content_proposal, "content_types_needed", []),
                    "query": getattr(world_content_proposal, "retrieval_query", ""),
                    "category": getattr(world_content_proposal, "content_category", "")
                }
        
        return {
            "content_types": [],
            "query": "",
            "category": ""
        }
    
    def _compile_response_spec(self, action_plan_v2: Any) -> Dict[str, Any]:
        """编译回复规格（统一字段名）"""
        response_style = getattr(action_plan_v2, "response_style", None)
        if response_style is None:
            response_style = getattr(action_plan_v2, "style", "friendly")
        
        response_length = getattr(action_plan_v2, "response_length", None)
        if response_length is None:
            response_length = getattr(action_plan_v2, "length", "medium")
        
        return {
            "response_style": response_style,
            "response_length": response_length,
            "ask_followup": getattr(action_plan_v2, "ask_followup", False),
            "followup_goal": getattr(action_plan_v2, "followup_goal", "")
        }
    
    def _compile_world_updates(
        self,
        action_plan_v2: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """编译世界更新"""
        world_brain_output = context.get("world_brain_output")
        
        if world_brain_output:
            world_update_proposal = getattr(world_brain_output, "world_update_proposal", None)
            if world_update_proposal:
                return {
                    "time_advance_minutes": getattr(world_update_proposal, "time_advance_minutes", 0),
                    "suggested_location": getattr(world_update_proposal, "suggested_location", None),
                    "npc_context_hint": getattr(world_update_proposal, "npc_context_hint", "")
                }
        
        return {}
    
    def _compile_memory_updates(
        self,
        action_plan_v2: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        编译记忆更新
        
        V9 改版：记忆提交统一在 turn_orchestrator._post_commit() 中处理
        此方法保留为空，不再编译记忆更新
        """
        return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取编译统计"""
        action_counts = {}
        valid_count = 0
        invalid_counts = {level.value: 0 for level in InvalidLevel}
        supervisor_applied_count = 0
        
        for plan in self.compile_history:
            action_type = plan.action_type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            if plan.is_valid:
                valid_count += 1
            
            invalid_counts[plan.invalid_level.value] += 1
            
            if plan.supervisor_applied:
                supervisor_applied_count += 1
        
        return {
            "total_compiles": len(self.compile_history),
            "valid_count": valid_count,
            "invalid_counts": invalid_counts,
            "action_distribution": action_counts,
            "supervisor_applied_count": supervisor_applied_count
        }
