"""
视图构建器

V9 可观测层核心：
- 从 TurnContext 构建 TurnTraceView
- 不直接暴露业务对象细节
- 只提取展示需要的字段

设计原则：
- 每个脑一个构建方法
- 决策链自动推导
- 计划对比自动计算

V9 新增：
- MemoryCommitView 构建
- ProactiveTraceView 构建
"""

from typing import Any, Optional, List
import logging

from application.observability.trace_models import (
    TurnTraceView,
    BrainTraceView,
    ExecutionTraceView,
    ReplyGateView,
    PlanDiffView,
    DecisionChainView,
    MemoryCommitView,
    ProactiveTraceView,
    DecisionTensionView
)

logger = logging.getLogger(__name__)


class TraceBuilder:
    """
    视图构建器
    
    从 TurnContext 构建展示视图。
    只读取字段，不修改业务状态。
    """
    
    BRAIN_DISPLAY_NAMES = {
        "emotion": "情绪脑",
        "memory": "记忆脑",
        "world": "世界脑",
        "npc": "NPC脑",
        "behavior": "行为脑",
        "supervisor": "总控脑"
    }
    
    BRAIN_ORDER = ["emotion", "memory", "world", "npc", "behavior", "supervisor"]
    
    def build(self, turn_context: Any) -> TurnTraceView:
        """
        从 TurnContext 构建完整视图
        """
        view = TurnTraceView()
        
        view.turn_id = getattr(turn_context, "user_message_id", "") or "unknown"
        view.phase = getattr(turn_context, "phase", "initialized")
        
        self._brain_monologue_data = getattr(turn_context, "brain_monologues", {}) or {}
        self._brain_telemetry_data = getattr(turn_context, "brain_telemetry", {}) or {}
        
        self._build_user_input_view(turn_context, view)
        
        self._build_brain_views(turn_context, view)
        
        self._build_decision_tension_view(turn_context, view)
        
        self._build_plan_diff_view(turn_context, view)
        
        self._build_execution_view(turn_context, view)
        
        self._build_reply_gate_view(turn_context, view)
        
        self._build_memory_commit_view(turn_context, view)
        
        self._build_proactive_trace_view(turn_context, view)
        
        self._build_decision_chain(turn_context, view)
        
        self._build_summary(turn_context, view)
        
        self._build_timeline(turn_context, view)
        
        view.warnings = list(getattr(turn_context, "warnings", []) or [])
        
        return view
    
    def _build_user_input_view(self, turn_context: Any, view: TurnTraceView) -> None:
        user_input = getattr(turn_context, "user_input", "") or ""
        view.user_input_full = user_input
        view.user_input_summary = user_input[:50] + "..." if len(user_input) > 50 else user_input
    
    def _build_brain_views(self, turn_context: Any, view: TurnTraceView) -> None:
        brain_builders = {
            "emotion": self._build_emotion_brain_view,
            "memory": self._build_memory_brain_view,
            "world": self._build_world_brain_view,
            "npc": self._build_npc_brain_view,
            "behavior": self._build_behavior_brain_view,
            "supervisor": self._build_supervisor_brain_view
        }
        
        for brain_name in self.BRAIN_ORDER:
            builder = brain_builders.get(brain_name)
            if builder:
                brain_view = builder(turn_context)
                
                monologue_info = self._brain_monologue_data.get(brain_name, {})
                if monologue_info:
                    brain_view.monologue = monologue_info.get("monologue", "")
                    brain_view.actions = list(monologue_info.get("actions", []))
                    brain_view.interactions = list(monologue_info.get("interactions", []))
                    brain_view.tool_calls = list(monologue_info.get("tool_calls", []))
                    brain_view.llm_thought = monologue_info.get("llm_thought", "")
                
                telemetry_info = self._brain_telemetry_data.get(brain_name, {})
                if telemetry_info:
                    brain_view.telemetry = dict(telemetry_info)
                
                view.brain_views.append(brain_view)
    
    def _build_emotion_brain_view(self, turn_context: Any) -> BrainTraceView:
        view = BrainTraceView(
            brain_name="emotion",
            display_name=self.BRAIN_DISPLAY_NAMES["emotion"]
        )
        
        insight = getattr(turn_context, "emotion_insight", None)
        if not insight:
            view.triggered = False
            view.conclusion = "未触发情绪分析"
            return view
        
        view.triggered = True
        
        primary_emotion = getattr(insight, "primary_emotion", "neutral")
        valence = getattr(insight, "valence", 0.0)
        arousal = getattr(insight, "arousal", 0.5)
        support_need = getattr(insight, "support_need", "none")
        reasoning = getattr(insight, "reasoning", "")
        
        view.key_fields = {
            "primary_emotion": primary_emotion,
            "valence": round(valence, 2),
            "arousal": round(arousal, 2),
            "support_need": support_need
        }
        
        if support_need in ["high", "medium"]:
            view.conclusion = f"主情绪: {primary_emotion}，支持需求: {support_need}，应优先提供情感支持"
            view.influence_target = ["behavior", "supervisor"]
        else:
            view.conclusion = f"主情绪: {primary_emotion}，情绪稳定，可正常对话"
        
        return view
    
    def _build_memory_brain_view(self, turn_context: Any) -> BrainTraceView:
        view = BrainTraceView(
            brain_name="memory",
            display_name=self.BRAIN_DISPLAY_NAMES["memory"]
        )
        
        decision = getattr(turn_context, "memory_decision", None)
        memories = getattr(turn_context, "relevant_memories", []) or []
        
        if not decision and not memories:
            view.triggered = False
            view.conclusion = "未触发记忆检索"
            return view
        
        view.triggered = True
        
        memory_count = len(memories)
        used_count = 0
        if decision:
            used_count = getattr(decision, "memories_used", 0) or memory_count
        
        view.key_fields = {
            "retrieved_count": memory_count,
            "used_count": used_count
        }
        
        if memory_count > 0:
            view.conclusion = f"检索到 {memory_count} 条记忆，采用 {used_count} 条"
        else:
            view.conclusion = "无相关记忆"
        
        return view
    
    def _build_world_brain_view(self, turn_context: Any) -> BrainTraceView:
        view = BrainTraceView(
            brain_name="world",
            display_name=self.BRAIN_DISPLAY_NAMES["world"]
        )
        
        output = getattr(turn_context, "world_brain_output", None)
        if not output:
            view.triggered = False
            view.conclusion = "未触发世界判断"
            return view
        
        view.triggered = True
        
        should_expand = False
        should_update = False
        reason = ""
        
        content_proposal = getattr(output, "world_content_proposal", None)
        if content_proposal:
            should_expand = getattr(content_proposal, "user_is_asking_world_content", False)
        
        update_proposal = getattr(output, "world_update_proposal", None)
        if update_proposal:
            should_update = getattr(update_proposal, "world_commit_needed", False)
            reason = getattr(update_proposal, "reasoning", "")
        
        view.key_fields = {
            "should_expand_world": should_expand,
            "should_update_world": should_update,
            "reasoning": reason[:100] if reason else ""
        }
        
        world_mode = getattr(turn_context, "world_expression_mode", "suppressed")
        
        if world_mode == "suppressed":
            view.conclusion = "世界表达被压制（当前为情感支持/现实帮助场景）"
        elif should_expand:
            view.conclusion = "用户提及世界要素，允许展开世界内容"
            view.influence_target = ["behavior", "reply"]
        elif should_update:
            view.conclusion = "建议推进世界状态"
            view.influence_target = ["post_commit"]
        else:
            view.conclusion = "世界脑已触发，但本轮不需要主动展开世界内容"
        
        return view
    
    def _build_npc_brain_view(self, turn_context: Any) -> BrainTraceView:
        view = BrainTraceView(
            brain_name="npc",
            display_name=self.BRAIN_DISPLAY_NAMES["npc"]
        )
        
        hint = getattr(turn_context, "npc_interaction_hint", None)
        nearby_npcs = getattr(turn_context, "nearby_npcs", []) or []
        
        if not hint and not nearby_npcs:
            view.triggered = False
            view.conclusion = "未触发 NPC 判断"
            return view
        
        view.triggered = True
        
        npc_name = ""
        npc_mode = "none"
        should_interact = False
        
        if hint:
            npc_name = getattr(hint, "target_npc", "") or getattr(hint, "npc_name", "")
            npc_mode = getattr(hint, "interaction_mode", "none")
            should_interact = npc_mode not in ["none", "background"]
        
        view.key_fields = {
            "nearby_npc_count": len(nearby_npcs),
            "target_npc": npc_name,
            "interaction_mode": npc_mode,
            "should_interact": should_interact
        }
        
        if should_interact:
            view.conclusion = f"建议与 {npc_name} 进行 {npc_mode} 交互"
            view.influence_target = ["behavior", "execution"]
        else:
            view.conclusion = "本轮不需要 NPC 介入"
        
        return view
    
    def _build_behavior_brain_view(self, turn_context: Any) -> BrainTraceView:
        view = BrainTraceView(
            brain_name="behavior",
            display_name=self.BRAIN_DISPLAY_NAMES["behavior"]
        )
        
        plan = getattr(turn_context, "behavior_plan_v2", None)
        if not plan:
            view.triggered = False
            view.conclusion = "未生成行为计划"
            return view
        
        view.triggered = True
        
        primary_action = getattr(plan, "primary_action", None)
        action_str = primary_action.value if hasattr(primary_action, "value") else str(primary_action)
        
        mode = getattr(plan, "mode", "chat")
        world_expr = getattr(plan, "world_expression_mode", "suppressed")
        ask_followup = getattr(plan, "ask_followup", False)
        tool_plan = getattr(plan, "tool_plan", []) or []
        reasoning = getattr(plan, "reasoning", "")
        
        view.key_fields = {
            "primary_action": action_str,
            "mode": mode,
            "world_expression_mode": world_expr,
            "ask_followup": ask_followup,
            "tool_count": len(tool_plan)
        }
        
        view.conclusion = f"原始动作: {action_str}，世界表达: {world_expr}"
        view.influence_target = ["supervisor", "execution"]
        
        return view
    
    def _build_supervisor_brain_view(self, turn_context: Any) -> BrainTraceView:
        view = BrainTraceView(
            brain_name="supervisor",
            display_name=self.BRAIN_DISPLAY_NAMES["supervisor"]
        )
        
        decision = getattr(turn_context, "supervisor_decision", None)
        if not decision:
            view.triggered = False
            view.conclusion = "未触发总控裁决"
            return view
        
        view.triggered = True
        
        conflict_detected = getattr(decision, "conflict_detected", False)
        override_action = getattr(decision, "override_action_type", None)
        override_action_str = override_action.value if hasattr(override_action, "value") else str(override_action) if override_action else ""
        
        suppress_tool = getattr(decision, "suppress_tool_execution", False)
        suppress_npc = getattr(decision, "suppress_npc", False)
        override_world = getattr(decision, "override_world_expression_mode", None)
        reasoning = getattr(decision, "reasoning", "")
        
        view.key_fields = {
            "conflict_detected": conflict_detected,
            "override_action": override_action_str,
            "suppress_tool": suppress_tool,
            "suppress_npc": suppress_npc,
            "override_world_expression": override_world or ""
        }
        
        if conflict_detected or override_action or suppress_tool or suppress_npc:
            override_parts = []
            if override_action:
                override_parts.append(f"动作改为 {override_action_str}")
            if suppress_tool:
                override_parts.append("抑制工具执行")
            if suppress_npc:
                override_parts.append("抑制 NPC")
            if override_world:
                override_parts.append(f"世界表达改为 {override_world}")
            
            view.conclusion = "裁决: " + "，".join(override_parts)
            view.influence_target = ["execution", "reply"]
        else:
            view.conclusion = "认可行为计划，无需干预"
        
        return view
    
    def _build_plan_diff_view(self, turn_context: Any, view: TurnTraceView) -> None:
        plan = getattr(turn_context, "behavior_plan_v2", None)
        supervisor = getattr(turn_context, "supervisor_decision", None)
        
        diff = PlanDiffView()
        
        if plan:
            primary_action = getattr(plan, "primary_action", None)
            diff.original_action = primary_action.value if hasattr(primary_action, "value") else str(primary_action)
            diff.original_mode = getattr(plan, "mode", "chat")
            diff.original_world_expression = getattr(plan, "world_expression_mode", "suppressed")
        
        if supervisor:
            override_action = getattr(supervisor, "override_action_type", None)
            if override_action:
                diff.supervisor_overridden = True
                diff.override_action = override_action.value if hasattr(override_action, "value") else str(override_action)
                diff.override_reason = getattr(supervisor, "reasoning", "")
            
            diff.suppress_tool = getattr(supervisor, "suppress_tool_execution", False)
            diff.suppress_npc = getattr(supervisor, "suppress_npc", False)
            
            override_world = getattr(supervisor, "override_world_expression_mode", None)
            if override_world:
                diff.override_world_expression = override_world
        
        if diff.supervisor_overridden:
            diff.final_action = diff.override_action or diff.original_action
            diff.final_world_expression = diff.override_world_expression or diff.original_world_expression
        else:
            diff.final_action = diff.original_action
            diff.final_world_expression = diff.original_world_expression
        
        diff.final_mode = diff.original_mode
        
        self._build_suppressed_actions(turn_context, diff)
        
        view.plan_diff = diff
    
    def _build_suppressed_actions(self, turn_context: Any, diff: PlanDiffView) -> None:
        emotion = getattr(turn_context, "emotion_insight", None)
        supervisor = getattr(turn_context, "supervisor_decision", None)
        plan = getattr(turn_context, "behavior_plan_v2", None)
        
        diff.candidate_actions = ["respond", "comfort", "ask_followup", "tool_use", "world_expand", "npc_interact"]
        
        support_need = "none"
        if emotion:
            support_need = getattr(emotion, "support_need", "none")
        
        if support_need in ["high", "medium"]:
            diff.suppressed_actions.append("tool_use")
            diff.suppression_reasons["tool_use"] = "高支持需求场景，避免信息负担"
            diff.suppressed_actions.append("world_expand")
            diff.suppression_reasons["world_expand"] = "高支持需求场景，避免话题漂移"
        
        if supervisor:
            if getattr(supervisor, "suppress_tool_execution", False):
                if "tool_use" not in diff.suppressed_actions:
                    diff.suppressed_actions.append("tool_use")
                diff.suppression_reasons["tool_use"] = "总控抑制工具执行"
            
            if getattr(supervisor, "suppress_npc", False):
                diff.suppressed_actions.append("npc_interact")
                diff.suppression_reasons["npc_interact"] = "总控抑制 NPC 交互"
        
        world_mode = getattr(turn_context, "world_expression_mode", "suppressed")
        if world_mode == "suppressed" and "world_expand" not in diff.suppressed_actions:
            diff.suppressed_actions.append("world_expand")
            diff.suppression_reasons["world_expand"] = "世界表达模式为 suppressed"
    
    def _build_execution_view(self, turn_context: Any, view: TurnTraceView) -> None:
        exec_view = ExecutionTraceView()
        
        execution_result = getattr(turn_context, "execution_result", None)
        executable_plan = getattr(turn_context, "executable_plan", None)
        
        if executable_plan:
            exec_view.execution_mode = getattr(executable_plan, "execution_mode", "respond_only")
        
        if execution_result:
            exec_view.has_result = True
            
            tool_results = getattr(execution_result, "tool_results", None)
            if tool_results:
                if isinstance(tool_results, dict):
                    exec_view.tools_executed = list(tool_results.keys())
                elif isinstance(tool_results, list):
                    for tr in tool_results:
                        if isinstance(tr, dict):
                            tool_name = tr.get("tool_name", tr.get("name", "unknown"))
                            exec_view.tools_executed.append(tool_name)
            
            failed_tools = execution_result.get_failed_tools() if hasattr(execution_result, "get_failed_tools") else []
            if failed_tools:
                exec_view.tools_failed = failed_tools
            
            npc_result = getattr(execution_result, "npc_result", None)
            if npc_result:
                exec_view.npc_interacted = True
                exec_view.npc_name = getattr(npc_result, "npc_name", "")
                exec_view.npc_mode = getattr(npc_result, "mode", "")
            
            world_result = getattr(execution_result, "world_content_result", None)
            if world_result:
                exec_view.world_content_included = True
        
        view.execution_view = exec_view
    
    def _build_reply_gate_view(self, turn_context: Any, view: TurnTraceView) -> None:
        gate_view = ReplyGateView()
        
        world_mode = getattr(turn_context, "world_expression_mode", "suppressed")
        gate_view.world_content_allowed = world_mode != "suppressed"
        
        if world_mode == "suppressed":
            gate_view.world_content_reason = "世界表达模式为 suppressed"
        elif world_mode == "light":
            gate_view.world_content_reason = "仅允许轻微环境氛围"
        elif world_mode == "contextual":
            gate_view.world_content_reason = "仅在与话题相关时可引用"
        else:
            gate_view.world_content_reason = "允许展开世界内容"
            gate_view.world_expand_allowed = True
        
        supervisor = getattr(turn_context, "supervisor_decision", None)
        if supervisor:
            gate_view.model_tier = getattr(supervisor, "final_model_tier", "standard")
            gate_view.npc_allowed = not getattr(supervisor, "suppress_npc", False)
            if not gate_view.npc_allowed:
                gate_view.npc_reason = "总控抑制 NPC 交互"
        
        plan = getattr(turn_context, "behavior_plan_v2", None)
        if plan:
            gate_view.final_style = getattr(plan, "response_style", "friendly")
            gate_view.final_length = getattr(plan, "response_length", "medium")
        
        fallback = getattr(turn_context, "fallback_decision", None)
        if fallback:
            gate_view.fallback_triggered = True
            gate_view.fallback_reason = getattr(fallback, "reason", "")
        
        execution_result = getattr(turn_context, "execution_result", None)
        if execution_result and getattr(execution_result, "tool_results", None):
            gate_view.tool_result_included = True
        
        view.reply_gate = gate_view
    
    def _build_decision_tension_view(self, turn_context: Any, view: TurnTraceView) -> None:
        """
        构建决策冲突视图
        
        V9 新增：展示脑间的决策冲突和解决方案
        """
        tensions = getattr(turn_context, "decision_tension", []) or []
        
        for t in tensions:
            tension_view = DecisionTensionView(
                conflict=t.get("conflict", ""),
                resolution=t.get("resolution", ""),
                involved_brains=t.get("involved_brains", [])
            )
            view.decision_tensions.append(tension_view)
    
    def _build_decision_chain(self, turn_context: Any, view: TurnTraceView) -> None:
        chain = DecisionChainView()
        
        emotion = getattr(turn_context, "emotion_insight", None)
        if emotion:
            support_need = getattr(emotion, "support_need", "none")
            if support_need in ["high", "medium"]:
                chain.add_step(
                    source="emotion.support_need",
                    effect="标记高支持需求",
                    detail=f"support_need={support_need}"
                )
        
        supervisor = getattr(turn_context, "supervisor_decision", None)
        if supervisor:
            override_action = getattr(supervisor, "override_action_type", None)
            if override_action:
                action_str = override_action.value if hasattr(override_action, "value") else str(override_action)
                chain.add_step(
                    source="supervisor.override",
                    effect=f"动作改为 {action_str}",
                    detail=getattr(supervisor, "reasoning", "")
                )
            
            if getattr(supervisor, "suppress_tool_execution", False):
                chain.add_step(
                    source="supervisor.suppress_tool",
                    effect="抑制工具执行",
                    detail=""
                )
            
            if getattr(supervisor, "suppress_npc", False):
                chain.add_step(
                    source="supervisor.suppress_npc",
                    effect="抑制 NPC 交互",
                    detail=""
                )
        
        world_mode = getattr(turn_context, "world_expression_mode", "suppressed")
        if world_mode == "suppressed":
            chain.add_step(
                source="world_expression_mode",
                effect="压制世界内容",
                detail="当前场景不适合展开世界设定"
            )
        elif world_mode == "active":
            chain.add_step(
                source="world_expression_mode",
                effect="允许世界内容展开",
                detail="用户主动提及世界要素"
            )
        
        final_response = getattr(turn_context, "final_response_text", "")
        if final_response:
            chain.add_step(
                source="reply_composer",
                effect="生成最终回复",
                detail=f"长度 {len(final_response)} 字符"
            )
        
        view.decision_chain = chain
    
    def _build_summary(self, turn_context: Any, view: TurnTraceView) -> None:
        emotion = getattr(turn_context, "emotion_insight", None)
        if emotion:
            support_need = getattr(emotion, "support_need", "none")
            if support_need in ["high", "medium"]:
                view.primary_intent = "情感支持"
            else:
                view.primary_intent = "正常对话"
        else:
            view.primary_intent = "未知"
        
        dominant_brains = []
        for brain_view in view.brain_views:
            if brain_view.triggered and brain_view.influence_target:
                dominant_brains.append(brain_view.display_name)
        
        if dominant_brains:
            view.dominant_brain = " + ".join(dominant_brains[:2])
        else:
            view.dominant_brain = "行为脑"
        
        view.final_action = view.plan_diff.final_action
        
        view.has_world_content = view.execution_view.world_content_included
        view.has_npc = view.execution_view.npc_interacted
        view.has_tool = len(view.execution_view.tools_executed) > 0
        
        view.model_tier = view.reply_gate.model_tier
        
        view.final_response = getattr(turn_context, "final_response_text", "")
        view.response_source = "llm" if view.final_response else "none"
        
        if view.warnings:
            view.has_error = True
            view.error_msg = view.warnings[-1] if view.warnings else ""
    
    def _build_timeline(self, turn_context: Any, view: TurnTraceView) -> None:
        phase = getattr(turn_context, "phase", "initialized")
        
        phase_order = [
            "initialized",
            "context_collected",
            "brains_completed",
            "policy_checked",
            "plan_compiled",
            "executed",
            "responded",
            "committed"
        ]
        
        try:
            current_idx = phase_order.index(phase)
            view.timeline = phase_order[:current_idx + 1]
        except ValueError:
            view.timeline = [phase]
        
        trace = getattr(turn_context, "trace", []) or []
        for item in trace:
            if isinstance(item, dict) and "phase" in item:
                duration = item.get("duration_ms", 0)
                if duration:
                    view.timeline_durations[item["phase"]] = duration
    
    def _build_memory_commit_view(self, turn_context: Any, view: TurnTraceView) -> None:
        """
        V10: 构建记忆提交视图
        """
        memory_view = MemoryCommitView()
        
        memory_decision = getattr(turn_context, "memory_decision", None)
        if memory_decision:
            memory_view.working_written = getattr(memory_decision, "write_working", False)
            memory_view.episodic_written = getattr(memory_decision, "write_episodic", False)
            memory_view.core_updated = getattr(memory_decision, "write_core", False)
            memory_view.episodic_importance = getattr(memory_decision, "importance", 0.0)
            memory_view.episodic_emotional_impact = getattr(memory_decision, "emotional_impact", 0.0)
            memory_view.memory_decision_reasoning = getattr(memory_decision, "reasoning", "")
        
        memory_writes = getattr(turn_context, "memory_writes", [])
        if memory_writes:
            for write in memory_writes:
                layer = write.get("layer", "")
                if layer == "working":
                    memory_view.working_written = True
                    memory_view.working_entry_count += 1
                elif layer == "episodic":
                    memory_view.episodic_written = True
                    memory_view.episodic_entry_count += 1
                elif layer == "core":
                    memory_view.core_updated = True
                    memory_view.core_update_type = write.get("update_type", "")
                    memory_view.core_update_key = write.get("key", "")
        
        consolidation_service = getattr(turn_context, "consolidation_result", None)
        if consolidation_service:
            memory_view.consolidation_triggered = True
            memory_view.consolidation_to_episodic = getattr(consolidation_service, "to_episodic", 0)
            memory_view.consolidation_to_core = getattr(consolidation_service, "to_core", 0)
            memory_view.consolidation_forgotten = getattr(consolidation_service, "forgotten", 0)
        
        parts = []
        if memory_view.working_written:
            parts.append(f"工作记忆: {memory_view.working_entry_count} 条")
        if memory_view.episodic_written:
            parts.append(f"事件记忆: {memory_view.episodic_entry_count} 条")
        if memory_view.core_updated:
            parts.append(f"核心记忆: {memory_view.core_update_type}")
        if memory_view.consolidation_triggered:
            parts.append(f"巩固: E{memory_view.consolidation_to_episodic}/C{memory_view.consolidation_to_core}/F{memory_view.consolidation_forgotten}")
        
        if parts:
            memory_view.memory_summary = " | ".join(parts)
        else:
            memory_view.memory_summary = "无记忆写入"
        
        view.memory_commit = memory_view
    
    def _build_proactive_trace_view(self, turn_context: Any, view: TurnTraceView) -> None:
        """
        V10: 构建主动交互视图
        """
        proactive_view = ProactiveTraceView()
        
        proactive_decision = getattr(turn_context, "proactive_decision", None)
        if proactive_decision:
            proactive_view.checked = True
            proactive_view.check_reason = "主链检查主动交互"
            
            should_send = getattr(proactive_decision, "should_send", False)
            if should_send:
                proactive_view.candidate_generated = True
                proactive_view.candidate_reason = getattr(proactive_decision, "reason", "")
                
                trigger_type = getattr(proactive_decision, "trigger_type", None)
                if trigger_type:
                    proactive_view.candidate_type = trigger_type.value if hasattr(trigger_type, "value") else str(trigger_type)
                
                proactive_view.candidate_priority = getattr(proactive_decision, "priority", 0.0)
                
                cooldown = getattr(proactive_decision, "cooldown_seconds", 0)
                if cooldown > 0:
                    proactive_view.cooldown_blocked = True
                    proactive_view.cooldown_remaining_seconds = cooldown
                
                proactive_view.gate_passed = True
                proactive_view.gate_reason = "通过主动交互门控"
                
                proactive_view.sent = True
                proactive_view.sent_content = getattr(proactive_decision, "suggested_content", "")
            else:
                proactive_view.suppressed = True
                proactive_view.suppressed_reason = getattr(proactive_decision, "reason", "条件不满足")
        
        view.proactive = proactive_view
