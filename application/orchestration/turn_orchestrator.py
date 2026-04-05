"""
轮次编排器

V7 核心组件：只负责一轮对话的编排。
从 coordinator 中分离出来，职责单一。

主链流程：
Input -> CollectContext -> RunBrains -> ResolvePlan -> CompilePlan -> Execute -> GenerateReply -> Commit

这是真正的主线，coordinator 只是门面。

V7 改进（基于修改意见第1次整改）：
- 六脑逐个执行、逐个写回上下文（解决"本轮信息输入不到行为层"问题）
- 每个脑执行后立刻写回 TurnContext，后续脑可读取
- 增加 resolve 步骤，融合 supervisor 裁决
- 全流程推进 phase
- post_commit 真正处理 world_updates
- 使用 ReplyComposer 生成回复
"""

from typing import Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from application.orchestration.turn_context import TurnContext
from application.orchestration.plan_compiler import PlanCompiler
from application.orchestration.executor import ActionExecutor
from application.orchestration.reply_composer import ReplyComposer
from application.brains import BrainRegistry
from application.prompting.builder import PromptBuilder
from application.messaging.outbound_queue import OutboundQueue, OutboundMessage, MessageType
from domain.policy.fallback_policy import FallbackPolicy, FallbackDecision
from application.contracts import ExecutablePlan, ExecutionResult, ActionPlanV2, SupervisorDecision
from infrastructure.events.bus import global_event_bus, EventType

logger = logging.getLogger(__name__)


