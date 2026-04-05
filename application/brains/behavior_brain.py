"""
行为脑

V7 核心组件：唯一战术决策器。

V7 改进（基于修改意见第2次整改）：
1. 真正消费世界脑/NPC脑/事件/世界内容信息
2. 把"收集到"变成"真的参与决策"
3. LLM 优先输出结构化计划
4. Parse 层解析 LLM 输出
5. Normalizer 层标准化字段（使用 ActionType）
6. Sanitize 层语义修正
7. Fallback 简化为最小安全计划
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import json

from application.contracts.action_types import ActionType
from application.contracts.behavior import ActionPlanV2
from .base import BaseBrain

logger = logging.getLogger(__name__)

VALID_MODES = {"chat", "comfort", "tool", "task", "npc", "mixed"}
VALID_STYLES = {"friendly", "empathetic", "supportive", "professional", "gentle"}
VALID_LENGTHS = {"short", "medium", "long"}

ACTION_STRING_TO_TYPE = {
    "respond": ActionType.RESPOND,
    "ask": ActionType.RESPOND,
    "comfort": ActionType.COMFORT,
    "use_tool": ActionType.TOOL_USE,
    "shift_scene": ActionType.EXPLORE,
    "rest": ActionType.REST,
    "eat": ActionType.EAT,
    "socialize": ActionType.SOCIALIZE,
    "learn": ActionType.LEARN,
    "world_content_read": ActionType.WORLD_CONTENT_READ,
}


class ActionPlanParser:
    """
    行为计划解析器
    
    职责：
    1. 解析 LLM 原始输出
    2. 提取 JSON 结构
    3. 处理格式错误
    """
    
    def parse(self, response: str) -> Optional[Dict[str, Any]]:
        """解析 LLM 响应"""
        try:
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            return None


class ActionPlanNormalizer:
    """
    行为计划标准化器
    
    职责：
    1. 把 LLM 输出标准化
    2. 缺字段补默认
    3. 不合法值替换
    4. 格式保证
    5. 字符串动作映射为 ActionType
    """
    
    def normalize(self, plan_data: Dict[str, Any]) -> ActionPlanV2:
        """标准化行为计划"""
        mode = self._normalize_mode(plan_data.get("mode"))
        primary_action = self._normalize_action(plan_data.get("primary_action"), mode)
        
        return ActionPlanV2(
            mode=mode,
            primary_action=primary_action,
            execution_mode=self._normalize_execution_mode(plan_data.get("execution_mode"), mode),
            priority=self._normalize_priority(plan_data.get("priority")),
            confidence=self._normalize_confidence(plan_data.get("confidence")),
            tool_plan=self._normalize_tool_plan(plan_data.get("tool_plan")),
            response_style=self._normalize_style(plan_data.get("response_style")),
            response_length=self._normalize_length(plan_data.get("response_length")),
            ask_followup=bool(plan_data.get("ask_followup", False)),
            followup_goal=str(plan_data.get("followup_goal", "")),
            world_commit_needed=bool(plan_data.get("world_commit_needed", False)),
            memory_commit_needed=bool(plan_data.get("memory_commit_needed", False)),
            requires_tool_result=bool(plan_data.get("requires_tool_result", False)),
            safety_flags=self._normalize_safety_flags(plan_data.get("safety_flags")),
            world_expression_mode=self._normalize_world_expression_mode(plan_data.get("world_expression_mode")),
            reasoning=str(plan_data.get("reasoning", ""))
        )
    
    def _normalize_mode(self, mode: Any) -> str:
        if mode in VALID_MODES:
            return str(mode)
        return "chat"
    
    def _normalize_action(self, action: Any, mode: str) -> ActionType:
        if isinstance(action, ActionType):
            return action
        
        if isinstance(action, str) and action in ACTION_STRING_TO_TYPE:
            return ACTION_STRING_TO_TYPE[action]
        
        mode_to_action = {
            "chat": ActionType.RESPOND,
            "comfort": ActionType.COMFORT,
            "tool": ActionType.TOOL_USE,
            "npc": ActionType.RESPOND,
            "task": ActionType.RESPOND,
            "mixed": ActionType.RESPOND
        }
        return mode_to_action.get(mode, ActionType.RESPOND)
    
    def _normalize_execution_mode(self, exec_mode: Any, mode: str) -> str:
        valid_modes = {"respond_only", "tool_first", "mixed"}
        if exec_mode in valid_modes:
            return str(exec_mode)
        
        if mode == "tool":
            return "tool_first"
        return "respond_only"
    
    def _normalize_priority(self, priority: Any) -> int:
        if isinstance(priority, int) and 1 <= priority <= 10:
            return priority
        return 5
    
    def _normalize_confidence(self, confidence: Any) -> float:
        if isinstance(confidence, (int, float)) and 0 <= confidence <= 1:
            return float(confidence)
        return 0.5
    
    def _normalize_tool_plan(self, tool_plan: Any) -> List[Dict[str, Any]]:
        if not isinstance(tool_plan, list):
            return []
        
        normalized = []
        for item in tool_plan:
            if isinstance(item, dict):
                normalized.append({
                    "tool_name": str(item.get("tool_name", "")),
                    "args": item.get("args", {}) if isinstance(item.get("args"), dict) else {}
                })
        return normalized
    
    def _normalize_style(self, style: Any) -> str:
        if style in VALID_STYLES:
            return str(style)
        return "friendly"
    
    def _normalize_length(self, length: Any) -> str:
        if length in VALID_LENGTHS:
            return str(length)
        return "medium"
    
    def _normalize_safety_flags(self, flags: Any) -> List[str]:
        if not isinstance(flags, list):
            return []
        return [str(f) for f in flags if isinstance(f, str)]
    
    def _normalize_world_expression_mode(self, mode: Any) -> str:
        """标准化世界表达级别"""
        valid_modes = {"suppressed", "light", "contextual", "active"}
        if isinstance(mode, str) and mode in valid_modes:
            return mode
        return "suppressed"


class ActionPlanSanitizer:
    """
    行为计划语义修正器
    
    职责：
    1. 结合上下文做语义修正
    2. 空 tool_plan 降级
    3. 高支持需求时 style 温和化
    4. 低 confidence 时关闭 followup
    5. V10: 高支持需求/comfort动作时压制世界表达
    """
    
    def sanitize(self, plan: ActionPlanV2, context: Any) -> ActionPlanV2:
        """语义修正"""
        plan = self._sanitize_empty_tool_plan(plan)
        plan = self._sanitize_style_for_support_need(plan, context)
        plan = self._sanitize_followup_for_confidence(plan)
        plan = self._sanitize_world_expression_mode(plan, context)
        return plan
    
    def _sanitize_empty_tool_plan(self, plan: ActionPlanV2) -> ActionPlanV2:
        """空 tool_plan 降级"""
        if plan.mode == "tool" and not plan.tool_plan:
            plan.mode = "chat"
            plan.primary_action = ActionType.RESPOND
            plan.execution_mode = "respond_only"
            plan.reasoning = f"{plan.reasoning} [Sanitized: 空 tool_plan 降级为 chat]"
            logger.debug("空 tool_plan 降级为 chat")
        
        if plan.primary_action == ActionType.TOOL_USE and not plan.tool_plan:
            plan.primary_action = ActionType.RESPOND
            plan.reasoning = f"{plan.reasoning} [Sanitized: TOOL_USE 无工具降级为 RESPOND]"
            logger.debug("TOOL_USE 无工具降级为 RESPOND")
        
        return plan
    
    def _sanitize_style_for_support_need(self, plan: ActionPlanV2, context: Any) -> ActionPlanV2:
        """高支持需求时 style 温和化"""
        emotion_insight = getattr(context, "emotion_insight", None)
        if not emotion_insight:
            return plan
        
        support_need = getattr(emotion_insight, "support_need", "none")
        
        if support_need == "high" and plan.response_style == "professional":
            plan.response_style = "empathetic"
            plan.reasoning = f"{plan.reasoning} [Sanitized: 高支持需求时 style 改为 empathetic]"
            logger.debug("高支持需求时 style 改为 empathetic")
        
        return plan
    
    def _sanitize_followup_for_confidence(self, plan: ActionPlanV2) -> ActionPlanV2:
        """低 confidence 时关闭 followup"""
        if plan.confidence < 0.3 and plan.ask_followup:
            plan.ask_followup = False
            plan.followup_goal = ""
            plan.reasoning = f"{plan.reasoning} [Sanitized: 低 confidence 关闭 followup]"
            logger.debug("低 confidence 关闭 followup")
        
        return plan
    
    def _sanitize_world_expression_mode(self, plan: ActionPlanV2, context: Any) -> ActionPlanV2:
        """
        V10: 高支持需求/comfort动作时压制世界表达
        
        规则：
        - 高支持需求时，强制 suppressed
        - comfort 动作时，强制 suppressed
        """
        emotion_insight = getattr(context, "emotion_insight", None)
        support_need = getattr(emotion_insight, "support_need", "none") if emotion_insight else "none"
        
        primary_action_value = plan.primary_action.value.lower() if plan.primary_action else ""
        
        if support_need == "high":
            plan.world_expression_mode = "suppressed"
            plan.reasoning = f"{plan.reasoning} [Sanitized: 高支持需求压制世界表达]"
            logger.debug("高支持需求压制世界表达为 suppressed")
        
        if primary_action_value == "comfort":
            plan.world_expression_mode = "suppressed"
            plan.reasoning = f"{plan.reasoning} [Sanitized: comfort动作压制世界表达]"
            logger.debug("comfort动作压制世界表达为 suppressed")
        
        return plan


BEHAVIOR_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": list(VALID_MODES)},
        "primary_action": {"type": "string"},
        "execution_mode": {"type": "string"},
        "priority": {"type": "integer", "minimum": 1, "maximum": 10},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "tool_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string"},
                    "args": {"type": "object"}
                }
            }
        },
        "response_style": {"type": "string", "enum": list(VALID_STYLES)},
        "response_length": {"type": "string", "enum": list(VALID_LENGTHS)},
        "ask_followup": {"type": "boolean"},
        "followup_goal": {"type": "string"},
        "world_commit_needed": {"type": "boolean"},
        "memory_commit_needed": {"type": "boolean"},
        "reasoning": {"type": "string"}
    },
    "required": ["mode", "primary_action"]
}


class BehaviorBrain(BaseBrain):
    """
    行为脑
    
    V7 唯一战术决策器。
    
    V7 改进：
    - 真正消费世界脑/NPC脑/事件/世界内容信息
    - 把"收集到"变成"真的参与决策"
    
    处理流程：
    1. Parse: 解析 LLM 输出
    2. Normalize: 标准化字段（使用 ActionType）
    3. Sanitize: 语义修正
    4. Fallback: 最小安全计划
    
    职责：
    1. 确定行为模式
    2. 规划工具调用
    3. 设置回复风格
    4. 输出完整执行计划
    """
    
    def __init__(self, llm=None, decision_engine=None):
        self.llm = llm
        self.decision_engine = decision_engine
        self.parser = ActionPlanParser()
        self.normalizer = ActionPlanNormalizer()
        self.sanitizer = ActionPlanSanitizer()
    
    @property
    def name(self) -> str:
        return "behavior"
    
    async def process(self, context: Any) -> ActionPlanV2:
        """处理行为"""
        user_input = context.user_input
        emotion_insight = context.emotion_insight
        available_tools = context.available_tools
        
        world_brain_output = getattr(context, "world_brain_output", None)
        npc_hint = getattr(context, "npc_interaction_hint", None)
        recent_events = getattr(context, "recent_events", []) or []
        world_content_items = getattr(context, "world_content_items", []) or []
        nearby_npcs = getattr(context, "nearby_npcs", []) or []
        
        if self.llm:
            try:
                plan = await self._llm_decide(context)
                if plan:
                    context.record_telemetry(
                        "behavior",
                        mode=plan.mode,
                        primary_action=plan.primary_action.value if plan.primary_action else "unknown",
                        execution_mode=plan.execution_mode,
                        priority=plan.priority,
                        confidence=plan.confidence,
                        world_expression_mode=plan.world_expression_mode
                    )
                    
                    actions = []
                    interactions = []
                    
                    actions.append(f"行为模式: {plan.mode}")
                    actions.append(f"主要动作: {plan.primary_action.value if plan.primary_action else 'unknown'}")
                    
                    if plan.tool_plan:
                        actions.append(f"工具计划: {len(plan.tool_plan)} 个工具")
                        for tp in plan.tool_plan:
                            interactions.append(f"→ tool: {tp.get('tool_name', 'unknown')}")
                    
                    if emotion_insight:
                        interactions.append("← emotion_insight")
                    if world_brain_output:
                        interactions.append("← world_brain_output")
                    if npc_hint:
                        interactions.append("← npc_interaction_hint")
                    
                    context.record_monologue(
                        "behavior",
                        monologue=f"综合判断后决定: {plan.mode} 模式, {plan.primary_action.value if plan.primary_action else 'unknown'} 动作, 置信度 {plan.confidence:.2f}",
                        actions=actions,
                        interactions=interactions
                    )
                    
                    return plan
            except Exception as e:
                logger.warning(f"LLM 行为决策失败，使用 fallback: {e}")
        
        fallback_plan = self._fallback_decide(emotion_insight)
        
        context.record_telemetry(
            "behavior",
            mode=fallback_plan.mode,
            primary_action=fallback_plan.primary_action.value if fallback_plan.primary_action else "unknown",
            execution_mode=fallback_plan.execution_mode,
            priority=fallback_plan.priority,
            confidence=fallback_plan.confidence,
            world_expression_mode=fallback_plan.world_expression_mode
        )
        
        context.record_monologue(
            "behavior",
            monologue=f"使用 fallback 最小安全计划: {fallback_plan.mode} 模式",
            actions=[f"行为模式: {fallback_plan.mode}", f"主要动作: {fallback_plan.primary_action.value if fallback_plan.primary_action else 'unknown'}"],
            interactions=[]
        )
        
        return fallback_plan
    
    async def _llm_decide(self, context: Any) -> Optional[ActionPlanV2]:
        """LLM 结构化决策：parse → normalize → sanitize"""
        prompt = self._build_decision_prompt(context)
        
        try:
            response = await self.llm.generate(prompt)
            
            plan_data = self.parser.parse(response)
            
            if plan_data:
                plan = self.normalizer.normalize(plan_data)
                plan = self.sanitizer.sanitize(plan, context)
                return plan
        except Exception as e:
            logger.error(f"LLM 决策解析失败: {e}")
        
        return None
    
    def _build_decision_prompt(self, context: Any) -> str:
        """
        构建决策提示
        
        V7 改进：
        - 真正消费世界脑/NPC脑/事件/世界内容信息
        - 把这些信息纳入决策 prompt
        """
        emotion_summary = "无明显情绪信息"
        if context.emotion_insight:
            emotion_summary = f"""
