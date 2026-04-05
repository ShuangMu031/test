"""
回复生成器

V9 核心组件：最终回复门控器 + 生成器

V9 改进：
- 升级成最终回复门控器 + 生成器
- 只做三件事：
  1. 吃已经整理好的 prompt context
  2. 执行最终门控
  3. 输出回复 + 回复门控结果
- 强制注入执行结果
- 工具失败时优先走模板兜底
- 执行失败时不全靠 LLM 自由发挥
- 支持三层记忆上下文
"""

from typing import Any, Dict, Optional, Callable, Tuple
import logging

from application.orchestration.turn_context import TurnContext
from application.prompting.builder import PromptBuilder
from application.messaging.outbound_queue import OutboundMessage, MessageType
from datetime import datetime

logger = logging.getLogger(__name__)


class ReplyGateResult:
    """
    V10: 回复门控结果
    
    记录最终回复生成时的门控决策
    """
    def __init__(self):
        self.world_content_allowed: bool = False
        self.world_content_reason: str = ""
        self.world_expand_allowed: bool = False
        self.world_expand_reason: str = ""
        self.npc_allowed: bool = False
        self.npc_reason: str = ""
        self.tool_result_included: bool = False
        self.memory_context_included: bool = False
        self.final_style: str = "friendly"
        self.final_length: str = "medium"
        self.model_tier: str = "standard"
        self.fallback_triggered: bool = False
        self.fallback_reason: str = ""
        self.gate_decisions: list = []
    
    def add_gate_decision(self, gate: str, passed: bool, reason: str) -> None:
        """添加门控决策"""
        self.gate_decisions.append({
            "gate": gate,
            "passed": passed,
            "reason": reason
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "world_content_allowed": self.world_content_allowed,
            "world_content_reason": self.world_content_reason,
            "world_expand_allowed": self.world_expand_allowed,
            "world_expand_reason": self.world_expand_reason,
            "npc_allowed": self.npc_allowed,
            "npc_reason": self.npc_reason,
            "tool_result_included": self.tool_result_included,
            "memory_context_included": self.memory_context_included,
            "final_style": self.final_style,
            "final_length": self.final_length,
            "model_tier": self.model_tier,
            "fallback_triggered": self.fallback_triggered,
            "fallback_reason": self.fallback_reason,
            "gate_decisions": self.gate_decisions
        }


class ReplyComposer:
    """
    回复生成器
    
    V10: 最终回复门控器 + 生成器
    
    只做三件事：
    1. 吃已经整理好的 prompt context
    2. 执行最终门控
    3. 输出回复 + 回复门控结果
    
    不负责：
    - 工具执行
    - 世界更新
    - 记忆存储
    """
    
    FALLBACK_TEMPLATES = {
        "tool_failure": "抱歉，我尝试查询信息时遇到了问题。请稍后再试。",
        "tool_not_found": "抱歉，我暂时无法提供这个功能。",
        "high_support": "我理解你现在可能需要更多支持。让我来帮助你。",
        "emergency": "抱歉，我现在状态不太好，请稍后再聊。"
    }
    
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        outbound_queue: Any,
        model_router: Optional[Any] = None
    ):
        self.prompt_builder = prompt_builder
        self.outbound_queue = outbound_queue
        self.model_router = model_router
    
    async def compose(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> Tuple[str, OutboundMessage, ReplyGateResult]:
        """
        生成回复
        
        Args:
            turn_context: 轮次上下文
            services: 服务字典
            
        Returns:
            (response_text, outbound_message, gate_result)
        """
        gate_result = ReplyGateResult()
        
        self._execute_gates(turn_context, services, gate_result)
        
        memory_context = self._build_memory_context(turn_context, services)
        gate_result.memory_context_included = bool(memory_context)
        
        execution_result = turn_context.execution_result
        
        if execution_result and execution_result.has_tool_failures():
            logger.warning(f"工具执行失败: {execution_result.get_failed_tools()}")
            gate_result.fallback_triggered = True
            gate_result.fallback_reason = "tool_failure"
            response_text = await self._compose_with_failure(
                turn_context, services, gate_result, memory_context
            )
        elif execution_result and execution_result.tool_results:
            gate_result.tool_result_included = True
            response_text = await self._compose_with_results(
                turn_context, services, gate_result, memory_context
            )
        else:
            response_text = await self._compose_normal(
                turn_context, services, gate_result, memory_context
            )
        
        outbound_msg = self._create_outbound_message(turn_context, response_text, gate_result)
        
        await self.outbound_queue.enqueue(outbound_msg)
        
        return response_text, outbound_msg, gate_result
    
    def _execute_gates(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any],
        gate_result: ReplyGateResult
    ) -> None:
        """
        V10: 执行所有门控检查
        """
        self._gate_world_content(turn_context, gate_result)
        
        self._gate_npc_interaction(turn_context, gate_result)
        
        self._gate_model_selection(turn_context, gate_result)
        
        self._gate_response_style(turn_context, gate_result)
    
    def _gate_world_content(
        self,
        turn_context: TurnContext,
        gate_result: ReplyGateResult
    ) -> None:
        """
        世界内容门控
        
        V9 改版：优先消费 world_brain_output
        """
        world_brain_output = getattr(turn_context, "world_brain_output", None)
        mode = getattr(turn_context, "world_expression_mode", "suppressed")
        user_text = (getattr(turn_context, "user_input", "") or "").strip()
        
        if world_brain_output:
            should_read = getattr(world_brain_output, "should_read_world_content", False)
            if should_read:
                gate_result.world_content_allowed = True
                gate_result.world_content_reason = "世界脑建议读取世界内容"
                gate_result.add_gate_decision("world_content", True, "世界脑建议")
            else:
                gate_result.world_content_allowed = False
                gate_result.world_content_reason = "世界脑不建议读取世界内容"
                gate_result.add_gate_decision("world_content", False, "世界脑不建议")
            
            should_expand = getattr(world_brain_output, "should_expand_world_topic", False)
            if should_expand:
                gate_result.world_expand_allowed = True
                gate_result.world_expand_reason = "世界脑建议展开世界话题"
                gate_result.add_gate_decision("world_expand", True, "世界脑建议")
            else:
                gate_result.world_expand_allowed = False
                gate_result.world_expand_reason = "世界脑不建议展开世界话题"
                gate_result.add_gate_decision("world_expand", False, "世界脑不建议")
            
            return
        
        explicit_world_keywords = [
            "世界", "新闻", "事件", "公告", "传闻", "消息", "最近发生",
            "城里", "外面", "酒馆", "王城", "北境", "边境",
            "npc", "那个人", "那个商人", "那个老板", "那个骑士",
            "你那边", "那边怎么样", "发生什么", "有什么事"
        ]
        
        user_explicitly_mentions_world = any(k in user_text for k in explicit_world_keywords)
        
        if user_explicitly_mentions_world:
            gate_result.world_content_allowed = True
            gate_result.world_content_reason = "用户显式提及世界要素"
            gate_result.add_gate_decision("world_content", True, "用户显式提及")
        elif mode == "active":
            gate_result.world_content_allowed = True
            gate_result.world_content_reason = "世界表达模式为 active"
            gate_result.add_gate_decision("world_content", True, "模式允许")
        elif mode == "contextual":
            gate_result.world_content_allowed = True
            gate_result.world_content_reason = "世界表达模式为 contextual"
            gate_result.add_gate_decision("world_content", True, "模式允许")
        elif mode == "light":
            gate_result.world_content_allowed = True
            gate_result.world_content_reason = "世界表达模式为 light"
            gate_result.add_gate_decision("world_content", True, "模式允许")
        else:
            gate_result.world_content_allowed = False
            gate_result.world_content_reason = "世界表达模式为 suppressed"
            gate_result.add_gate_decision("world_content", False, "模式禁止")
        
        explicit_expand_keywords = [
            "新闻", "最近发生什么", "最近有什么事", "有什么消息",
            "公告", "传闻", "最近怎么样", "城里发生了什么",
            "那个事件", "那件事", "边境", "王城", "外面怎么了"
        ]
        
        if any(k in user_text for k in explicit_expand_keywords):
            gate_result.world_expand_allowed = True
            gate_result.world_expand_reason = "用户显式要求展开世界话题"
            gate_result.add_gate_decision("world_expand", True, "用户显式要求")
        elif mode == "active":
            gate_result.world_expand_allowed = True
            gate_result.world_expand_reason = "世界表达模式为 active"
            gate_result.add_gate_decision("world_expand", True, "模式允许")
        else:
            gate_result.world_expand_allowed = False
            gate_result.world_expand_reason = "世界表达模式不允许展开"
            gate_result.add_gate_decision("world_expand", False, "模式禁止")
    
    def _gate_npc_interaction(
        self,
        turn_context: TurnContext,
        gate_result: ReplyGateResult
    ) -> None:
        """NPC 交互门控"""
        supervisor = turn_context.supervisor_decision
        if supervisor and getattr(supervisor, "suppress_npc", False):
            gate_result.npc_allowed = False
            gate_result.npc_reason = "总控抑制 NPC 交互"
            gate_result.add_gate_decision("npc", False, "总控抑制")
            return
        
        npc_hint = getattr(turn_context, "npc_interaction_hint", None)
        if npc_hint and getattr(npc_hint, "should_involve_npc", False):
            gate_result.npc_allowed = True
            gate_result.npc_reason = "NPC 脑建议介入"
            gate_result.add_gate_decision("npc", True, "NPC 脑建议")
        else:
            gate_result.npc_allowed = False
            gate_result.npc_reason = "本轮不需要 NPC 介入"
            gate_result.add_gate_decision("npc", False, "无需介入")
    
    def _gate_model_selection(
        self,
        turn_context: TurnContext,
        gate_result: ReplyGateResult
    ) -> None:
        """模型选择门控"""
        supervisor = turn_context.supervisor_decision
        if supervisor:
            gate_result.model_tier = getattr(supervisor, "final_model_tier", "standard")
        else:
            gate_result.model_tier = "standard"
        
        gate_result.add_gate_decision("model", True, f"tier={gate_result.model_tier}")
    
    def _gate_response_style(
        self,
        turn_context: TurnContext,
        gate_result: ReplyGateResult
    ) -> None:
        """回复风格门控"""
        plan = turn_context.behavior_plan_v2
        if plan:
            gate_result.final_style = getattr(plan, "response_style", "friendly")
            gate_result.final_length = getattr(plan, "response_length", "medium")
        else:
            gate_result.final_style = "friendly"
            gate_result.final_length = "medium"
        
        gate_result.add_gate_decision("style", True, f"style={gate_result.final_style}")
    
    def _build_memory_context(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        构建三层记忆上下文（V9 新增）
        
        从 prompt_memory_context 或服务中获取记忆上下文
        """
        if turn_context.prompt_memory_context:
            return turn_context.prompt_memory_context
        
        memory_services = services.get("memory_services", {})
        context = {}
        
        working_memory = memory_services.get("working")
        if working_memory:
            context["working_memory"] = working_memory.to_prompt_context()
            context["dialogue_history"] = working_memory.get_dialogue_history()
        
        episodic_memory = memory_services.get("episodic")
        if episodic_memory:
            context["episodic_memory"] = episodic_memory.to_prompt_context()
            context["recent_events"] = episodic_memory.get_recent_events()
        
        core_memory = memory_services.get("core")
        if core_memory:
            context["core_memory"] = core_memory.to_prompt_context()
            context["persona"] = core_memory.get_persona()
        
        return context
    
    async def _compose_with_failure(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any],
        gate_result: ReplyGateResult,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """执行失败时的回复策略"""
        execution_result = turn_context.execution_result
        failed_tools = execution_result.get_failed_tools()
        
        for tool_name in failed_tools:
            if "not found" in str(execution_result.error or "").lower():
                return self.FALLBACK_TEMPLATES["tool_not_found"]
        
        character_context = services.get("character_context", {})
        llm = self._select_llm(turn_context, services)
        
        prompt = self.prompt_builder.build_from_turn_context(
            turn_context,
            character_context,
            include_execution_result=True,
            include_supervisor_decision=True,
            include_world_content=gate_result.world_content_allowed,
            expand_world_topic=gate_result.world_expand_allowed,
            memory_context=memory_context
        )
        
        try:
            return await llm.generate(prompt)
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            return self.FALLBACK_TEMPLATES["tool_failure"]
    
    async def _compose_with_results(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any],
        gate_result: ReplyGateResult,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """有执行结果时的回复策略"""
        character_context = services.get("character_context", {})
        llm = self._select_llm(turn_context, services)
        
        prompt = self.prompt_builder.build_from_turn_context(
            turn_context,
            character_context,
            include_execution_result=True,
            include_supervisor_decision=True,
            include_world_content=gate_result.world_content_allowed,
            expand_world_topic=gate_result.world_expand_allowed,
            memory_context=memory_context
        )
        
        try:
            return await llm.generate(prompt)
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            return "抱歉，我暂时无法回应，请稍后再试。"
    
    async def _compose_normal(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any],
        gate_result: ReplyGateResult,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """正常回复策略"""
        character_context = services.get("character_context", {})
        llm = self._select_llm(turn_context, services)
        
        prompt = self.prompt_builder.build_from_turn_context(
            turn_context,
            character_context,
            include_execution_result=True,
            include_supervisor_decision=True,
            include_world_content=gate_result.world_content_allowed,
            expand_world_topic=gate_result.world_expand_allowed,
            memory_context=memory_context
        )
        
        try:
            return await llm.generate(prompt)
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            return "抱歉，我暂时无法回应，请稍后再试。"
    
    def _select_llm(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> Any:
        """选择回复模型"""
        reply_llm_getter = services.get("reply_llm")
        
        if callable(reply_llm_getter):
            return reply_llm_getter(turn_context)
        
        if self.model_router and turn_context.supervisor_decision:
            tier = turn_context.supervisor_decision.final_model_tier
            return self.model_router.get_llm_for_tier(tier)
        
        return services.get("llm")
    
    def _create_outbound_message(
        self,
        turn_context: TurnContext,
        response_text: str,
        gate_result: ReplyGateResult
    ) -> OutboundMessage:
        """创建出站消息"""
        metadata = {
            "gate_result": gate_result.to_dict()
        }
        
        if turn_context.emotion_insight:
            metadata["emotion"] = turn_context.emotion_insight.primary_emotion
        
        if turn_context.behavior_plan_v2:
            metadata["mode"] = turn_context.behavior_plan_v2.mode
        
        if turn_context.supervisor_decision:
            metadata["model_tier"] = turn_context.supervisor_decision.final_model_tier
        
        if turn_context.execution_result:
            metadata["execution_success"] = turn_context.execution_result.success
            if turn_context.execution_result.tool_results:
                metadata["tools_used"] = [r.tool_name for r in turn_context.execution_result.tool_results if r.success]
        
        return OutboundMessage(
            id=f"msg_{datetime.now().timestamp()}",
            message_type=MessageType.RESPONSE,
            content=response_text,
            metadata=metadata
        )
