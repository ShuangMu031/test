"""
提示词构建器

V9 核心组件：从 TurnContext 构建 prompt。

V9 改进：
- 支持三层记忆上下文
- 只吃"已整理好的 prompt 上下文"
- 新增 core/episodic/working memory section
- 支持世界快照上下文
- 支持记忆上下文参数
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    提示词构建器
    
    V9 改进：
    - 使用 build_from_turn_context() 方法
    - 所有 prompt block 都从 ctx 里取
    - 支持三层记忆上下文
    - 支持执行结果和总控裁决
    - 明确约束回复行为
    - 支持世界出场许可机制
    """
    
    STYLES = {
        "friendly": "你是一个温柔、体贴、善解人意的 AI 助手。",
        "empathetic": "你是一个富有同理心的倾听者，善于理解和共情。",
        "supportive": "你是一个支持性的伙伴，愿意提供帮助和鼓励。",
        "professional": "你是一个专业、高效的 AI 助手。"
    }
    
    def __init__(self, style: str = "friendly"):
        self.style = style
        self.system_prompt = self.STYLES.get(style, self.STYLES["friendly"])
    
    def build_from_turn_context(
        self,
        turn_context: Any,
        character_context: Optional[Dict[str, Any]] = None,
        include_execution_result: bool = False,
        include_supervisor_decision: bool = False,
        include_world_content: bool = False,
        expand_world_topic: bool = False,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """
        从 TurnContext 构建 prompt
        
        Args:
            turn_context: 轮次上下文
            character_context: 角色上下文
            include_execution_result: 是否包含执行结果
            include_supervisor_decision: 是否包含总控裁决
            include_world_content: 是否包含世界内容
            expand_world_topic: 是否展开世界话题
            memory_context: V10: 三层记忆上下文
            
        Returns:
            完整的 prompt
        """
        parts = []
        
        parts.append(self._build_system_section(character_context))
        
        parts.append(self._build_world_instruction(turn_context, include_world_content, expand_world_topic))
        
        if include_supervisor_decision:
            parts.append(self._build_supervisor_section(turn_context))
        
        parts.append(self._build_emotion_section(turn_context))
        
        parts.append(self._build_world_section(turn_context))
        
        parts.append(self._build_core_memory_section(turn_context, memory_context))
        
        parts.append(self._build_episodic_memory_section(turn_context, memory_context))
        
        parts.append(self._build_working_memory_section(turn_context, memory_context))
        
        parts.append(self._build_behavior_section(turn_context))
        
        if include_execution_result:
            parts.append(self._build_execution_section(turn_context))
        
        parts.append(self._build_world_content_section_v2(turn_context, include_world_content, expand_world_topic))
        
        parts.append(self._build_user_input_section(turn_context))
        
        parts.append(self._build_response_constraints(turn_context, include_execution_result))
        
        return "\n\n".join(parts)
    
    def _build_system_section(self, character_context: Optional[Dict[str, Any]]) -> str:
        """构建系统部分"""
        if character_context:
            name = character_context.get("name", "小雨")
            personality = character_context.get("personality", "温柔、体贴")
            return f"{self.system_prompt}\n\n你的名字是 {name}，性格特点是 {personality}。"
        return self.system_prompt
    
    def _build_supervisor_section(self, turn_context: Any) -> str:
        """构建总控裁决部分"""
        supervisor = turn_context.supervisor_decision
        if not supervisor:
            return ""
        
        lines = ["## 总控裁决"]
        
        if supervisor.conflict_detected:
            lines.append(f"- 检测到冲突: {supervisor.conflict_resolution}")
        
        if supervisor.override_action_type:
            lines.append(f"- 动作覆盖: {supervisor.override_action_type.value}")
        
        if supervisor.suppress_tool_execution:
            lines.append("- 抑制工具执行")
        
        if supervisor.suppress_npc:
            lines.append("- 抑制NPC交互")
        
        if len(lines) == 1:
            return ""
        
        return "\n".join(lines)
    
    def _build_emotion_section(self, turn_context: Any) -> str:
        """构建情绪部分"""
        emotion = turn_context.emotion_insight
        if not emotion:
            return "## 当前情绪\n情绪状态正常。"
        
        primary = getattr(emotion, "primary_emotion", "neutral")
        valence = getattr(emotion, "valence", 0.0)
        support_need = getattr(emotion, "support_need", "none")
        
        return f"""## 当前情绪
- 主要情绪: {primary}
- 愉悦度: {valence:.2f}
- 支持需求: {support_need}"""
    
    def _build_world_section(self, turn_context: Any) -> str:
        """构建世界部分"""
        world_state = turn_context.world_state
        if not world_state:
            return "## 当前环境\n环境状态正常。"
        
        energy = getattr(world_state, "energy", 70.0)
        hunger = getattr(world_state, "hunger", 0.0)
        weather = "晴朗"
        if hasattr(world_state, "weather") and world_state.weather:
            weather = getattr(world_state.weather, "value", "晴朗")
        
        location = turn_context.get_location_name() or "宿舍"
        
        return f"""## 当前环境
- 能量: {energy:.0f}%
- 饥饿: {hunger:.0f}%
- 天气: {weather}
- 位置: {location}"""
    
    def _build_core_memory_section(
        self,
        turn_context: Any,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """
        V10: 构建核心记忆部分
        
        从 memory_context 或 turn_context 获取核心记忆
        """
        core_memory_text = ""
        
        if memory_context:
            core_memory_text = memory_context.get("core_memory", "")
            persona = memory_context.get("persona", {})
            if persona and not core_memory_text:
                identity = persona.get("identity", "")
                relationships = persona.get("relationships", [])
                preferences = persona.get("preferences", [])
                
                lines = []
                if identity:
                    lines.append(f"- 身份: {identity}")
                if relationships:
                    for rel in relationships[:3]:
                        key = rel.get("key", "")
                        value = rel.get("value", "")
                        lines.append(f"- 关系 {key}: {value}")
                if preferences:
                    for pref in preferences[:3]:
                        key = pref.get("key", "")
                        value = pref.get("value", "")
                        lines.append(f"- 偏好 {key}: {value}")
                
                if lines:
                    core_memory_text = "\n".join(lines)
        
        if not core_memory_text:
            prompt_context = getattr(turn_context, "prompt_memory_context", {})
            if prompt_context:
                core_memory_text = prompt_context.get("core_memory", "")
        
        if not core_memory_text:
            return "## 核心记忆\n暂无核心记忆。"
        
        return f"## 核心记忆\n{core_memory_text}"
    
    def _build_episodic_memory_section(
        self,
        turn_context: Any,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """
        V10: 构建事件记忆部分
        
        从 memory_context 或 turn_context 获取事件记忆
        """
        episodic_memory_text = ""
        recent_events = []
        
        if memory_context:
            episodic_memory_text = memory_context.get("episodic_memory", "")
            recent_events = memory_context.get("recent_events", [])
        
        if not episodic_memory_text and not recent_events:
            prompt_context = getattr(turn_context, "prompt_memory_context", {})
            if prompt_context:
                episodic_memory_text = prompt_context.get("episodic_memory", "")
                recent_events = prompt_context.get("recent_events", [])
        
        if recent_events:
            lines = []
            for event in recent_events[:5]:
                if isinstance(event, dict):
                    desc = event.get("description", str(event))
                    time_str = event.get("timestamp", "")
                    if time_str:
                        lines.append(f"- [{time_str}] {desc}")
                    else:
                        lines.append(f"- {desc}")
                else:
                    lines.append(f"- {str(event)[:100]}")
            
            if lines:
                return "## 最近重要事件\n" + "\n".join(lines)
        
        if episodic_memory_text:
            return f"## 最近重要事件\n{episodic_memory_text}"
        
        return "## 最近重要事件\n暂无重要事件。"
    
    def _build_working_memory_section(
        self,
        turn_context: Any,
        memory_context: Dict[str, Any] = None
    ) -> str:
        """
        V10: 构建工作记忆部分
        
        从 memory_context 或 turn_context 获取工作记忆（对话历史）
        """
        working_memory_text = ""
        dialogue_history = []
        
        if memory_context:
            working_memory_text = memory_context.get("working_memory", "")
            dialogue_history = memory_context.get("dialogue_history", [])
        
        if not working_memory_text and not dialogue_history:
            prompt_context = getattr(turn_context, "prompt_memory_context", {})
            if prompt_context:
                working_memory_text = prompt_context.get("working_memory", "")
                dialogue_history = prompt_context.get("dialogue_history", [])
        
        if dialogue_history:
            lines = []
            for entry in dialogue_history[-10:]:
                if isinstance(entry, dict):
                    role = entry.get("role", "unknown")
                    content = entry.get("content", str(entry))
                    role_label = "用户" if role == "user" else "助手"
                    lines.append(f"{role_label}: {content[:100]}")
                else:
                    role = getattr(entry, "role", "unknown")
                    content = getattr(entry, "content", str(entry))
                    role_label = "用户" if role == "user" else "助手"
                    lines.append(f"{role_label}: {content[:100]}")
            
            if lines:
                return "## 最近对话\n" + "\n".join(lines)
        
        if working_memory_text:
            return f"## 最近对话\n{working_memory_text}"
        
        messages = getattr(turn_context, "recent_messages", [])
        if messages:
            lines = []
            for msg in messages[-5:]:
                role = getattr(msg, "role", "unknown")
                content = getattr(msg, "content", str(msg))[:100]
                role_label = "用户" if role == "human" or role == "user" else "助手"
                lines.append(f"{role_label}: {content}")
            
            if lines:
                return "## 最近对话\n" + "\n".join(lines)
        
        return "## 最近对话\n暂无最近对话。"
    
    def _build_behavior_section(self, turn_context: Any) -> str:
        """构建行为部分"""
        behavior = turn_context.behavior_plan_v2
        if not behavior:
            return "## 行为指导\n正常回复用户。"
        
        mode = getattr(behavior, "mode", "chat")
        style = getattr(behavior, "response_style", "friendly")
        length = getattr(behavior, "response_length", "medium")
        
        hints = []
        if mode == "comfort":
            hints.append("请给予用户情感支持和安慰")
        elif mode == "tool":
            hints.append("请根据工具结果回答用户问题")
        
        if style == "empathetic":
            hints.append("请使用富有同理心的语气")
        
        if length == "short":
            hints.append("请简短回复")
        elif length == "long":
            hints.append("请详细回复")
        
        hint_text = "\n".join(f"- {h}" for h in hints) if hints else "正常回复用户"
        return f"## 行为指导\n{hint_text}"
    
    def _build_execution_section(self, turn_context: Any) -> str:
        """构建执行结果部分"""
        execution = turn_context.execution_result
        if not execution:
            return ""
        
        lines = ["## 执行结果"]
        
        if execution.tool_results:
            for result in execution.tool_results:
                tool_name = result.tool_name
                if result.success:
                    lines.append(f"### {tool_name} 执行成功")
                    if result.data:
                        if isinstance(result.data, dict):
                            for key, value in result.data.items():
                                if isinstance(value, (str, int, float, bool)):
                                    lines.append(f"- {key}: {value}")
                                elif isinstance(value, list) and len(value) <= 5:
                                    lines.append(f"- {key}: {value}")
                        else:
                            lines.append(f"- 结果: {str(result.data)[:200]}")
                else:
                    lines.append(f"### {tool_name} 执行失败")
                    lines.append(f"- 错误: {result.error}")
        
        if execution.world_content_result:
            lines.append("### 世界内容")
            items = execution.world_content_result.get("items", [])
            for item in items[:3]:
                if isinstance(item, dict):
                    lines.append(f"- {item.get('abstract_content', str(item))[:100]}")
                else:
                    lines.append(f"- {str(item)[:100]}")
        
        if execution.error:
            lines.append(f"### 执行错误")
            lines.append(f"- {execution.error}")
        
        if len(lines) == 1:
            return ""
        
        return "\n".join(lines)
    
    def _build_user_input_section(self, turn_context: Any) -> str:
        """构建用户输入部分"""
        user_input = turn_context.user_input
        return f"## 用户输入\n{user_input}"
    
    def _build_response_constraints(self, turn_context: Any, include_execution_result: bool) -> str:
        """构建回复约束"""
        constraints = ["## 回复要求"]
        
        execution = turn_context.execution_result
        emotion = turn_context.emotion_insight
        supervisor = turn_context.supervisor_decision
        
        if include_execution_result and execution and execution.tool_results:
            if execution.has_tool_failures():
                constraints.append("- 工具执行失败，请明确告知用户并解释原因")
                constraints.append("- 不要编造工具结果")
            else:
                constraints.append("- 必须基于工具执行结果回复")
                constraints.append("- 不要编造工具没有返回的信息")
        
        if emotion and getattr(emotion, "support_need", "none") in ["high", "medium"]:
            constraints.append("- 用户需要情感支持，请先安抚再回答")
        
        if supervisor and supervisor.override_action_type:
            constraints.append(f"- 总控要求: 执行 {supervisor.override_action_type.value} 动作")
        
        constraints.append("- 请用自然、友好的语气回复")
        
        return "\n".join(constraints)
    
    def _build_world_instruction(
        self,
        turn_context: Any,
        include_world_content: bool,
        expand_world_topic: bool
    ) -> str:
        """
        构建世界表达规则指令
        
        根据模式决定什么时候能说、说到什么程度
        """
        mode = getattr(turn_context, "world_expression_mode", "suppressed")
        
        if not include_world_content or mode == "suppressed":
            return """## 世界表达规则
- 本轮不要主动引入虚拟世界新闻、事件、NPC动态、公告或传闻
- 不要因为系统里存在世界信息就主动展开
- 重点放在回应用户当前现实话题/情绪需求"""
        
        if mode == "light" and not expand_world_topic:
            return """## 世界表达规则
- 仅允许极轻微的环境氛围描写
- 不要引入新的世界事件、新闻、NPC动态
- 世界信息不能抢走回复主轴"""
        
        if mode == "contextual" and not expand_world_topic:
            return """## 世界表达规则
- 只有在与用户当前话题直接相关时，才可提及少量世界信息
- 不要主动展开成新的世界剧情
- 世界信息应服务当前话题，而不是转移话题"""
        
        return """## 世界表达规则
- 用户已主动提及世界事件/新闻/NPC/地点/某些事情，允许顺势展开
- 优先围绕用户提到的那个点展开，不要把所有世界素材一股脑倒出来
- 先回答用户最关心的内容，再补充相关世界信息"""
    
    def _build_world_content_section_v2(
        self,
        turn_context: Any,
        include_world_content: bool,
        expand_world_topic: bool
    ) -> str:
        """
        构建世界内容部分（分层）
        
        根据 mode 和 expand_world_topic 决定塞什么内容
        """
        if not include_world_content:
            return ""
        
        mode = getattr(turn_context, "world_expression_mode", "suppressed")
        
        if mode == "light" and not expand_world_topic:
            return self._build_light_world_hint(turn_context)
        
        if mode == "contextual" and not expand_world_topic:
            return self._build_contextual_world_hint(turn_context)
        
        if expand_world_topic or mode == "active":
            return self._build_active_world_bundle(turn_context)
        
        return ""
    
    def _build_light_world_hint(self, turn_context: Any) -> str:
        """
        轻量环境摘要
        
        用于 light 模式，只允许一句环境氛围
        """
        world_state = getattr(turn_context, "world_state", None)
        if not world_state:
            return ""

        location = getattr(world_state, "current_location", "") or getattr(world_state, "location", "")
        tod = getattr(world_state, "time_of_day", "") or getattr(world_state, "time_phase", "")
        weather = getattr(world_state, "weather", "")

        lines = []
        if location:
            lines.append(f"- 当前位置: {location}")
        if tod:
            lines.append(f"- 时间: {tod}")
        if weather:
            lines.append(f"- 天气: {weather}")

        if not lines:
            return ""

        return "## 可用于轻微环境陪伴的世界背景\n" + "\n".join(lines)
    
    def _build_contextual_world_hint(self, turn_context: Any) -> str:
        """
        上下文世界摘要
        
        用于 contextual 模式，只在话题相关时提
        """
        lines = []

        world_state = getattr(turn_context, "world_state", None)
        if world_state:
            location = getattr(world_state, "current_location", "") or getattr(world_state, "location", "")
            if location:
                lines.append(f"- 当前地点: {location}")

        world_items = getattr(turn_context, "world_content_items", None) or []
        for item in world_items[:2]:
            title = getattr(item, "title", None) or str(item)
            lines.append(f"- 相关世界内容: {title}")

        recent_events = getattr(turn_context, "recent_events", None) or []
        for evt in recent_events[:2]:
            title = getattr(evt, "title", None) or str(evt)
            lines.append(f"- 相关事件: {title}")

        if not lines:
            return ""

        return "## 仅在与当前话题直接相关时可引用的世界信息\n" + "\n".join(lines)
    
    def _build_active_world_bundle(self, turn_context: Any) -> str:
        """
        主动展开世界摘要
        
        用于 active 模式或用户明确提到时，允许展开世界内容
        """
        lines = []

        world_snapshot = getattr(turn_context, "world_snapshot", None)
        if world_snapshot:
            lines.append("## 世界快照")
            lines.append(f"- 时间: {getattr(world_snapshot, 'world_time', 'N/A')}")
            lines.append(f"- 天气: {getattr(world_snapshot, 'weather', 'N/A')}")
            lines.append(f"- 地点: {getattr(world_snapshot, 'location', 'N/A')}")

        world_items = getattr(turn_context, "world_content_items", None) or []
        if world_items:
            lines.append("## 世界内容")
            for item in world_items[:5]:
                title = getattr(item, "title", None) or str(item)
                summary = getattr(item, "summary", None) or getattr(item, "content", None) or ""
                if summary:
                    lines.append(f"- {title}: {summary}")
                else:
                    lines.append(f"- {title}")

        recent_events = getattr(turn_context, "recent_events", None) or []
        recent_world_events = getattr(turn_context, "recent_world_events", None) or []
        
        if recent_world_events:
            lines.append("## 最近世界事件")
            for evt in recent_world_events[:5]:
                if isinstance(evt, dict):
                    desc = evt.get("description", str(evt))
                    lines.append(f"- {desc}")
                else:
                    title = getattr(evt, "title", None) or str(evt)
                    summary = getattr(evt, "summary", None) or ""
                    if summary:
                        lines.append(f"- {title}: {summary}")
                    else:
                        lines.append(f"- {title}")
        elif recent_events:
            lines.append("## 最近事件")
            for evt in recent_events[:5]:
                title = getattr(evt, "title", None) or str(evt)
                summary = getattr(evt, "summary", None) or ""
                if summary:
                    lines.append(f"- {title}: {summary}")
                else:
                    lines.append(f"- {title}")

        if not lines:
            return ""

        return "\n".join(lines)
    
    def build(
        self,
        user_input: str,
        recent_messages: List = None,
        relevant_memories: List = None,
        emotional_state: Any = None,
        world_state: Any = None,
        memory_context: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        兼容旧接口的构建方法
        
        不推荐使用，建议使用 build_from_turn_context()
        """
        from application.orchestration.turn_context import TurnContext
        
        ctx = TurnContext()
        ctx.user_input = user_input
        ctx.recent_messages = recent_messages or []
        ctx.relevant_memories = relevant_memories or []
        ctx.emotional_state = emotional_state
        ctx.world_state = world_state
        
        if memory_context:
            ctx.set_prompt_memory_context(memory_context)
        
        return self.build_from_turn_context(
            ctx, 
            kwargs.get("character_context"),
            memory_context=memory_context
        )
