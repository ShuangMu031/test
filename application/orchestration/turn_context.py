"""
轮次上下文

V9 改版：唯一黑板 + 三层记忆支持

改进：
1. 增加 phase 字段，变成有阶段感的黑板
2. 明确各阶段应该存在的字段
3. 删除平铺重复字段，改用聚合结构
4. 核心字段全上真实类型
5. 增加 get_debug_snapshot() 调试输出方法
6. 增加 warnings/trace 追踪能力
7. 增加 to_debug_dict() 完整调试输出
8. V10: 增加三层记忆相关字段
"""

from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field
import logging

from application.contracts import (
    EmotionInsight,
    MemoryDecision,
    WorldBrainOutput,
    NPCInteractionHint,
    ActionPlanV2,
    SupervisorDecision,
    FallbackDecision,
    ExecutablePlan,
    ExecutionResult
)

logger = logging.getLogger(__name__)


TurnPhase = Literal[
    "initialized",
    "working_memory_written",
    "context_collected",
    "brains_completed",
    "policy_checked",
    "plan_compiled",
    "executed",
    "responded",
    "memory_committed",
    "committed"
]


@dataclass
class TurnContext:
    """
    轮次上下文 - 唯一黑板
    
    统一存储一轮对话的所有上下文信息。
    所有组件都从这里读取数据，不再使用散参数。
    
    V9 改进：
    - 增加三层记忆相关字段
    - 增加世界快照字段
    - 明确记忆写入阶段
    
    阶段约束：
    - initialized: 刚创建，只有 user_input
    - working_memory_written: 用户输入已写入 working memory
    - context_collected: 收集了 emotional_state, recent_messages, world_state 等
    - brains_completed: 各 brain 输出完成
    - policy_checked: policy 校验完成
    - plan_compiled: 编译成 executable_plan
    - executed: 执行完成，有 execution_result
    - responded: 响应已生成
    - memory_committed: 记忆已提交
    - committed: 后处理完成
    
    字段分类：
    
    原始轮次上下文（phase >= context_collected）：
    - user_input, user_message_id
    - emotional_state, recent_messages, relevant_memories
    - world_state, recent_events, nearby_npcs
    - available_tools, world_content_items
    
    三层记忆字段（V9 新增）：
    - working_memory_before: working memory 写入前状态
    - working_memory_after: working memory 写入后状态
    - memory_writes: 记忆写入记录
    - episodic_candidates: 事件记忆候选
    - core_update_candidates: 核心记忆更新候选
    - prompt_memory_context: 给 prompt 的记忆上下文
    
    世界字段（V9 新增）：
    - world_snapshot: 世界快照
    - recent_world_events: 最近世界事件
    
    正式阶段产物（phase >= brains_completed）：
    - emotion_insight: EmotionInsight
    - memory_decision: MemoryDecision
    - world_brain_output: WorldBrainOutput（聚合结构）
    - npc_interaction_hint: NPCInteractionHint
    - behavior_plan_v2: ActionPlanV2
    - supervisor_decision: SupervisorDecision
    
    后续阶段产物：
    - executable_plan: ExecutablePlan（phase >= plan_compiled）
    - execution_result: ExecutionResult（phase >= executed）
    - fallback_decision: FallbackDecision（phase >= policy_checked，可选）
    
    追踪字段：
    - warnings: 警告列表
    - trace: 执行轨迹
    - world_changes: 世界变更
    """
    
    phase: TurnPhase = "initialized"
    
    user_input: str = ""
    user_message_id: str = ""
    
    emotional_state: Any = None
    recent_messages: List[Any] = field(default_factory=list)
    relevant_memories: List[Any] = field(default_factory=list)
    world_state: Any = None
    recent_events: List[Any] = field(default_factory=list)
    nearby_npcs: List[Any] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)
    world_content_items: List[Any] = field(default_factory=list)
    
    working_memory_before: List[Any] = field(default_factory=list)
    working_memory_after: List[Any] = field(default_factory=list)
    memory_writes: List[Dict[str, Any]] = field(default_factory=list)
    episodic_candidates: List[Dict[str, Any]] = field(default_factory=list)
    core_update_candidates: List[Dict[str, Any]] = field(default_factory=list)
    prompt_memory_context: Dict[str, Any] = field(default_factory=dict)
    
    world_snapshot: Any = None
    recent_world_events: List[Any] = field(default_factory=list)
    
    emotion_insight: Optional[EmotionInsight] = None
    memory_decision: Optional[MemoryDecision] = None
    world_brain_output: Optional[WorldBrainOutput] = None
    npc_interaction_hint: Optional[NPCInteractionHint] = None
    behavior_plan_v2: Optional[ActionPlanV2] = None
    supervisor_decision: Optional[SupervisorDecision] = None
    fallback_decision: Optional[FallbackDecision] = None
    
    executable_plan: Optional[ExecutablePlan] = None
    execution_result: Optional[ExecutionResult] = None
    
    final_response_text: str = ""
    
    warnings: List[str] = field(default_factory=list)
    trace: List[str] = field(default_factory=list)
    world_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    brain_telemetry: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    brain_monologues: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    decision_tension: List[Dict[str, Any]] = field(default_factory=list)
    
    world_expression_mode: str = "suppressed"
    
    @property
    def world_update_proposal(self) -> Any:
        """从 world_brain_output 获取 world_update_proposal"""
        if self.world_brain_output:
            return self.world_brain_output.world_update_proposal
        return None
    
    @property
    def world_content_proposal(self) -> Any:
        """从 world_brain_output 获取 world_content_proposal"""
        if self.world_brain_output:
            return self.world_brain_output.world_content_proposal
        return None
    
    @property
    def has_emotion_insight(self) -> bool:
        """是否有情绪洞察"""
        return self.emotion_insight is not None
    
    @property
    def has_supervisor_decision(self) -> bool:
        """是否有总控决策"""
        return self.supervisor_decision is not None
    
    @property
    def has_executable_plan(self) -> bool:
        """是否有可执行计划"""
        return self.executable_plan is not None
    
    @property
    def has_execution_result(self) -> bool:
        """是否有执行结果"""
        return self.execution_result is not None
    
    def set_phase(self, new_phase: TurnPhase) -> None:
        """设置阶段"""
        self.phase = new_phase
        logger.debug(f"TurnContext phase: {self.phase}")
    
    def advance_phase(self, new_phase: TurnPhase) -> None:
        """推进阶段"""
        valid_transitions = {
            "initialized": ["working_memory_written", "context_collected"],
            "working_memory_written": ["context_collected"],
            "context_collected": ["brains_completed"],
            "brains_completed": ["policy_checked"],
            "policy_checked": ["plan_compiled"],
            "plan_compiled": ["executed"],
            "executed": ["responded"],
            "responded": ["memory_committed"],
            "memory_committed": ["committed"]
        }
        
        if new_phase in valid_transitions.get(self.phase, []):
            self.phase = new_phase
            logger.debug(f"TurnContext phase: {self.phase}")
        else:
            logger.warning(f"Invalid phase transition: {self.phase} -> {new_phase}")
            self.phase = new_phase
    
    def set_user_input(self, user_input: str, message_id: str = "") -> None:
        """设置用户输入"""
        self.user_input = user_input
        self.user_message_id = message_id
    
    def set_emotional_state(self, emotional_state: Any) -> None:
        """设置情绪状态"""
        self.emotional_state = emotional_state
    
    def set_recent_messages(self, messages: List[Any]) -> None:
        """设置最近消息"""
        self.recent_messages = messages
    
    def set_relevant_memories(self, memories: List[Any]) -> None:
        """设置相关记忆"""
        self.relevant_memories = memories
    
    def set_world_state(self, world_state: Any) -> None:
        """设置世界状态"""
        self.world_state = world_state
    
    def set_recent_events(self, events: List[Any]) -> None:
        """设置最近事件"""
        self.recent_events = events
    
    def set_nearby_npcs(self, npcs: List[Any]) -> None:
        """设置附近 NPC"""
        self.nearby_npcs = npcs
    
    def set_available_tools(self, tools: List[str]) -> None:
        """设置可用工具"""
        self.available_tools = tools
    
    def set_world_content_items(self, items: List[Any]) -> None:
        """设置世界内容"""
        self.world_content_items = items
    
    def set_working_memory_before(self, entries: List[Any]) -> None:
        """设置 working memory 写入前状态"""
        self.working_memory_before = entries
    
    def set_working_memory_after(self, entries: List[Any]) -> None:
        """设置 working memory 写入后状态"""
        self.working_memory_after = entries
    
    def add_memory_write(self, write: Dict[str, Any]) -> None:
        """添加记忆写入记录"""
        self.memory_writes.append(write)
    
    def add_episodic_candidate(self, candidate: Dict[str, Any]) -> None:
        """添加事件记忆候选"""
        self.episodic_candidates.append(candidate)
    
    def add_core_update_candidate(self, candidate: Dict[str, Any]) -> None:
        """添加核心记忆更新候选"""
        self.core_update_candidates.append(candidate)
    
    def set_prompt_memory_context(self, context: Dict[str, Any]) -> None:
        """设置给 prompt 的记忆上下文"""
        self.prompt_memory_context = context
    
    def set_world_snapshot(self, snapshot: Any) -> None:
        """设置世界快照"""
        self.world_snapshot = snapshot
    
    def set_recent_world_events(self, events: List[Any]) -> None:
        """设置最近世界事件"""
        self.recent_world_events = events
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要（V9 新增）"""
        return {
            "working_entries_count": len(self.working_memory_after),
            "episodic_candidates_count": len(self.episodic_candidates),
            "core_update_candidates_count": len(self.core_update_candidates),
            "memory_writes_count": len(self.memory_writes),
            "has_memory_decision": self.memory_decision is not None
        }
    
    def set_emotion_insight(self, insight: EmotionInsight) -> None:
        """设置情绪洞察"""
        self.emotion_insight = insight
    
    def set_memory_decision(self, decision: MemoryDecision) -> None:
        """设置记忆决策"""
        self.memory_decision = decision
    
    def set_world_brain_output(self, output: WorldBrainOutput) -> None:
        """设置世界脑输出"""
        self.world_brain_output = output
    

    def set_world_update_proposal(self, proposal) -> None:
        """兼容旧示例接口：仅设置 world_update_proposal。"""
        from application.contracts.world import WorldBrainOutput
        if proposal is None:
            self.world_brain_output = None
        elif isinstance(proposal, WorldBrainOutput):
            self.world_brain_output = proposal
        else:
            self.world_brain_output = WorldBrainOutput(world_update_proposal=proposal)

    def set_npc_interaction_hint(self, hint: NPCInteractionHint) -> None:
        """设置 NPC 交互提示"""
        self.npc_interaction_hint = hint
    
    def set_behavior_plan_v2(self, plan: ActionPlanV2) -> None:
        """设置行为计划 V2"""
        self.behavior_plan_v2 = plan
    
    def set_supervisor_decision(self, decision: SupervisorDecision) -> None:
        """设置总控决策"""
        self.supervisor_decision = decision
    
    def set_world_expression_mode(self, mode: str) -> None:
        """
        设置世界表达级别
        
        V7 新增：
        - suppressed: 压制，不主动说世界内容
        - light: 轻量，只允许一句环境氛围
        - contextual: 上下文式，只在当前话题直接相关时说
        - active: 主动展开，允许把世界内容作为主轴
        """
        valid_modes = {"suppressed", "light", "contextual", "active"}
        if mode in valid_modes:
            self.world_expression_mode = mode
        else:
            self.world_expression_mode = "suppressed"
    
    def set_fallback_decision(self, decision: FallbackDecision) -> None:
        """设置兜底决策"""
        self.fallback_decision = decision
    
    def set_executable_plan(self, plan: ExecutablePlan) -> None:
        """设置可执行计划"""
        self.executable_plan = plan
    
    def set_execution_result(self, result: ExecutionResult) -> None:
        """设置执行结果"""
        self.execution_result = result
    
    def add_world_change(self, change: Dict[str, Any]) -> None:
        """添加世界变更"""
        self.world_changes.append(change)
    
    def add_warning(self, msg: str) -> None:
        """添加警告"""
        self.warnings.append(msg)
        logger.warning(f"TurnContext warning: {msg}")
    
    def add_trace(self, msg: str) -> None:
        """添加执行轨迹"""
        self.trace.append(msg)
        logger.debug(f"TurnContext trace: {msg}")
    
    def record_telemetry(self, brain_name: str, **kwargs) -> None:
        """
        记录脑的原始遥测数据
        
        Args:
            brain_name: 脑名称
            **kwargs: 遥测数据键值对
        """
        if brain_name not in self.brain_telemetry:
            self.brain_telemetry[brain_name] = {}
        self.brain_telemetry[brain_name].update(kwargs)
        self.add_trace(f"已捕获 {brain_name} 的原始遥测数据")
    
    def record_monologue(
        self,
        brain_name: str,
        monologue: str = "",
        actions: List[str] = None,
        interactions: List[str] = None,
        tool_calls: List[str] = None,
        llm_thought: str = ""
    ) -> None:
        """
        记录脑的脑内独白
        
        Args:
            brain_name: 脑名称
            monologue: 脑内独白
            actions: 具体工作列表
            interactions: 脑间交互列表
            tool_calls: 工具/API调用列表
            llm_thought: LLM 原始推理
        """
        if brain_name not in self.brain_monologues:
            self.brain_monologues[brain_name] = {}
        
        self.brain_monologues[brain_name].update({
            "monologue": monologue,
            "actions": actions or [],
            "interactions": interactions or [],
            "tool_calls": tool_calls or [],
            "llm_thought": llm_thought
        })
        self.add_trace(f"已记录 {brain_name} 的脑内独白")
    
    def add_brain_reasoning(
        self,
        brain_name: str,
        reasoning: str,
        thought: str = "",
        input_refs: List[str] = None
    ) -> None:
        """
        添加脑的推理记录（简化接口）
        
        Args:
            brain_name: 脑名称
            reasoning: 推理说明
            thought: 思考过程
            input_refs: 输入引用列表
        """
        self.record_monologue(
            brain_name,
            monologue=thought,
            actions=[reasoning],
            interactions=input_refs or []
        )
    
    def add_decision_tension(
        self,
        conflict_desc: str,
        resolution: str,
        involved_brains: List[str] = None
    ) -> None:
        """
        添加决策冲突记录
        
        Args:
            conflict_desc: 冲突描述
            resolution: 解决方案
            involved_brains: 涉及的脑列表
        """
        self.decision_tension.append({
            "conflict": conflict_desc,
            "resolution": resolution,
            "involved_brains": involved_brains or []
        })
        self.add_trace(f"已记录决策冲突: {conflict_desc[:30]}...")
    
    def set_final_response(self, response_text: str) -> None:
        """设置最终回复"""
        self.final_response_text = response_text
    
    def to_debug_dict(self) -> Dict[str, Any]:
        """
        完整调试输出
        
        用于问题排查，包含所有字段。
        """
        return {
            "phase": self.phase,
            "user_input": self.user_input,
            "user_message_id": self.user_message_id,
            "emotional_state": str(self.emotional_state) if self.emotional_state else None,
            "recent_messages_count": len(self.recent_messages),
            "relevant_memories_count": len(self.relevant_memories),
            "world_state": self.get_world_summary(),
            "recent_events_count": len(self.recent_events),
            "nearby_npcs_count": len(self.nearby_npcs),
            "available_tools": self.available_tools,
            "world_content_items_count": len(self.world_content_items),
            "emotion_insight": self.emotion_insight.to_dict() if self.emotion_insight else None,
            "memory_decision": self.memory_decision.to_dict() if self.memory_decision else None,
            "world_brain_output": self.world_brain_output.to_dict() if self.world_brain_output else None,
            "npc_interaction_hint": self.npc_interaction_hint.to_dict() if self.npc_interaction_hint else None,
            "behavior_plan_v2": self.behavior_plan_v2.to_dict() if self.behavior_plan_v2 else None,
            "supervisor_decision": self.supervisor_decision.to_dict() if self.supervisor_decision else None,
            "fallback_decision": self.fallback_decision.to_dict() if self.fallback_decision else None,
            "executable_plan": self.executable_plan.to_dict() if self.executable_plan else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "final_response_text": self.final_response_text,
            "warnings": self.warnings,
            "trace": self.trace,
            "world_changes": self.world_changes
        }
    
    def get_location_name(self) -> str:
        """获取当前位置名称"""
        if self.world_state and hasattr(self.world_state, "location"):
            return getattr(self.world_state.location, "name", "")
        return ""
    
    def get_emotion_summary(self) -> Dict[str, Any]:
        """获取情绪摘要"""
        if not self.emotion_insight:
            return {}
        
        return {
            "primary_emotion": self.emotion_insight.primary_emotion,
            "valence": self.emotion_insight.valence,
            "arousal": self.emotion_insight.arousal,
            "support_need": self.emotion_insight.support_need
        }
    
    def get_world_summary(self) -> Dict[str, Any]:
        """获取世界摘要"""
        if not self.world_state:
            return {}
        
        return {
            "energy": getattr(self.world_state, "energy", 70.0),
            "hunger": getattr(self.world_state, "hunger", 0.0),
            "weather": getattr(self.world_state.weather, "value", "晴朗") if hasattr(self.world_state, "weather") else "晴朗",
            "location": self.get_location_name()
        }
    
    def get_debug_snapshot(self) -> Dict[str, Any]:
        """
        获取调试快照
        
        用于 CLI 和日志输出，包含关键状态标记。
        """
        return {
            "phase": self.phase,
            "user_input": self.user_input[:100] if self.user_input else "",
            "has_emotion_insight": self.has_emotion_insight,
            "has_supervisor_decision": self.has_supervisor_decision,
            "has_executable_plan": self.has_executable_plan,
            "has_execution_result": self.has_execution_result,
            "available_tools": self.available_tools,
            "world_content_count": len(self.world_content_items),
            "emotion_summary": self.get_emotion_summary(),
            "world_summary": self.get_world_summary(),
            "behavior_mode": self.behavior_plan_v2.mode if self.behavior_plan_v2 else None,
            "model_tier": self.supervisor_decision.final_model_tier if self.supervisor_decision else None,
            "execution_success": self.execution_result.success if self.execution_result else None,
            "execution_warnings": self.execution_result.warnings if self.execution_result else [],
            "execution_trace": self.execution_result.trace if self.execution_result else [],
            "world_changes_count": len(self.world_changes)
        }
    
    def get_brain_state_summary(self) -> Dict[str, Any]:
        """
        快速查看六脑是否已写回
        
        V7 新增方法：
        - 用于调试时快速判断哪些脑已执行并写回
        - 一眼看出链路是否通畅
        """
        return {
            "emotion": self.emotion_insight is not None,
            "memory": self.memory_decision is not None,
            "world": self.world_brain_output is not None,
            "npc": self.npc_interaction_hint is not None,
            "behavior": self.behavior_plan_v2 is not None,
            "supervisor": self.supervisor_decision is not None,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "phase": self.phase,
            "user_input": self.user_input,
            "user_message_id": self.user_message_id,
            "emotional_state": str(self.emotional_state) if self.emotional_state else None,
            "recent_messages_count": len(self.recent_messages),
            "relevant_memories_count": len(self.relevant_memories),
            "world_state": self.get_world_summary(),
            "recent_events_count": len(self.recent_events),
            "nearby_npcs_count": len(self.nearby_npcs),
            "available_tools": self.available_tools,
            "world_content_items_count": len(self.world_content_items),
            "has_emotion_insight": self.has_emotion_insight,
            "has_supervisor_decision": self.has_supervisor_decision,
            "has_executable_plan": self.has_executable_plan,
            "has_execution_result": self.has_execution_result,
            "emotion_insight": self.emotion_insight.to_dict() if self.emotion_insight else None,
            "memory_decision": self.memory_decision.to_dict() if self.memory_decision else None,
            "world_brain_output": self.world_brain_output.to_dict() if self.world_brain_output else None,
            "npc_interaction_hint": self.npc_interaction_hint.to_dict() if self.npc_interaction_hint else None,
            "behavior_plan_v2": self.behavior_plan_v2.to_dict() if self.behavior_plan_v2 else None,
            "supervisor_decision": self.supervisor_decision.to_dict() if self.supervisor_decision else None,
            "fallback_decision": self.fallback_decision.to_dict() if self.fallback_decision else None,
            "executable_plan": self.executable_plan.to_dict() if self.executable_plan else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "world_changes": self.world_changes
        }