情绪脑输出：
- 主情绪: {getattr(context.emotion_insight, 'primary_emotion', 'unknown')}
- valence: {getattr(context.emotion_insight, 'valence', 0.0)}
- arousal: {getattr(context.emotion_insight, 'arousal', 0.0)}
- support_need: {getattr(context.emotion_insight, 'support_need', 'none')}
"""
        
        world_brain_output = getattr(context, "world_brain_output", None)
        world_brain_summary = "无世界脑输出"
        if world_brain_output:
            world_update = getattr(world_brain_output, "world_update_proposal", None)
            world_content = getattr(world_brain_output, "world_content_proposal", None)

            parts = ["世界脑输出："]

            parts.append(
                f"- should_apply_update: {getattr(world_brain_output, 'should_apply_update', False)}"
            )
            parts.append(
                f"- should_read_world_content: {getattr(world_brain_output, 'should_read_world_content', False)}"
            )

            if world_update:
                parts.append(
                    f"- time_advance_minutes: {getattr(world_update, 'time_advance_minutes', 0)}"
                )
                parts.append(
                    f"- suggested_location: {getattr(world_update, 'suggested_location', '')}"
                )
                parts.append(
                    f"- npc_context_hint: {getattr(world_update, 'npc_context_hint', '')}"
                )
                parts.append(
                    f"- world_commit_needed: {getattr(world_update, 'world_commit_needed', False)}"
                )

            if world_content:
                parts.append(
                    f"- user_is_asking_world_content: {getattr(world_content, 'user_is_asking_world_content', False)}"
                )
                parts.append(
                    f"- content_types_needed: {getattr(world_content, 'content_types_needed', [])}"
                )
                parts.append(
                    f"- retrieval_query: {getattr(world_content, 'retrieval_query', '')}"
                )

            world_brain_summary = "\n".join(parts)
        
        npc_hint = getattr(context, "npc_interaction_hint", None)
        npc_summary = "无NPC脑输出"
        if npc_hint:
            npc_summary = f"""
