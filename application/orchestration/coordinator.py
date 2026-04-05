"""
Agent 协调器

V9 修复版：门面协调器

职责：
1. start() / stop() 生命周期
2. handle_user_input() 入口 - 委托给 TurnOrchestrator
3. get_state() 状态查询
4. 组装各个子组件

V9 修复：
- 导入 application.brains 而非 application.cognition
- 使用 MemoryFacade 统一记忆接口
- 正确传递三层记忆给 MemoryBrain
- 使用 world_runtime 而非 world_service
"""

from typing import Dict, Any, Optional, List
import logging
import asyncio
from datetime import datetime

from domain.emotion.service import EmotionService
from domain.world_state.port import WorldRuntimePort
from domain.proactivity.service import ProactiveInteractionService
from infrastructure.tools.base import BaseTool
from domain.npc import NPCManager
from infrastructure.llm.base import BaseLLM
from infrastructure.events.bus import global_event_bus, EventType

from application.orchestration.turn_orchestrator import TurnOrchestrator
from application.orchestration.background_runtime import BackgroundRuntime
from application.orchestration.event_bridge import EventBridge
from application.orchestration.turn_context import TurnContext
from application.brains import BrainRegistry
from application.brains.model_router import ModelRouter
from application.prompting.builder import PromptBuilder
from application.messaging.outbound_queue import OutboundQueue
from application.messaging.response_models import AgentResponse
from application.memory.facade import MemoryFacade

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Agent 协调器
    
    V9 修复版：
    - 使用 MemoryFacade 统一记忆接口
    - 正确初始化六脑
    - 委托编排给 TurnOrchestrator
    """
    
    def __init__(
        self,
        llm: BaseLLM,
        emotion_service: EmotionService,
        memory_services: Dict[str, Any],
        world_runtime: WorldRuntimePort,
        proactive_service: ProactiveInteractionService,
        enable_proactivity: bool = False,
        proactive_check_interval: float = 300.0,
        proactive_message_composer=None,
        character_context: Optional[Dict[str, Any]] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        tools: Optional[Dict[str, BaseTool]] = None,
        npc_manager: Optional[NPCManager] = None,
        model_router: Optional[ModelRouter] = None,
        brain_llms: Optional[Dict[str, BaseLLM]] = None,
        reply_llm: Optional[BaseLLM] = None,
        world_content_service=None,
        reality_feed_service=None,
        memory_consolidation_service=None
    ):
        self.llm = llm
        self.emotion_service = emotion_service
        self.world_runtime = world_runtime
        self.proactive_service = proactive_service
        self.enable_proactivity = enable_proactivity
        self.proactive_check_interval = proactive_check_interval
        self.proactive_message_composer = proactive_message_composer
        self.character_context = character_context or {}
        self.tools = tools or {}
        self.npc_manager = npc_manager
        self.model_router = model_router
        self.brain_llms = brain_llms or {}
        self.reply_llm = reply_llm or llm
        self.world_content_service = world_content_service
        self.reality_feed_service = reality_feed_service
        self.memory_consolidation_service = memory_consolidation_service
        
        self.core_memory = memory_services.get("core")
        self.episodic_memory = memory_services.get("episodic")
        self.working_memory = memory_services.get("working")
        
        self.memory_facade = MemoryFacade(
            core_memory=self.core_memory,
            episodic_memory=self.episodic_memory,
            working_memory=self.working_memory
        )
        
        self.prompt_builder = prompt_builder or PromptBuilder(style="friendly")
        
        self.brain_registry = BrainRegistry()
        self._setup_brains()
        
        self.outbound_queue = OutboundQueue()
        
        self.turn_orchestrator = TurnOrchestrator(
            brain_registry=self.brain_registry,
            prompt_builder=self.prompt_builder,
            outbound_queue=self.outbound_queue,
            world_content_service=world_content_service,
            reality_feed_service=reality_feed_service,
            tools=self.tools,
            world_service=world_runtime,
            model_router=model_router,
            npc_manager=npc_manager
        )
        
        self.background_runtime = BackgroundRuntime(
            world_service=world_runtime,
            proactive_service=proactive_service if enable_proactivity else None,
            proactive_message_composer=proactive_message_composer,
            memory_consolidation_service=memory_consolidation_service,
            memory_services=memory_services,
            proactive_check_interval=proactive_check_interval
        )
        
        self.event_bridge = EventBridge()
        self._setup_events()
        
        self.is_running = False
        self.current_conversation_id = None
        self.last_interaction_time = datetime.now().timestamp()
        
        logger.info("AgentCoordinator 初始化完成")
    
    def _setup_brains(self) -> None:
        """设置六脑系统 - V9 修复版"""
        from application.brains import (
            EmotionBrain, MemoryBrain, WorldBrain,
            NPCBrain, BehaviorBrain, SupervisorBrain
        )
        
        emotion_llm = self.brain_llms.get("emotion", self.llm)
        self.brain_registry.register(
            EmotionBrain(llm=emotion_llm, emotion_service=self.emotion_service),
            priority=10
        )
        
        memory_llm = self.brain_llms.get("memory", self.llm)
        self.brain_registry.register(
            MemoryBrain(
                llm=memory_llm,
                core_memory=self.core_memory,
                episodic_memory=self.episodic_memory,
                working_memory=self.working_memory
            ),
            priority=20
        )
        
        world_llm = self.brain_llms.get("world", self.llm)
        self.brain_registry.register(
            WorldBrain(
                llm=world_llm,
                world_runtime=self.world_runtime,
                world_content_service=self.world_content_service
            ),
            priority=30
        )
        
        npc_llm = self.brain_llms.get("npc", self.llm)
        self.brain_registry.register(
            NPCBrain(llm=npc_llm, npc_manager=self.npc_manager),
            priority=40
        )
        
        behavior_llm = self.brain_llms.get("behavior", self.llm)
        self.brain_registry.register(
            BehaviorBrain(llm=behavior_llm),
            priority=50
        )
        
        supervisor_llm = self.brain_llms.get("supervisor", self.llm)
        self.brain_registry.register(
            SupervisorBrain(llm=supervisor_llm, character_config=self.character_context),
            priority=100
        )
        
        logger.info(f"六脑系统初始化完成: {self.brain_registry.list_brains()}")
    
    def _setup_events(self) -> None:
        """设置事件处理器"""
        self.event_bridge.register(EventType.MESSAGE_RECEIVED, self._on_message_received)
        self.event_bridge.register(EventType.MESSAGE_SENT, self._on_message_sent)
        self.event_bridge.register(EventType.EMOTION_UPDATED, self._on_emotion_updated)
        self.event_bridge.register(EventType.PROACTIVE_TRIGGERED, self._on_proactive_triggered)
    
    def _on_message_received(self, message) -> None:
        self.last_interaction_time = datetime.now().timestamp()
        if self.proactive_service:
            self.proactive_service.update_last_interaction()
    
    def _on_message_sent(self, message) -> None:
        self.last_interaction_time = datetime.now().timestamp()
    
    def _on_emotion_updated(self, emotional_state) -> None:
        logger.debug(f"情绪更新: {emotional_state}")
    
    def _on_proactive_triggered(self, data) -> None:
        logger.info(f"主动消息触发: {data}")
    
    async def start(self) -> None:
        """启动系统"""
        if self.is_running:
            return
        
        self.is_running = True
        self.current_conversation_id = f"conv_{datetime.now().timestamp()}"
        
        if self.enable_proactivity:
            self.background_runtime.set_proactive_callback(self._handle_proactive_message)
        
        self.event_bridge.bind()
        await self.background_runtime.start()
        
        self.event_bridge.publish(EventType.SYSTEM_STARTED, {
            "conversation_id": self.current_conversation_id
        })
        
        logger.info(f"AgentCoordinator 启动，会话 ID: {self.current_conversation_id}")
    
    async def _handle_proactive_message(self, message) -> None:
        """
        处理主动消息
        
        V9 改版：主动消息回调处理
        - 真正 enqueue 到 outbound_queue
        - 存入 working memory 保持对话连续性
        """
        content = getattr(message, "content", "")
        trigger_type = getattr(message, "trigger_type", None)
        priority = getattr(message, "priority", 5)
        
        logger.info(f"处理主动消息: {content[:50] if content else message}")
        
        from application.messaging.outbound_queue import OutboundMessage, MessageType
        
        outbound_msg = OutboundMessage(
            id=f"proactive_{datetime.now().timestamp()}",
            message_type=MessageType.PROACTIVE,
            content=content,
            metadata={
                "trigger_type": trigger_type.value if trigger_type else "unknown",
                "priority": priority
            }
        )
        
        await self.outbound_queue.enqueue(outbound_msg)
        
        if self.working_memory:
            self.working_memory.add_dialogue("assistant", content)
        
        self.event_bridge.publish(EventType.PROACTIVE_TRIGGERED, {
            "content": content,
            "trigger_type": trigger_type.value if trigger_type else "unknown",
            "priority": priority
        })
    
    async def stop(self) -> None:
        """停止系统"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        await self.background_runtime.stop()
        self.event_bridge.unbind()
        
        self.event_bridge.publish(EventType.SYSTEM_STOPPED, {
            "conversation_id": self.current_conversation_id
        })
        
        logger.info("AgentCoordinator 停止")
    
    async def handle_user_input(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        处理用户输入
        
        主入口方法，委托给 TurnOrchestrator
        """
        if not self.is_running:
            await self.start()
        
        self.last_interaction_time = datetime.now().timestamp()
        if self.proactive_service:
            self.proactive_service.update_last_interaction()
        
        turn_context = TurnContext()
        
        user_message = self.memory_facade.store_message(
            role="human",
            content=user_input
        )
        turn_context.set_user_input(user_input, user_message.id)
        
        turn_context.set_prompt_memory_context(self._build_prompt_memory_context())
        
        services = self._build_services_dict()
        
        response_text, outbound_msg, gate_result = await self.turn_orchestrator.orchestrate(
            user_input=user_input,
            turn_context=turn_context,
            services=services
        )
        
        if gate_result:
            turn_context.reply_gate_result = gate_result
        
        self.event_bridge.publish(EventType.MESSAGE_SENT, outbound_msg)
        
        self._update_proactive_context(turn_context)
        
        return AgentResponse(
            text=response_text,
            world_state=turn_context.world_state,
            recent_messages_count=len(turn_context.recent_messages),
            relevant_memories_count=len(turn_context.relevant_memories),
            response_message_id=outbound_msg.id,
            delivery_required=True,
            emotion_insight=turn_context.emotion_insight.to_dict() if turn_context.emotion_insight else None,
            memory_decision=turn_context.memory_decision.to_dict() if turn_context.memory_decision else None,
            world_update_proposal=turn_context.world_update_proposal.to_dict() if turn_context.world_update_proposal else None,
            npc_interaction_hint=turn_context.npc_interaction_hint.to_dict() if turn_context.npc_interaction_hint else None,
            behavior_plan_v2=turn_context.behavior_plan_v2.to_dict() if turn_context.behavior_plan_v2 else None,
            supervisor_decision=turn_context.supervisor_decision.to_dict() if turn_context.supervisor_decision else None,
            execution_result=turn_context.execution_result.to_dict() if turn_context.execution_result else None,
            world_changes=turn_context.world_changes,
            debug={
                "phase": turn_context.phase,
                "model_tier": turn_context.supervisor_decision.final_model_tier if turn_context.supervisor_decision else None,
                "trace": turn_context.execution_result.trace if turn_context.execution_result else [],
                "warnings": turn_context.execution_result.warnings if turn_context.execution_result else [],
                "gate_result": gate_result.to_dict() if gate_result else None
            },
            _turn_context=turn_context
        )
    
    def _build_services_dict(self) -> Dict[str, Any]:
        """构建服务字典
        
        V9 改版：添加 memory_services 字段供 ReplyComposer 使用
        """
        return {
            "llm": self.llm,
            "reply_llm": self._select_reply_llm,
            "emotion_service": self.emotion_service,
            "memory_service": self.memory_facade,
            "core_memory": self.core_memory,
            "episodic_memory": self.episodic_memory,
            "working_memory": self.working_memory,
            "memory_services": {
                "core": self.core_memory,
                "episodic": self.episodic_memory,
                "working": self.working_memory,
                "consolidation": self.memory_consolidation_service
            },
            "world_runtime": self.world_runtime,
            "npc_manager": self.npc_manager,
            "tools": self.tools,
            "character_context": self.character_context,
            "model_router": self.model_router,
            "memory_consolidation_service": self.memory_consolidation_service
        }
    
    def _select_reply_llm(self, turn_context: TurnContext) -> BaseLLM:
        """根据 Supervisor 决策选择回复模型"""
        llm = self.reply_llm
        
        if turn_context.supervisor_decision and self.model_router:
            tier = getattr(turn_context.supervisor_decision, "final_model_tier", "standard")
            if tier == "cheap":
                llm = self.model_router.get_cheap_llm()
            elif tier == "top":
                llm = self.model_router.get_top_llm()
        
        return llm
    
    def _build_prompt_memory_context(self) -> Dict[str, Any]:
        """
        V10: 预构建三层记忆 prompt 上下文
        
        在 handle_user_input() 入口处提前构建，
        这样 ReplyComposer 不用再自己拼
        """
        context = {}
        
        if self.working_memory:
            prompt_ctx = self.working_memory.to_prompt_context() if hasattr(self.working_memory, 'to_prompt_context') else ""
            context["working_memory"] = prompt_ctx
            dialogue_history = self.working_memory.get_dialogue_history() if hasattr(self.working_memory, 'get_dialogue_history') else []
            context["dialogue_history"] = [
                e.to_dict() if hasattr(e, "to_dict") else {"role": getattr(e, "role", "unknown"), "content": str(e)}
                for e in dialogue_history
            ]
        
        if self.episodic_memory:
            prompt_ctx = self.episodic_memory.to_prompt_context() if hasattr(self.episodic_memory, 'to_prompt_context') else ""
            context["episodic_memory"] = prompt_ctx
            recent_events = self.episodic_memory.get_recent_events() if hasattr(self.episodic_memory, 'get_recent_events') else []
            context["recent_events"] = [
                e.to_dict() if hasattr(e, "to_dict") else {"description": str(e)}
                for e in recent_events
            ]
        
        if self.core_memory:
            prompt_ctx = self.core_memory.to_prompt_context() if hasattr(self.core_memory, 'to_prompt_context') else ""
            context["core_memory"] = prompt_ctx
            persona = self.core_memory.get_persona() if hasattr(self.core_memory, 'get_persona') else {}
            context["persona"] = persona
        
        return context
    
    def _update_proactive_context(self, turn_context: TurnContext) -> None:
        """
        V10: 回灌主动交互上下文
        
        每轮结束后更新 BackgroundRuntime 的主动交互上下文
        
        V10 修复：无论 enable_proactivity 是否开启都更新 context
        避免恢复后误触发
        """
        last_emotion = None
        last_support_need = "none"
        if turn_context.emotion_insight:
            last_emotion = getattr(turn_context.emotion_insight, "primary_emotion", None)
            last_support_need = getattr(turn_context.emotion_insight, "support_need", "none")
        
        last_world_event = None
        if turn_context.recent_world_events:
            first_event = turn_context.recent_world_events[0]
            if hasattr(first_event, "description"):
                last_world_event = first_event.description
            elif isinstance(first_event, dict):
                last_world_event = first_event.get("description", str(first_event))
            else:
                last_world_event = str(first_event)
        
        pending_promises = []
        if self.working_memory and hasattr(self.working_memory, "get_pending_promises"):
            pending_promises = self.working_memory.get_pending_promises()
        
        recent_npc_interactions = []
        if turn_context.npc_interaction_hint:
            npc_name = getattr(turn_context.npc_interaction_hint, "target_npc_id", None)
            if npc_name:
                recent_npc_interactions.append(npc_name)
        
        self.background_runtime.update_proactive_context(
            last_emotion=last_emotion,
            last_support_need=last_support_need,
            last_world_event=last_world_event,
            pending_promises=pending_promises,
            recent_npc_interactions=recent_npc_interactions
        )
    
    def get_agent_state(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "is_running": self.is_running,
            "conversation_id": self.current_conversation_id,
            "tools_available": list(self.tools.keys()),
            "npc_manager_enabled": self.npc_manager is not None,
            "world_content_enabled": self.world_content_service is not None,
            "last_interaction": self.last_interaction_time,
            "background_runtime": self.background_runtime.get_status(),
            "memory_stats": self.memory_facade.get_stats()
        }
    
    def get_pending_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取待发送消息"""
        messages = self.outbound_queue.get_pending(limit)
        return [
            {
                "id": msg.id,
                "message_type": msg.message_type.value,
                "content": msg.content
            }
            for msg in messages
        ]
    
    async def mark_message_delivered(self, message_id: str) -> bool:
        """标记消息已发送"""
        return await self.outbound_queue.mark_delivered(message_id)
    
    async def pause_proactivity(self) -> None:
        """暂停主动回复"""
        self.enable_proactivity = False
        await self.background_runtime.pause_proactivity()
        logger.info("主动回复已暂停")
    
    async def resume_proactivity(self) -> None:
        """恢复主动回复"""
        self.enable_proactivity = True
        self.background_runtime.proactive_service = self.proactive_service
        self.background_runtime.set_proactive_callback(self._handle_proactive_message)
        await self.background_runtime.resume_proactivity()
        logger.info("主动回复已恢复")
    
    def get_proactivity_status(self) -> Dict[str, Any]:
        """获取主动回复状态"""
        status = self.background_runtime.get_status()
        return {
            "enabled": self.enable_proactivity,
            "task_active": status.get("proactive_task_active", False),
            "check_interval": status.get("proactive_check_interval"),
            "context": status.get("proactive_context", {})
        }
