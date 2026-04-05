"""
情绪相关 Schema

V6 统一字段体系：
- primary_emotion: 主要情绪
- valence: 效价（-1 到 1）
- arousal: 唤醒度（0 到 1）
- support_need: 支持需求
- reasoning: 推理说明

第二次整改：
- 补充 from_dict() 方法
"""

from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class EmotionInsight:
    """
    情绪洞察
    
    来自 EmotionBrain 的输出，包含情绪分析结果。
    
    统一字段说明：
    - primary_emotion: 主要情绪
    - valence: 效价（-1 到 1）
    - arousal: 唤醒度（0 到 1）
    - support_need: 支持需求类型
    - reasoning: 推理说明
    """
    primary_emotion: str
    valence: float
    arousal: float
    support_need: str
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_emotion": self.primary_emotion,
            "valence": self.valence,
            "arousal": self.arousal,
            "support_need": self.support_need,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionInsight":
        return cls(
            primary_emotion=data.get("primary_emotion", "neutral"),
            valence=data.get("valence", 0.0),
            arousal=data.get("arousal", 0.5),
            support_need=data.get("support_need", "none"),
            reasoning=data.get("reasoning", "")
        )