NPC脑输出：
- should_involve_npc: {getattr(npc_hint, 'should_involve_npc', False)}
- npc_id: {getattr(npc_hint, 'npc_id', '')}
- intervention_type: {getattr(npc_hint, 'intervention_type', '')}
- dialogue_hint: {getattr(npc_hint, 'dialogue_hint', '')}
"""
        
        recent_events = getattr(context, "recent_events", None)
        recent_events_summary = "无最近事件"
        if recent_events:
            lines = []
            for evt in recent_events[:3]:
                title = getattr(evt, "title", None) or str(evt)
                lines.append(f"- {title}")
            recent_events_summary = "最近世界事件：\n" + "\n".join(lines)
        
        world_content_items = getattr(context, "world_content_items", None)
        world_content_summary = "无当前世界内容"
        if world_content_items:
            lines = []
            for item in world_content_items[:3]:
                title = getattr(item, "title", None) or str(item)
                lines.append(f"- {title}")
            world_content_summary = "当前世界内容：\n" + "\n".join(lines)
        
        nearby_npcs = getattr(context, "nearby_npcs", None)
        nearby_npcs_summary = "无附近NPC"
        if nearby_npcs:
            lines = []
            for npc in nearby_npcs[:3]:
                npc_name = getattr(npc, "name", None) or getattr(npc, "npc_id", None) or str(npc)
                lines.append(f"- {npc_name}")
            nearby_npcs_summary = "附近NPC：\n" + "\n".join(lines)
        
        tools_str = ", ".join(context.available_tools) if context.available_tools else "无"
        
        return f"""你是行为决策脑，负责根据当前轮上下文生成本轮行为计划。

