"""
策略相关 Schema

V6 统一字段体系：
- action_type: 动作类型（ActionType 枚举）
- reasoning: 推理说明
- response_hint: 响应提示
- confidence: 置信度（0-1）
- is_emergency: 是否紧急

第二次整改：
- 补充 from_dict() 方法
"""

from typing import Any, Dict
from dataclasses import dataclass

from .action_types import ActionType


@dataclass
class FallbackDecision:
    """
    兜底决策
    
    来自 FallbackPolicy 的输出，包含降级决策。
    
    统一字段说明：
    - action_type: 动作类型（ActionType 枚举）
    - reasoning: 推理说明
    - response_hint: 响应提示文本
    - confidence: 置信度（0-1）
    - is_emergency: 是否为紧急情况
    """
    action_type: ActionType
    reasoning: str
    response_hint: str = ""
    confidence: float = 0.5
    is_emergency: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "reasoning": self.reasoning,
            "response_hint": self.response_hint,
            "confidence": self.confidence,
            "is_emergency": self.is_emergency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FallbackDecision":
        action_type_value = data.get("action_type", "respond")
        if isinstance(action_type_value, str):
            action_type = ActionType(action_type_value)
        else:
            action_type = action_type_value
        
        return cls(
            action_type=action_type,
            reasoning=data.get("reasoning", ""),
            response_hint=data.get("response_hint", ""),
            confidence=data.get("confidence", 0.5),
            is_emergency=data.get("is_emergency", False)
        )
