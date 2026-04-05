"""
Prompt 块生成器

定义各个 prompt block 的生成函数。
"""

from typing import Any, Dict, List, Optional

from application.prompting.limits import (
    MAX_MESSAGE_LENGTH,
    MAX_MEMORY_LENGTH,
    MAX_DIALOGUE_HISTORY,
    MAX_MEMORY_COUNT,
    MAX_NPC_COUNT
)
from application.prompting.templates import build_system_template, get_action_guidance


def truncate_content(content: str, max_length: int) -> str:
    """
    截断内容到最大长度
    
    Args:
        content: 原始内容
        max_length: 最大长度
        
    Returns:
        截断后的内容
    """
    if len(content) <= max_length:
        return content
    return content[:max_length - 3] + "..."


def build_system_block(
    character_context: Dict[str, Any],
    world_state: Any,
    emotional_state: Any
) -> str:
    """
    构建系统提示部分
    
    Args:
        character_context: 角色上下文
        world_state: 虚拟世界状态
        emotional_state: 情绪状态
        
    Returns:
        系统提示文本
    """
    name = character_context.get('name', 'Agent')
    personality = character_context.get('personality', '友好、乐于助人')
    backstory = character_context.get('backstory', '')
    
    valence = emotional_state.valence if emotional_state else 0.0
    arousal = emotional_state.arousal if emotional_state else 0.0
    dominant_emotion = emotional_state.get_dominant_emotion() if emotional_state else None
    emotion_str = dominant_emotion[0].value if dominant_emotion else "neutral"
    emotion_strength = dominant_emotion[1] if dominant_emotion else 0
    
    time_str = f"{world_state.time.hour:02d}:{world_state.time.minute:02d}" if world_state else "00:00"
    weather_str = world_state.weather.value if world_state else "晴朗"
    location_str = world_state.location.name if world_state else "未知"
    activity_str = world_state.activity.value if world_state else "休息"
    
    return build_system_template(
        name=name,
        personality=personality,
        backstory=backstory,
        time_str=time_str,
        location_str=location_str,
        weather_str=weather_str,
        activity_str=activity_str,
        emotion_str=emotion_str,
        emotion_strength=emotion_strength,
        valence=valence,
        arousal=arousal
    )


def build_decision_block(decision: Any) -> str:
    """
    构建决策建议块
    
    Args:
        decision: 决策结果
        
    Returns:
        决策建议文本
    """
    if not decision:
        return ""
    
    action_type = decision.action_type.value if hasattr(decision, 'action_type') else "respond"
    reasoning = decision.reasoning if hasattr(decision, 'reasoning') else ""
    confidence = decision.confidence if hasattr(decision, 'confidence') else 0.0
    
    guidance = get_action_guidance(action_type)
    
    return f"""
行为决策建议:
- 建议行为: {action_type}
- 决策理由: {reasoning}
- 置信度: {confidence:.2f}
- 回复指导: {guidance}"""


def build_tool_observations_block(tool_observations: Optional[List[str]]) -> str:
    """
    构建工具观察结果块
    
    Args:
        tool_observations: 工具调用观察结果
        
    Returns:
        工具观察结果文本
    """
    if not tool_observations:
        return ""
    
    lines = ["\n工具调用结果:"]
    for obs in tool_observations:
        lines.append(f"- {obs}")
    
    return "\n".join(lines)


def build_execution_status_block(execution_result: Optional[Dict[str, Any]]) -> str:
    """
    构建执行状态块
    
    Args:
        execution_result: 执行结果
        
    Returns:
        执行状态文本
    """
    if not execution_result:
        return ""
    
    success = execution_result.get("success", True)
    action_type = execution_result.get("action_type", "respond")
    error = execution_result.get("error")
    failure_stage = execution_result.get("failure_stage")
    executed_steps = execution_result.get("executed_steps", [])
    
    lines = ["\n执行状态:"]
    lines.append(f"- 动作: {action_type}")
    lines.append(f"- 是否成功: {'是' if success else '否'}")
    
    if not success:
        if failure_stage:
            lines.append(f"- 失败阶段: {failure_stage}")
        if error:
            lines.append(f"- 失败原因: {error}")
    
    if executed_steps:
        lines.append("- 执行步骤:")
        for step in executed_steps:
            lines.append(f"  - {step}")
    
    return "\n".join(lines)


