"""
视图模型定义

V9 可观测层核心：
- 定义统一的展示视图模型
- CLI/API/Web 都消费这些模型
- 不直接暴露业务对象

设计原则：
- 视图模型只包含展示需要的字段
- 所有字段都是简单类型（str/int/float/bool/list/dict）
- 提供默认值，避免 None 导致展示异常

V9 新增：
- MemoryCommitView: 记忆写入结果视图
- ProactiveTraceView: 主动交互结果视图
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class BrainTraceView:
    """
    单脑展示视图
    
    用于展示单个脑的结论卡片。
    
    V9 新增：
    - telemetry: 原始遥测数据
    - monologue: 脑内独白
    - actions: 具体工作列表
    - interactions: 脑间交互列表
    - tool_calls: 工具/API调用列表
    - llm_thought: LLM 原始推理
    """
    brain_name: str = ""
    display_name: str = ""
    triggered: bool = False
    conclusion: str = ""
    key_fields: Dict[str, Any] = field(default_factory=dict)
    influence_target: List[str] = field(default_factory=list)
    
    telemetry: Dict[str, Any] = field(default_factory=dict)
    
    monologue: str = ""
    actions: List[str] = field(default_factory=list)
    interactions: List[str] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    llm_thought: str = ""
    
    duration_ms: int = 0
    has_error: bool = False
    error_msg: str = ""


@dataclass
class ExecutionTraceView:
    """
    执行展示视图
    
    用于展示工具执行和 NPC 交互结果。
    """
    tools_executed: List[str] = field(default_factory=list)
    tools_failed: List[str] = field(default_factory=list)
    npc_interacted: bool = False
    npc_name: str = ""
    npc_mode: str = ""
    world_content_included: bool = False
    world_content_source: str = ""
    execution_mode: str = "respond_only"
    has_result: bool = False


@dataclass
class ReplyGateView:
    """
    回复门控视图
    
    用于展示最终回复生成时的门控决策。
    """
    world_content_allowed: bool = False
    world_content_reason: str = ""
    world_expand_allowed: bool = False
    world_expand_reason: str = ""
    npc_allowed: bool = False
    npc_reason: str = ""
    tool_result_included: bool = False
    final_style: str = "friendly"
    final_length: str = "medium"
    model_tier: str = "standard"
    fallback_triggered: bool = False
    fallback_reason: str = ""


@dataclass
class PlanDiffView:
    """
    计划对比视图
    
    用于展示 Behavior 原计划 vs Supervisor 裁决 vs 最终计划。
    """
    original_action: str = ""
    original_mode: str = ""
    original_world_expression: str = "suppressed"
    
    supervisor_overridden: bool = False
    override_action: str = ""
    override_world_expression: str = ""
    suppress_tool: bool = False
    suppress_npc: bool = False
    override_reason: str = ""
    
    final_action: str = ""
    final_mode: str = ""
    final_world_expression: str = "suppressed"
    
    candidate_actions: List[str] = field(default_factory=list)
    suppressed_actions: List[str] = field(default_factory=list)
    suppression_reasons: Dict[str, str] = field(default_factory=dict)


@dataclass
class DecisionChainView:
    """
    决策链视图
    
    用于展示因果链：为什么最终回复变成这样。
    """
    steps: List[Dict[str, str]] = field(default_factory=list)
    
    def add_step(self, source: str, effect: str, detail: str = "") -> None:
        self.steps.append({
            "source": source,
            "effect": effect,
            "detail": detail
        })


@dataclass
class MemoryCommitView:
    """
    V10: 记忆写入结果视图
    
    用于展示三层记忆的写入结果。
    """
    working_written: bool = False
    working_entry_count: int = 0
    working_token_count: int = 0
    
    episodic_written: bool = False
    episodic_entry_count: int = 0
    episodic_importance: float = 0.0
    episodic_emotional_impact: float = 0.0
    
    core_updated: bool = False
    core_update_type: str = ""
    core_update_key: str = ""
    
    consolidation_triggered: bool = False
    consolidation_to_episodic: int = 0
    consolidation_to_core: int = 0
    consolidation_forgotten: int = 0
    
    memory_summary: str = ""
    memory_decision_reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "working_written": self.working_written,
            "working_entry_count": self.working_entry_count,
            "working_token_count": self.working_token_count,
            "episodic_written": self.episodic_written,
            "episodic_entry_count": self.episodic_entry_count,
            "episodic_importance": self.episodic_importance,
            "episodic_emotional_impact": self.episodic_emotional_impact,
            "core_updated": self.core_updated,
            "core_update_type": self.core_update_type,
            "core_update_key": self.core_update_key,
            "consolidation_triggered": self.consolidation_triggered,
            "consolidation_to_episodic": self.consolidation_to_episodic,
            "consolidation_to_core": self.consolidation_to_core,
            "consolidation_forgotten": self.consolidation_forgotten,
            "memory_summary": self.memory_summary,
            "memory_decision_reasoning": self.memory_decision_reasoning
        }


@dataclass
class ProactiveTraceView:
    """
    V10: 主动交互结果视图
    
    用于展示主动交互的检查和触发结果。
    """
    checked: bool = False
    check_reason: str = ""
    
    candidate_generated: bool = False
    candidate_reason: str = ""
    candidate_type: str = ""
    candidate_priority: float = 0.0
    
    cooldown_blocked: bool = False
    cooldown_remaining_seconds: int = 0
    
    gate_passed: bool = False
    gate_reason: str = ""
    
    sent: bool = False
    sent_content: str = ""
    
    suppressed: bool = False
    suppressed_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "checked": self.checked,
            "check_reason": self.check_reason,
            "candidate_generated": self.candidate_generated,
            "candidate_reason": self.candidate_reason,
            "candidate_type": self.candidate_type,
            "candidate_priority": self.candidate_priority,
            "cooldown_blocked": self.cooldown_blocked,
            "cooldown_remaining_seconds": self.cooldown_remaining_seconds,
            "gate_passed": self.gate_passed,
            "gate_reason": self.gate_reason,
            "sent": self.sent,
            "sent_content": self.sent_content,
            "suppressed": self.suppressed,
            "suppressed_reason": self.suppressed_reason
        }


@dataclass
class DecisionTensionView:
    """
    V10: 决策冲突视图
    
    用于展示脑间的决策冲突和解决方案。
    """
    conflict: str = ""
    resolution: str = ""
    involved_brains: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict": self.conflict,
            "resolution": self.resolution,
            "involved_brains": self.involved_brains
        }


@dataclass
class TurnTraceView:
    """
    单轮完整展示视图
    
    这是展示层的顶层模型，包含一轮对话的所有展示信息。
    
    V9 新增：
    - memory_commit: 记忆写入结果视图
    - proactive: 主动交互结果视图
    """
    turn_id: str = ""
    phase: str = "initialized"
    
    user_input_summary: str = ""
    user_input_full: str = ""
    
    primary_intent: str = ""
    dominant_brain: str = ""
    final_action: str = ""
    
    has_world_content: bool = False
    has_npc: bool = False
    has_tool: bool = False
    
    model_tier: str = "standard"
    total_duration_ms: int = 0
    has_error: bool = False
    error_msg: str = ""
    
    timeline: List[str] = field(default_factory=list)
    timeline_durations: Dict[str, int] = field(default_factory=dict)
    
    brain_views: List[BrainTraceView] = field(default_factory=list)
    
    plan_diff: PlanDiffView = field(default_factory=PlanDiffView)
    
    execution_view: ExecutionTraceView = field(default_factory=ExecutionTraceView)
    
    reply_gate: ReplyGateView = field(default_factory=ReplyGateView)
    
    decision_chain: DecisionChainView = field(default_factory=DecisionChainView)
    
    memory_commit: MemoryCommitView = field(default_factory=MemoryCommitView)
    
    proactive: ProactiveTraceView = field(default_factory=ProactiveTraceView)
    
    decision_tensions: List[DecisionTensionView] = field(default_factory=list)
    
    final_response: str = ""
    response_source: str = ""
    
    warnings: List[str] = field(default_factory=list)
    
    def get_brain_view(self, brain_name: str) -> Optional[BrainTraceView]:
        for view in self.brain_views:
            if view.brain_name == brain_name:
                return view
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "phase": self.phase,
            "user_input_summary": self.user_input_summary,
            "primary_intent": self.primary_intent,
            "dominant_brain": self.dominant_brain,
            "final_action": self.final_action,
            "has_world_content": self.has_world_content,
            "has_npc": self.has_npc,
            "has_tool": self.has_tool,
            "model_tier": self.model_tier,
            "total_duration_ms": self.total_duration_ms,
            "has_error": self.has_error,
            "error_msg": self.error_msg,
            "timeline": self.timeline,
            "brain_views": [bv.__dict__ for bv in self.brain_views],
            "plan_diff": self.plan_diff.__dict__,
            "execution_view": self.execution_view.__dict__,
            "reply_gate": self.reply_gate.__dict__,
            "decision_chain": {"steps": self.decision_chain.steps},
            "memory_commit": self.memory_commit.to_dict(),
            "proactive": self.proactive.to_dict(),
            "decision_tensions": [dt.to_dict() for dt in self.decision_tensions],
            "final_response": self.final_response,
            "response_source": self.response_source,
            "warnings": self.warnings
        }
