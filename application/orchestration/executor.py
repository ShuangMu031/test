"""
动作执行器

V6 核心组件：执行编译后的计划。

V6 改进：
- 增加 _execute_world_updates()
- 增加 _execute_npc_hint()
- 工具不存在时写入失败结果
- ExecutionResult 增加 world_update_result 和 npc_result
- ExecutionResult 从 schemas/execution.py 导入（唯一正式定义）
"""

from typing import Dict, Any, Optional, List
import logging
import asyncio

from application.contracts.action_types import ActionType
from application.contracts.execution import ExecutionResult
from infrastructure.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    动作执行器
    
    执行编译后的 ExecutablePlan。
    
    职责：
    1. 执行工具调用
    2. 读取世界内容
    3. 更新世界状态
    4. 执行 NPC 提示
    5. 返回执行结果
    """
    
    def __init__(
        self,
        tool_registry: Optional[Dict[str, BaseTool]] = None,
        world_service=None,
        world_content_service=None,
        npc_manager=None
    ):
        self.tool_registry = tool_registry or {}
        self.world_service = world_service
        self.world_content_service = world_content_service
        self.npc_manager = npc_manager
    
    async def execute(
        self,
        executable_plan: Any,
        turn_context: Any = None
    ) -> ExecutionResult:
        """
        执行计划
        
        Args:
            executable_plan: 可执行计划
            turn_context: 轮次上下文
            
        Returns:
            ExecutionResult
        """
        action_type = executable_plan.action_type
        
        try:
            result = ExecutionResult(success=True, action_type=action_type)
            
            if action_type == ActionType.TOOL_USE:
                tool_result = await self._execute_tools(executable_plan)
                result.tool_results = tool_result.tool_results
                result.success = tool_result.success
                result.warnings.extend(tool_result.warnings)
                result.trace.extend(tool_result.trace)
            
            if action_type == ActionType.WORLD_CONTENT_READ:
                content_result = await self._execute_world_content_read(executable_plan)
                result.world_content_result = content_result.world_content_result
                result.success = content_result.success
                result.warnings.extend(content_result.warnings)
            
            if executable_plan.world_updates:
                result.world_update_result = await self._execute_world_updates(executable_plan)
            
            if executable_plan.npc_hint:
                result.npc_result = await self._execute_npc_hint(executable_plan)
            
            return result
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return ExecutionResult(
                success=False,
                action_type=action_type,
                error=str(e),
                trace=[f"执行异常: {e}"]
            )
    
    async def _execute_tools(self, plan: Any) -> ExecutionResult:
        """执行工具调用"""
        tool_results = []
        warnings = []
        trace = []
        
        for tool_call in plan.tool_calls:
            tool_name = tool_call.get("tool_name")
            tool_args = tool_call.get("args", {})
            
            trace.append(f"调用工具: {tool_name}")
            
            if tool_name not in self.tool_registry:
                logger.warning(f"工具不存在: {tool_name}")
                warnings.append(f"工具不存在: {tool_name}")
                tool_results.append(ToolResult(
                    success=False,
                    error=f"工具不存在: {tool_name}",
                    tool_name=tool_name,
                    source="executor"
                ))
                continue
            
            tool = self.tool_registry[tool_name]
            
            try:
                result = await tool.execute(**tool_args)
                tool_results.append(result)
                trace.append(f"工具 {tool_name} 执行成功")
                logger.info(f"工具 {tool_name} 执行成功")
            except Exception as e:
                logger.error(f"工具 {tool_name} 执行失败: {e}")
                warnings.append(f"工具 {tool_name} 执行失败: {e}")
                trace.append(f"工具 {tool_name} 执行失败: {e}")
                tool_results.append(ToolResult(
                    success=False,
                    error=str(e),
                    tool_name=tool_name,
                    source="executor"
                ))
        
        return ExecutionResult(
            success=all(r.success for r in tool_results) if tool_results else True,
            action_type=ActionType.TOOL_USE,
            tool_results=tool_results,
            warnings=warnings,
            trace=trace
        )
    
    async def _execute_world_content_read(self, plan: Any) -> ExecutionResult:
        """执行世界内容读取"""
        if not self.world_content_service:
            return ExecutionResult(
                success=False,
                action_type=ActionType.WORLD_CONTENT_READ,
                error="世界内容服务未启用",
                warnings=["世界内容服务未启用"]
            )
        
        query = plan.world_content_query or {}
        content_types = query.get("content_types", [])
        search_query = query.get("query", "")
        
        try:
            if content_types:
                if isinstance(content_types, (str, type(None))):
                    content_types = [content_types] if content_types else []
                content = self.world_content_service.get_content_by_types(content_types)
            elif search_query:
                content = self.world_content_service.search_relevant_content(search_query)
            else:
                content = self.world_content_service.get_latest_content(limit=5)
            
            return ExecutionResult(
                success=True,
                action_type=ActionType.WORLD_CONTENT_READ,
                world_content_result={
                    "items": [c.to_dict() if hasattr(c, "to_dict") else str(c) for c in content],
                    "count": len(content)
                },
                trace=[f"读取世界内容: {len(content)} 条"]
            )
        except Exception as e:
            logger.error(f"世界内容读取失败: {e}")
            return ExecutionResult(
                success=False,
                action_type=ActionType.WORLD_CONTENT_READ,
                error=str(e),
                warnings=[f"世界内容读取失败: {e}"]
            )
    
    async def _execute_world_updates(self, plan: Any) -> Dict[str, Any]:
        """
        执行世界更新
        
        V9 修复：使用新接口 enqueue_world_action
        """
        if not self.world_service:
            logger.warning("世界服务未启用，跳过世界更新")
            return {"success": False, "reason": "world_service_not_available"}
        
        world_updates = plan.world_updates
        if not world_updates:
            return {"success": True, "reason": "no_updates"}
        
        try:
            time_advance = world_updates.get("time_advance_minutes", 0)
            suggested_location = world_updates.get("suggested_location")
            npc_context_hint = world_updates.get("npc_context_hint", "")
            
            if time_advance > 0:
                await self.world_service.enqueue_world_action({
                    "type": "tick",
                    "minutes": time_advance
                })
                logger.info(f"世界时间推进: {time_advance} 分钟")
            
            if suggested_location:
                await self.world_service.enqueue_world_action({
                    "type": "move",
                    "location": suggested_location
                })
                logger.info(f"世界位置更新: {suggested_location}")
            
            return {
                "success": True,
                "time_advanced": time_advance,
                "location_updated": suggested_location is not None,
                "npc_hint": npc_context_hint
            }
        except Exception as e:
            logger.error(f"世界更新失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_npc_hint(self, plan: Any) -> Dict[str, Any]:
        """执行 NPC 提示"""
        if not self.npc_manager:
            logger.warning("NPC 管理器未启用，跳过 NPC 提示")
            return {"success": False, "reason": "npc_manager_not_available"}
        
        npc_hint = plan.npc_hint
        if not npc_hint:
            return {"success": True, "reason": "no_hint"}
        
        try:
            npc_id = npc_hint.get("npc_id")
            intervention_type = npc_hint.get("intervention_type", "none")
            dialogue_hint = npc_hint.get("dialogue_hint", "")
            
            if intervention_type == "none":
                return {"success": True, "reason": "no_intervention"}
            
            npc = self.npc_manager.get_npc(npc_id) if npc_id else None
            if not npc:
                logger.warning(f"NPC 不存在: {npc_id}")
                return {"success": False, "reason": "npc_not_found"}
            
            return {
                "success": True,
                "npc_id": npc_id,
                "intervention_type": intervention_type,
                "dialogue_hint": dialogue_hint
            }
        except Exception as e:
            logger.error(f"NPC 提示执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def register_tool(self, name: str, tool: BaseTool) -> None:
        """注册工具"""
        self.tool_registry[name] = tool
        logger.info(f"工具注册: {name}")
    
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表"""
        return list(self.tool_registry.keys())
