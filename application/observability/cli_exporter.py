"""
CLI 输出器

V7 可观测层：
- 将 TurnTraceView 输出为 CLI 可读格式
- 支持详细模式和简洁模式
- 支持颜色高亮

设计原则：
- 只消费视图模型，不读业务对象
- 输出格式清晰易读
- 支持多种展示级别
"""

from typing import Any, Optional
from application.observability.trace_models import (
    TurnTraceView,
    BrainTraceView,
    PlanDiffView
)


class CLIExporter:
    """
    CLI 输出器
    
    将视图模型输出为终端可读格式。
    """
    
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m"
    }
    
    def __init__(self, use_color: bool = True, verbose: bool = False):
        self.use_color = use_color
        self.verbose = verbose
    
    def export(self, view: TurnTraceView) -> str:
        lines = []
        
        lines.append(self._build_overview_section(view))
        lines.append("")
        
        lines.append(self._build_timeline_section(view))
        lines.append("")
        
        lines.append(self._build_brain_cards_section(view))
        lines.append("")
        
        lines.append(self._build_decision_tension_section(view))
        lines.append("")
        
        lines.append(self._build_plan_diff_section(view))
        lines.append("")
        
        lines.append(self._build_execution_section(view))
        lines.append("")
        
        lines.append(self._build_reply_gate_section(view))
        lines.append("")
        
        lines.append(self._build_decision_chain_section(view))
        lines.append("")
        
        lines.append(self._build_final_response_section(view))
        
        if view.warnings:
            lines.append("")
            lines.append(self._build_warnings_section(view))
        
        return "\n".join(lines)
    
    def export_summary(self, view: TurnTraceView) -> str:
        lines = []
        
        lines.append(self._color("bold", "【本轮总览】"))
        lines.append(f"用户输入: {view.user_input_summary}")
        lines.append(f"主意图: {view.primary_intent}")
        lines.append(f"主导脑: {view.dominant_brain}")
        lines.append(f"最终动作: {view.final_action}")
        lines.append(f"世界内容: {'是' if view.has_world_content else '否'}")
        lines.append(f"NPC: {'是' if view.has_npc else '否'}")
        lines.append(f"工具: {'是' if view.has_tool else '否'}")
        lines.append(f"模型档位: {view.model_tier}")
        lines.append(f"状态: {'异常' if view.has_error else '正常'}")
        
        return "\n".join(lines)
    
    def _build_overview_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", self._color("cyan", "═" * 60)))
        lines.append(self._color("bold", self._color("cyan", "【本轮总览】")))
        lines.append(self._color("bold", self._color("cyan", "═" * 60)))
        lines.append(f"用户输入: {self._color("yellow", view.user_input_summary)}")
        lines.append(f"主意图: {view.primary_intent}")
        lines.append(f"主导脑: {self._color("green", view.dominant_brain)}")
        lines.append(f"最终动作: {self._color("magenta", view.final_action)}")
        lines.append(f"世界内容: {self._bool_str(view.has_world_content)}")
        lines.append(f"NPC: {self._bool_str(view.has_npc)}")
        lines.append(f"工具: {self._bool_str(view.has_tool)}")
        lines.append(f"模型档位: {view.model_tier}")
        lines.append(f"耗时: {view.total_duration_ms}ms")
        lines.append(f"状态: {self._status_str(view.has_error, view.error_msg)}")
        return "\n".join(lines)
    
    def _build_timeline_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【时间线】"))
        
        if not view.timeline:
            lines.append("  无时间线信息")
            return "\n".join(lines)
        
        timeline_str = " → ".join(view.timeline)
        lines.append(f"  {timeline_str}")
        
        return "\n".join(lines)
    
    def _build_brain_cards_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【六脑判断】"))
        
        for brain_view in view.brain_views:
            lines.append(self._build_brain_card(brain_view))
        
        return "\n".join(lines)
    
    def _build_brain_card(self, brain: BrainTraceView) -> str:
        lines = []
        
        status = self._color("green", "[Y]") if brain.triggered else self._color("dim", "[N]")
        name = self._color("bold", brain.display_name)
        
        lines.append(f"  {status} {name}")
        
        if brain.triggered:
            lines.append(f"      结论: {brain.conclusion}")
            
            if self.verbose and brain.key_fields:
                fields_str = " | ".join(f"{k}={v}" for k, v in brain.key_fields.items())
                lines.append(f"      字段: {fields_str}")
            
            if brain.influence_target:
                targets = ", ".join(brain.influence_target)
                lines.append(f"      影响: → {targets}")
            
            if brain.monologue:
                lines.append(f"      [脑内独白]: {brain.monologue}")
            
            if brain.actions:
                lines.append("      [具体工作]:")
                for action in brain.actions:
                    lines.append(f"        - {action}")
            
            if brain.interactions:
                lines.append("      [脑间交互]:")
                for interaction in brain.interactions:
                    lines.append(f"        - {interaction}")
            
            if brain.tool_calls:
                lines.append("      [工具/API调用]:")
                for tool in brain.tool_calls:
                    lines.append(f"        - {tool}")
            
            if brain.llm_thought:
                lines.append("      [LLM 原始推理]:")
                for tl in brain.llm_thought.strip().split("\n"):
                    if tl.strip():
                        lines.append(f"         {tl}")
            
            if brain.telemetry and self.verbose:
                lines.append("      [原始遥测数据]:")
                for k, v in brain.telemetry.items():
                    if isinstance(v, dict):
                        lines.append(f"        - {k}:")
                        for sub_k, sub_v in v.items():
                            lines.append(f"          └ {sub_k}: {sub_v}")
                    else:
                        lines.append(f"        - {k}: {v}")
        
        return "\n".join(lines)
    
    def _build_decision_tension_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【决策冲突与调和】"))
        
        if not view.decision_tensions:
            lines.append("  本轮无显著决策冲突。")
            return "\n".join(lines)
        
        for tension in view.decision_tensions:
            involved = ", ".join(tension.involved_brains) if tension.involved_brains else "未指定"
            lines.append(f"  [!] 冲突: {tension.conflict}")
            lines.append(f"      涉及大脑: {involved}")
            lines.append(f"  [R] 裁决: {tension.resolution}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_plan_diff_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【计划对比】"))
        
        diff = view.plan_diff
        
        lines.append(f"  原始动作: {diff.original_action}")
        lines.append(f"  原始世界表达: {diff.original_world_expression}")
        
        if diff.supervisor_overridden:
            lines.append(self._color("yellow", "  ─── 总控裁决 ───"))
            lines.append(f"  覆盖动作: {self._color("magenta", diff.override_action)}")
            if diff.override_world_expression:
                lines.append(f"  覆盖世界表达: {diff.override_world_expression}")
            lines.append(f"  抑制工具: {self._bool_str(diff.suppress_tool)}")
            lines.append(f"  抑制NPC: {self._bool_str(diff.suppress_npc)}")
            if diff.override_reason:
                lines.append(f"  理由: {diff.override_reason[:50]}...")
        
        lines.append(self._color("green", "  ─── 最终计划 ───"))
        lines.append(f"  最终动作: {self._color("green", diff.final_action)}")
        lines.append(f"  最终世界表达: {diff.final_world_expression}")
        
        if diff.suppressed_actions:
            lines.append("  被抑制的动作:")
            for action in diff.suppressed_actions:
                reason = diff.suppression_reasons.get(action, "")
                lines.append(f"    - {action}: {reason}")
        
        return "\n".join(lines)
    
    def _build_execution_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【执行结果】"))
        
        exec_view = view.execution_view
        
        lines.append(f"  执行模式: {exec_view.execution_mode}")
        
        if exec_view.tools_executed:
            tools_str = ", ".join(exec_view.tools_executed)
            lines.append(f"  执行工具: {tools_str}")
        
        if exec_view.tools_failed:
            failed_str = ", ".join(exec_view.tools_failed)
            lines.append(f"  失败工具: {self._color("red", failed_str)}")
        
        if exec_view.npc_interacted:
            lines.append(f"  NPC交互: {exec_view.npc_name} ({exec_view.npc_mode})")
        
        if exec_view.world_content_included:
            lines.append(f"  世界内容: 已包含")
        
        if not exec_view.has_result:
            lines.append("  无执行结果")
        
        return "\n".join(lines)
    
    def _build_reply_gate_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【回复门控】"))
        
        gate = view.reply_gate
        
        lines.append(f"  世界内容放行: {self._bool_str(gate.world_content_allowed)}")
        if gate.world_content_reason:
            lines.append(f"    原因: {gate.world_content_reason}")
        
        lines.append(f"  世界展开放行: {self._bool_str(gate.world_expand_allowed)}")
        
        lines.append(f"  NPC放行: {self._bool_str(gate.npc_allowed)}")
        if gate.npc_reason:
            lines.append(f"    原因: {gate.npc_reason}")
        
        lines.append(f"  工具结果包含: {self._bool_str(gate.tool_result_included)}")
        lines.append(f"  最终风格: {gate.final_style}")
        lines.append(f"  模型档位: {gate.model_tier}")
        
        if gate.fallback_triggered:
            lines.append(self._color("red", f"  降级触发: {gate.fallback_reason}"))
        
        return "\n".join(lines)
    
    def _build_decision_chain_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【决策链】"))
        
        chain = view.decision_chain
        
        if not chain.steps:
            lines.append("  无决策链信息")
            return "\n".join(lines)
        
        for i, step in enumerate(chain.steps):
            source = step.get("source", "")
            effect = step.get("effect", "")
            detail = step.get("detail", "")
            
            prefix = "  →" if i == 0 else "    →"
            lines.append(f"{prefix} {source}")
            lines.append(f"      └─ {effect}")
            if detail and self.verbose:
                lines.append(f"         ({detail})")
        
        return "\n".join(lines)
    
    def _build_final_response_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", "【最终回复】"))
        
        if view.final_response:
            response_preview = view.final_response[:200]
            if len(view.final_response) > 200:
                response_preview += "..."
            lines.append(f"  {response_preview}")
            lines.append(f"  (共 {len(view.final_response)} 字符)")
        else:
            lines.append("  无最终回复")
        
        return "\n".join(lines)
    
    def _build_warnings_section(self, view: TurnTraceView) -> str:
        lines = []
        lines.append(self._color("bold", self._color("red", "【警告】")))
        
        for warning in view.warnings:
            lines.append(f"  - {warning}")
        
        return "\n".join(lines)
    
    def _color(self, color_name: str, text: str) -> str:
        if not self.use_color:
            return text
        
        color_code = self.COLORS.get(color_name, "")
        reset = self.COLORS["reset"]
        
        if not color_code:
            return text
        
        return f"{color_code}{text}{reset}"
    
    def _bool_str(self, value: bool) -> str:
        if value:
            return self._color("green", "是")
        return self._color("dim", "否")
    
    def _status_str(self, has_error: bool, error_msg: str) -> str:
        if has_error:
            msg = error_msg[:30] if error_msg else "未知错误"
            return self._color("red", f"异常: {msg}")
        return self._color("green", "正常")