class TurnOrchestrator:
    """
    轮次编排器
    
    V6 主线编排器，负责一轮对话的完整流程：
    1. 收集上下文 -> phase: context_collected
    2. 运行六脑 -> phase: brains_completed
    3. 检查紧急情况 -> phase: policy_checked
    4. resolve 行为计划（融合 supervisor）
    5. 编译计划 -> phase: plan_compiled
    6. 执行动作 -> phase: executed
    7. 生成回复 -> phase: responded
    8. 提交更新 -> phase: committed
    
    不负责：
    - 后台任务
    - 事件订阅
    - 服务生命周期
    """
    
    def __init__(
        self,
        brain_registry: BrainRegistry,
        prompt_builder: PromptBuilder,
        outbound_queue: OutboundQueue,
        world_content_service=None,
        reality_feed_service=None,
        tools: Optional[Dict[str, Any]] = None,
        world_service=None,
        model_router=None,
        npc_manager=None
    ):
        self.brain_registry = brain_registry
        self.prompt_builder = prompt_builder
        self.outbound_queue = outbound_queue
        self.world_content_service = world_content_service
        self.reality_feed_service = reality_feed_service
        self.tools = tools or {}
        self.world_service = world_service
        self.model_router = model_router
        self.npc_manager = npc_manager
        
        self.plan_compiler = PlanCompiler()
        self.action_executor = ActionExecutor(
            tool_registry=self.tools,
            world_service=world_service,
            world_content_service=world_content_service,
            npc_manager=npc_manager
        )
        self.fallback_policy = FallbackPolicy()
        self.reply_composer = ReplyComposer(
            prompt_builder=prompt_builder,
            outbound_queue=outbound_queue,
            model_router=model_router
        )
        
        self._world_lock = asyncio.Lock()
    
    async def orchestrate(
        self,
        user_input: str,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> tuple:
        """
        编排一轮对话
        
        主链流程（唯一主链）：
        Input -> CollectContext -> RunBrains -> ResolvePlan -> CompilePlan -> Execute -> GenerateReply -> Commit
        
        Args:
            user_input: 用户输入
            turn_context: 轮次上下文（唯一黑板）
            services: 服务字典
            
        Returns:
            (response_text, outbound_message)
        """
        turn_context.add_trace("开始编排")
        
        await self._collect_context(user_input, turn_context, services)
        turn_context.set_phase("context_collected")
        turn_context.add_trace("上下文收集完成")
        
        brain_outputs = await self._run_brains(turn_context)
        turn_context.set_phase("brains_completed")
        turn_context.add_trace("六脑运行完成")
        
        emergency = self._check_emergency(turn_context)
        turn_context.set_phase("policy_checked")
        
        if emergency:
            logger.warning(f"紧急情况，使用兜底策略: {emergency.reasoning}")
            turn_context.add_warning(f"紧急情况: {emergency.reasoning}")
            return await self._handle_emergency(emergency, turn_context, services)
        
        resolved_plan = self._resolve_behavior_plan(
            turn_context.behavior_plan_v2,
            turn_context.supervisor_decision
        )
        turn_context.add_trace("行为计划 resolve 完成")
        
        if resolved_plan and getattr(resolved_plan, "world_expression_mode", None):
            turn_context.set_world_expression_mode(resolved_plan.world_expression_mode)
            turn_context.add_trace(f"世界表达级别: {resolved_plan.world_expression_mode}")
        
        executable_plan = self._compile_plan(resolved_plan, turn_context)
        turn_context.set_executable_plan(executable_plan)
        turn_context.set_phase("plan_compiled")
        turn_context.add_trace(f"计划编译完成: {executable_plan.action_type.value}")
        
        execution_result = await self._execute(executable_plan, turn_context)
        turn_context.set_execution_result(execution_result)
        turn_context.set_phase("executed")
        turn_context.add_trace(f"执行完成: success={execution_result.success}")
        
        if execution_result.warnings:
            for w in execution_result.warnings:
                turn_context.add_warning(w)
        
        response_text, outbound_msg, gate_result = await self._generate_response(turn_context, services)
        turn_context.set_final_response(response_text)
        turn_context.reply_gate_result = gate_result
        turn_context.set_phase("responded")
        turn_context.add_trace("回复生成完成")
        
        await self._post_commit(turn_context, services)
        turn_context.set_phase("committed")
        turn_context.add_trace("编排完成")
        
        return response_text, outbound_msg, gate_result
    
    def _resolve_behavior_plan(
        self,
        behavior_plan: Optional[ActionPlanV2],
        supervisor_decision: Optional[SupervisorDecision]
    ) -> Optional[ActionPlanV2]:
        """
        融合 supervisor 裁决，生成最终行为计划
        
        只做这几件事：
        1. 覆盖主动作
        2. 抑制工具
        3. 抑制 NPC
        4. 调整回复风格
        5. V10: 覆盖世界表达级别
        """
        if behavior_plan is None:
            return None
        
        if supervisor_decision is None:
            return behavior_plan
        
        if supervisor_decision.override_action_type is not None:
            behavior_plan.primary_action = supervisor_decision.override_action_type
            logger.info(f"Supervisor override action: {supervisor_decision.override_action_type.value}")
        
        if supervisor_decision.suppress_tool_execution:
            behavior_plan.tool_plan = []
            behavior_plan.requires_tool_result = False
            logger.info("Supervisor suppressed tool execution")
        
        if supervisor_decision.suppress_npc:
            behavior_plan.npc_plan = {}
            logger.info("Supervisor suppressed NPC interaction")
        
        if supervisor_decision.conflict_resolution == "prioritize_comfort":
            behavior_plan.response_style = "empathetic"
        
        if supervisor_decision.override_world_expression_mode is not None:
            behavior_plan.world_expression_mode = supervisor_decision.override_world_expression_mode
            logger.info(f"Supervisor override world_expression_mode: {supervisor_decision.override_world_expression_mode}")
        
        return behavior_plan
    
    async def _collect_context(
        self,
        user_input: str,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> None:
        """
        收集轮次上下文
        
        V9 修复：使用 WorldRuntimePort 新接口
        - get_world_snapshot() 替代 get_world_state()
        - get_recent_events() 保持不变
        """
        emotion_service = services.get("emotion_service")
        memory_service = services.get("memory_service")
        world_runtime = services.get("world_runtime") or services.get("virtual_world_service")
        npc_manager = services.get("npc_manager")
        tools = services.get("tools", {})
        
        if emotion_service:
            emotional_state = emotion_service.analyze_and_update(user_input)
            turn_context.set_emotional_state(emotional_state)
        
        if memory_service:
            recent_messages = memory_service.get_recent_messages(limit=10)
            turn_context.set_recent_messages(recent_messages)
            
            relevant_memories = memory_service.retrieve_memories(user_input, limit=5)
            turn_context.set_relevant_memories(relevant_memories)
        
        if world_runtime:
            async with self._world_lock:
                world_snapshot = await world_runtime.get_world_snapshot()
            turn_context.set_world_snapshot(world_snapshot)
            turn_context.set_world_state(world_snapshot)
            
            recent_events = await world_runtime.get_recent_events(limit=3)
            turn_context.set_recent_world_events(recent_events)
            turn_context.set_recent_events(recent_events)
        
        turn_context.set_available_tools(list(tools.keys()))
        
        if npc_manager and turn_context.world_snapshot:
            location_name = getattr(turn_context.world_snapshot, 'location', '未知')
            nearby_npcs = await world_runtime.get_npcs_at_location(location_name)
            turn_context.set_nearby_npcs(nearby_npcs)
        
        if self.world_content_service:
            if self.world_content_service.should_refresh():
                await self._refresh_world_content()
            
            world_content_items = self.world_content_service.get_latest_content(limit=5)
            turn_context.set_world_content_items(world_content_items)
    
    async def _run_brains(self, turn_context: TurnContext) -> Dict[str, Any]:
        """
        按顺序运行六脑，并在每个脑执行后立刻写回上下文
        
        V7 改进：
        - 逐脑执行、逐脑写回
        - 解决"本轮信息输入不到行为层"问题
        - 后续脑可读取前面脑的结果
        """
        results: Dict[str, Any] = {}

        sorted_brains = sorted(
            self.brain_registry._brains.items(),
            key=lambda x: self.brain_registry._priorities.get(x[0], 50)
        )

        for brain_name, brain in sorted_brains:
            try:
                result = await brain.process(turn_context)
                results[brain_name] = result

                self._apply_single_brain_output(turn_context, brain_name, result)

                turn_context.add_trace(f"{brain_name} 脑执行完成并已写回")
                logger.debug(f"脑子 {brain_name} 执行完成并已写回上下文")

            except Exception as e:
                logger.error(f"脑子 {brain_name} 执行失败: {e}")
                turn_context.add_warning(f"脑子 {brain_name} 执行失败: {e}")

        logger.info(f"六脑系统运行完成，共 {len(results)} 个脑子输出")
        return results
    
    def _apply_single_brain_output(
        self,
        turn_context: TurnContext,
        brain_name: str,
        result: Any
    ) -> None:
        """
        单个脑结果立刻写回上下文
        
        V7 新增方法：
        - 每个脑执行后立刻写回
        - 确保后续脑可读取当前轮的结果
        """
        if result is None:
            return

        if brain_name == "emotion":
            turn_context.set_emotion_insight(result)
            logger.debug(
                f"情绪脑输出已写回: "
                f"{getattr(result, 'primary_emotion', 'unknown')}"
            )

        elif brain_name == "memory":
            turn_context.set_memory_decision(result)
            logger.debug(
                f"记忆脑输出已写回: "
                f"write_core={getattr(result, 'write_core', False)}, "
                f"write_episodic={getattr(result, 'write_episodic', False)}, "
                f"write_working={getattr(result, 'write_working', True)}"
            )

        elif brain_name == "world":
            turn_context.set_world_brain_output(result)
            logger.debug(
                f"世界脑输出已写回: "
                f"should_apply={getattr(result, 'should_apply_update', False)}, "
                f"should_read={getattr(result, 'should_read_world_content', False)}"
            )

        elif brain_name == "npc":
            turn_context.set_npc_interaction_hint(result)
            logger.debug(
                f"NPC脑输出已写回: "
                f"should_involve={getattr(result, 'should_involve_npc', False)}"
            )

        elif brain_name == "behavior":
            turn_context.set_behavior_plan_v2(result)
            logger.debug(
                f"行为脑输出已写回: "
                f"mode={getattr(result, 'mode', 'unknown')}, "
                f"action={getattr(getattr(result, 'primary_action', None), 'value', 'unknown')}"
            )

        elif brain_name == "supervisor":
            turn_context.set_supervisor_decision(result)
            logger.debug(
                f"总控脑输出已写回: "
                f"tier={getattr(result, 'final_model_tier', 'unknown')}, "
                f"override={getattr(getattr(result, 'override_action_type', None), 'value', None)}"
            )
    
    def _apply_brain_outputs(
        self,
        turn_context: TurnContext,
        brain_outputs: Dict[str, Any]
    ) -> None:
        """应用脑子输出到上下文"""
        if "emotion" in brain_outputs:
            turn_context.set_emotion_insight(brain_outputs["emotion"])
            logger.debug(f"情绪脑输出: {brain_outputs['emotion'].primary_emotion}")
        
        if "memory" in brain_outputs:
            turn_context.set_memory_decision(brain_outputs["memory"])
            decision = brain_outputs["memory"]
            logger.debug(f"记忆脑输出: write_core={getattr(decision, 'write_core', False)}, write_episodic={getattr(decision, 'write_episodic', False)}")
        
        if "world" in brain_outputs:
            world_output = brain_outputs["world"]
            turn_context.set_world_brain_output(world_output)
            if hasattr(world_output, "world_update_proposal"):
                logger.debug(f"世界脑输出: time_advance={world_output.world_update_proposal.time_advance_minutes}")
        
        if "npc" in brain_outputs:
            turn_context.set_npc_interaction_hint(brain_outputs["npc"])
            logger.debug(f"NPC脑输出: involve={brain_outputs['npc'].should_involve_npc}")
        
        if "behavior" in brain_outputs:
            turn_context.set_behavior_plan_v2(brain_outputs["behavior"])
            logger.debug(f"行为脑输出: mode={brain_outputs['behavior'].mode}")
        
        if "supervisor" in brain_outputs:
            turn_context.set_supervisor_decision(brain_outputs["supervisor"])
            logger.debug(f"总控脑输出: tier={brain_outputs['supervisor'].final_model_tier}")
    
    def _check_emergency(self, turn_context: TurnContext) -> Optional[FallbackDecision]:
        """检查紧急情况"""
        return self.fallback_policy.check_emergency(
            turn_context.emotion_insight,
            turn_context.user_input
        )
    
    async def _handle_emergency(
        self,
        emergency: FallbackDecision,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> tuple:
        """处理紧急情况"""
        response_text = emergency.response_hint or "抱歉，我现在状态不太好，请稍后再聊。"
        
        outbound_msg = OutboundMessage(
            id=f"msg_{datetime.now().timestamp()}",
            message_type=MessageType.RESPONSE,
            content=response_text,
            metadata={"emergency": True, "action": emergency.action_type.value}
        )
        
        await self.outbound_queue.enqueue(outbound_msg)
        
        return response_text, outbound_msg
    
    def _compile_plan(
        self,
        resolved_plan: Optional[ActionPlanV2],
        turn_context: TurnContext
    ) -> ExecutablePlan:
        """编译执行计划"""
        return self.plan_compiler.compile(
            resolved_plan,
            {
                "world_brain_output": turn_context.world_brain_output,
                "npc_interaction_hint": turn_context.npc_interaction_hint,
                "memory_decision": turn_context.memory_decision
            },
            supervisor_decision=turn_context.supervisor_decision
        )
    
    async def _execute(
        self,
        executable_plan: ExecutablePlan,
        turn_context: TurnContext
    ) -> ExecutionResult:
        """执行动作"""
        return await self.action_executor.execute(executable_plan, turn_context)
    
    async def _generate_response(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> tuple:
        """生成回复（委托给 ReplyComposer）"""
        return await self.reply_composer.compose(turn_context, services)
    
    async def _post_commit(
        self,
        turn_context: TurnContext,
        services: Dict[str, Any]
    ) -> None:
        """
        后置提交
        
        V9 三层记忆系统：
        - 短期记忆: 写入会话文档（当前对话窗口、情绪轨迹）
        - 事件记忆: 写入事件档案（重大事件）
        - 长期记忆: 写入角色事实库（身份/偏好）
        - should_consolidate: 标记为 scheduled，由后台执行
        """
        memory_service = services.get("memory_service")
        core_memory = services.get("core_memory")
        episodic_memory = services.get("episodic_memory")
        working_memory = services.get("working_memory")
        memory_consolidation = services.get("memory_consolidation_service")
        document_store = services.get("memory_document_store")
        
        analysis_doc = getattr(turn_context, "memory_analysis_document", None)
        
        if analysis_doc and document_store:
            session_id = getattr(turn_context, "session_id", "default_session")
            
            session = document_store.get_session(session_id)
            if not session:
                session = document_store.create_session(session_id, ttl_minutes=10)
            
            for candidate in analysis_doc.short_term_candidates:
                session.active_topic = candidate.topic
                session.salience = candidate.salience
                
                if analysis_doc.emotion_insight:
                    session.add_emotion_trace(
                        turn_id=analysis_doc.turn_id,
                        primary_emotion=analysis_doc.emotion_insight.get("primary_emotion", "neutral"),
                        intensity=analysis_doc.emotion_insight.get("intensity", 0)
                    )
                
                session.add_dialogue_entry(
                    turn_id=analysis_doc.turn_id,
                    role="user",
                    content=analysis_doc.raw_input
                )
                
                if candidate.pending_followup:
                    session.add_pending_promise(candidate.topic)
                    if working_memory and hasattr(working_memory, "add_pending_promise"):
                        working_memory.add_pending_promise(candidate.topic)
                        logger.info(f"Working memory 写入 pending_promise: {candidate.topic}")
                
                logger.info(f"短期记忆更新: session={session_id}, topic={candidate.topic}")
        
        if turn_context.memory_decision:
            decision = turn_context.memory_decision
            
            if getattr(decision, "write_core", False) and core_memory:
                payload = getattr(decision, "core_payload", None)
                if payload:
                    key = payload.get("key", "unknown")
                    value = payload.get("value", turn_context.user_input)
                    category = payload.get("category", "identity")
                    core_memory.set_entry(key, value, category)
                    logger.info(f"Core memory 写入: key={key}, category={category}")
            
            if getattr(decision, "write_episodic", False) and episodic_memory:
                payload = getattr(decision, "episodic_payload", {})
                from domain.memory import EpisodicEventType
                event_type_str = payload.get("event_type", "user_interaction")
                try:
                    event_type = EpisodicEventType(event_type_str)
                except ValueError:
                    event_type = EpisodicEventType.USER_INTERACTION
                
                description = payload.get("description", turn_context.user_input)
                importance = getattr(decision, "importance", 0.5)
                
                episodic_memory.add_event(
                    event_type=event_type,
                    description=description,
                    importance=importance,
                    metadata=payload.get("metadata", {})
                )
                logger.info(f"Episodic memory 写入: type={event_type.value}, importance={importance}")
            
            if getattr(decision, "should_consolidate", False) and memory_consolidation:
                logger.info("触发记忆固化（标记为 scheduled，由后台执行）")
                turn_context.add_memory_write({
                    "layer": "consolidation",
                    "status": "scheduled"
                })
        
        if turn_context.execution_result and turn_context.execution_result.world_update_result:
            turn_context.add_world_change(turn_context.execution_result.world_update_result)
            logger.info(f"世界更新已记录: {turn_context.execution_result.world_update_result}")
    
    async def _refresh_world_content(self) -> None:
        """刷新世界内容"""
        if not self.world_content_service or not self.reality_feed_service:
            return
        
        try:
            signals = await self.reality_feed_service.collect_signals()
            added_count = await self.world_content_service.refresh_from_reality(signals)
            logger.info(f"世界内容刷新完成，处理了 {len(signals)} 个现实信号，新增 {added_count} 条内容")
        except Exception as e:
            logger.error(f"世界内容刷新失败: {e}")