用户输入：
{context.user_input}

{emotion_summary}

{world_brain_summary}

{npc_summary}

{recent_events_summary}

{world_content_summary}

{nearby_npcs_summary}

可用工具：
{tools_str}

请综合判断：
1. 本轮主要动作是什么（回复 / 安慰 / 工具 / 读取世界内容 / NPC介入）
2. 是否需要优先安抚情绪
3. 是否需要引入NPC
4. 是否需要读取世界内容
5. 回复风格和长度应该是什么
6. 是否需要追问

请额外判断本轮"世界信息表达级别" world_expression_mode，只能是以下四个值之一：
- suppressed: 用户当前主要在进行情感倾诉、现实求助、现实聊天，此时不要主动带出虚拟世界信息
- light: 允许非常轻微的环境氛围描写，但不能引入新世界事件、新闻或NPC动态
- contextual: 只有当用户当前话题直接涉及地点、NPC、世界状态时，才允许提及相关世界信息
- active: 用户明确在询问世界新闻、事件、NPC、地点、剧情推进时，允许主动展开世界内容

重要：如果用户本轮核心需求是被理解、被安慰、被支持，优先使用 suppressed。

请输出 JSON 格式的行为计划，包含以下字段：
- mode: 行为模式 (chat/comfort/tool/task/npc/mixed)
- primary_action: 主要动作 (respond/comfort/use_tool/shift_scene/world_content_read)
- execution_mode: 执行模式 (respond_only/tool_first/mixed)
- priority: 优先级 (1-10)
- confidence: 置信度 (0-1)
- tool_plan: 工具调用计划 (数组，每项包含 tool_name 和 args)
- response_style: 回复风格 (friendly/empathetic/supportive/professional/gentle)
- response_length: 回复长度 (short/medium/long)
- ask_followup: 是否追问 (true/false)
- followup_goal: 追问目标
- world_commit_needed: 是否需要世界更新 (true/false)
- memory_commit_needed: 是否需要记忆存储 (true/false)
- world_expression_mode: 世界表达级别 (suppressed/light/contextual/active)
- reasoning: 决策理由