def build_world_change_block(execution_result: Optional[Dict[str, Any]]) -> str:
    """
    构建世界变化块
    
    Args:
        execution_result: 执行结果
        
    Returns:
        世界变化文本
    """
    if not execution_result:
        return ""
    
    world_before = execution_result.get("world_before")
    world_after = execution_result.get("world_after")
    
    if not world_before or not world_after:
        return ""
    
    changes = []
    
    if world_before.get("location") != world_after.get("location"):
        changes.append(f"- 位置: {world_before.get('location', '未知')} -> {world_after.get('location', '未知')}")
    
    if world_before.get("energy") != world_after.get("energy"):
        changes.append(f"- 能量: {world_before.get('energy', 0)} -> {world_after.get('energy', 0)}")
    
    if world_before.get("hunger") != world_after.get("hunger"):
        changes.append(f"- 饥饿: {world_before.get('hunger', 0)} -> {world_after.get('hunger', 0)}")
    
    if not changes:
        return ""
    
    return "\n世界变化:\n" + "\n".join(changes)


def build_response_hints_block(response_hints: Optional[List[str]]) -> str:
    """
    构建回复提示块
    
    Args:
        response_hints: 回复提示列表
        
    Returns:
        回复提示文本
    """
    if not response_hints:
        return ""
    
    return "\n回复提示: " + "、".join(response_hints)


def build_npc_block(nearby_npcs: Optional[List[Any]]) -> str:
    """
    构建附近NPC块
    
    Args:
        nearby_npcs: 附近的NPC列表
        
    Returns:
        NPC信息文本
    """
    if not nearby_npcs:
        return ""
    
    lines = ["\n附近的人:"]
    for npc in nearby_npcs[:MAX_NPC_COUNT]:
        name = npc.name if hasattr(npc, 'name') else str(npc)
        personality = npc.personality.value if hasattr(npc, 'personality') else "未知"
        state = npc.state.value if hasattr(npc, 'state') else "idle"
        mood = npc.mood if hasattr(npc, 'mood') else 0.5
        mood_desc = "心情不错" if mood > 0.6 else "心情一般" if mood > 0.3 else "心情不太好"
        lines.append(f"- {name} ({personality}, {state}, {mood_desc})")
    
    return "\n".join(lines)


def build_memory_block(relevant_memories: List[Any]) -> str:
    """
    构建记忆块
    
    Args:
        relevant_memories: 相关的记忆列表
        
    Returns:
        记忆块文本
    """
    if not relevant_memories:
        return ""
    
    memory_lines = ["\n相关记忆:"]
    for mem in relevant_memories[:MAX_MEMORY_COUNT]:
        content = mem.content if hasattr(mem, 'content') else str(mem)
        content = truncate_content(content, MAX_MEMORY_LENGTH)
        memory_lines.append(f"- {content}")
    
    return "\n".join(memory_lines)


def build_dialogue_block(recent_messages: List[Any]) -> str:
    """
    构建对话历史块
    
    Args:
        recent_messages: 最近的消息列表（按时间倒序，最新的在前）
        
    Returns:
        对话历史文本
    """
    if not recent_messages:
        return "\n\n最近的对话:\n(无)"
    
    latest_five = recent_messages[:MAX_DIALOGUE_HISTORY]
    
    dialogue_lines = ["\n最近的对话:"]
    for msg in reversed(latest_five):
        role = "用户" if msg.role == "human" else "你"
        content = truncate_content(msg.content, MAX_MESSAGE_LENGTH)
        dialogue_lines.append(f"{role}: {content}")
    
    return "\n".join(dialogue_lines)


def build_user_input_block(user_input: str) -> str:
    """
    构建用户输入块
    
    Args:
        user_input: 用户输入
        
    Returns:
        用户输入文本
    """
    truncated_input = truncate_content(user_input, MAX_MESSAGE_LENGTH)
    return f"\n用户: {truncated_input}"
