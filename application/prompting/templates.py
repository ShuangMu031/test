"""
Prompt 模板

定义系统提示和风格控制模板。
"""

from typing import Dict


STYLE_INSTRUCTIONS: Dict[str, str] = {
    "friendly": "请用自然、友好、口语化的中文回复用户。回答要简洁明了，避免重复使用相同词汇，不要使用表情符号或多余标点，确保回答流畅自然。必须使用纯中文，不要混合任何英文词汇或缩写。",
    "professional": "请用专业、正式的中文回复用户。回答要准确、有条理，避免口语化表达。",
    "casual": "请用轻松、随意的中文回复用户。可以适当使用口语化表达，保持亲切感。",
    "empathetic": "请用温暖、共情的中文回复用户。关注用户的情绪状态，给予适当的支持和理解。"
}

ACTION_GUIDANCE: Dict[str, str] = {
    "comfort": "用户情绪低落，请给予温暖的安慰和支持。",
    "socialize": "用户心情不错，可以愉快地交流。",
    "rest": "可以建议用户休息一下。",
    "respond": "正常回复用户的问题。",
    "listen": "用户需要倾诉，请耐心倾听并给予回应。"
}


def get_style_instruction(style: str) -> str:
    """
    获取风格指令
    
    Args:
        style: 风格名称
        
    Returns:
        风格指令文本
    """
    return STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["friendly"])


def get_action_guidance(action_type: str) -> str:
    """
    获取动作指导
    
    Args:
        action_type: 动作类型
        
    Returns:
        动作指导文本
    """
    return ACTION_GUIDANCE.get(action_type, "正常回复用户。")


def build_system_template(
    name: str,
    personality: str,
    backstory: str,
    time_str: str,
    location_str: str,
    weather_str: str,
    activity_str: str,
    emotion_str: str,
    emotion_strength: float,
    valence: float,
    arousal: float
) -> str:
    """
    构建系统提示模板
    
    Args:
        name: 角色名称
        personality: 性格
        backstory: 背景故事
        time_str: 时间字符串
        location_str: 地点字符串
        weather_str: 天气字符串
        activity_str: 活动字符串
        emotion_str: 情绪字符串
        emotion_strength: 情绪强度
        valence: 效价
        arousal: 唤醒度
        
    Returns:
        系统提示文本
    """
    return f"""你是{name}，一个{personality}的AI助手。

背景故事:
{backstory}

当前情况:
- 时间: {time_str}
- 地点: {location_str}
- 天气: {weather_str}
- 活动: {activity_str}

本轮输入情绪分析:
- 主导情绪: {emotion_str} (强度: {emotion_strength:.2f})
- 效价: {valence:.2f} (消极到积极)
- 唤醒度: {arousal:.2f} (平静到兴奋)"""