只输出 JSON，不要其他内容。"""
    
    def _fallback_decide(self, emotion_insight: Any) -> ActionPlanV2:
        """
        Fallback 最小安全计划
        
        V7 简化：只返回最小安全回复计划
        - 不做工具调用
        - 不做世界更新
        - 只做简单回复
        """
        support_need = getattr(emotion_insight, "support_need", "none") if emotion_insight else "none"
        
        if support_need == "high":
            return ActionPlanV2(
                mode="comfort",
                primary_action=ActionType.COMFORT,
                execution_mode="respond_only",
                priority=8,
                confidence=0.3,
                tool_plan=[],
                response_style="gentle",
                response_length="short",
                ask_followup=False,
                followup_goal="",
                world_commit_needed=False,
                memory_commit_needed=False,
                requires_tool_result=False,
                safety_flags=[],
                reasoning="fallback: 高支持需求最小安全计划"
            )
        
        return ActionPlanV2(
            mode="chat",
            primary_action=ActionType.RESPOND,
            execution_mode="respond_only",
            priority=5,
            confidence=0.3,
            tool_plan=[],
            response_style="friendly",
            response_length="short",
            ask_followup=False,
            followup_goal="",
            world_commit_needed=False,
            memory_commit_needed=False,
            requires_tool_result=False,
            safety_flags=[],
            reasoning="fallback: 无效 LLM 行为输出的最小安全计划"
        )
