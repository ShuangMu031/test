"""
情绪领域模型

定义情绪相关的数据结构和接口。
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class EmotionType(Enum):
    """情绪类型枚举"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    LOVE = "love"
    ADMIRATION = "admiration"
    CONFUSION = "confusion"
    CURIOSITY = "curiosity"
    EXCITEMENT = "excitement"
    GRATITUDE = "gratitude"


@dataclass
class EmotionalState:
    """
    情感状态
    
    表示持续的情绪状态，随时间累积和变化。
    
    Attributes:
        emotions: 情绪字典，键为情绪类型，值为强度（0-1）
        valence: 效价（-1到1，负值为消极，正值为积极）
        arousal: 唤醒度（0到1，值越高越兴奋）
        dominance: 支配度（0到1，值越高越有控制感）
        timestamp: 时间戳
    """
    emotions: Dict[EmotionType, float]
    valence: float
    arousal: float
    dominance: float
    timestamp: float
    
    def get_dominant_emotion(self) -> Optional[Tuple[EmotionType, float]]:
        """
        获取主导情绪
        
        Returns:
            主导情绪及其强度
        """
        if not self.emotions:
            return None
        return max(self.emotions.items(), key=lambda x: x[1])
    
    def to_dict(self) -> Dict[str, any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "emotions": {emotion.value: strength for emotion, strength in self.emotions.items()},
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "timestamp": self.timestamp,
            "dominant_emotion": self.get_dominant_emotion()[0].value if self.get_dominant_emotion() else None,
            "dominant_emotion_strength": self.get_dominant_emotion()[1] if self.get_dominant_emotion() else 0
        }


@dataclass
class EmotionResult:
    """
    情绪识别结果
    
    表示单次文本输入识别出的情绪，与持续情绪状态区分。
    用于情绪检测器的输出。
    
    Attributes:
        emotions: 情绪字典，键为情绪类型，值为强度（0-1）
        valence: 效价（-1到1）
        arousal: 唤醒度（0到1）
        dominance: 支配度（0到1）
        timestamp: 时间戳
        source: 来源标识（如 'deep_learning', 'rule_based'）
    """
    emotions: Dict[EmotionType, float]
    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.5
    timestamp: float = 0.0
    source: str = "detector"
    
    def get_dominant_emotion(self) -> Optional[Tuple[EmotionType, float]]:
        """
        获取主导情绪
        
        Returns:
            主导情绪及其强度
        """
        if not self.emotions:
            return None
        dominant = max(self.emotions.items(), key=lambda x: x[1])
        return dominant if dominant[1] > 0 else None
    
    def to_dict(self) -> Dict[str, any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "emotions": {emotion.value: strength for emotion, strength in self.emotions.items()},
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "timestamp": self.timestamp,
            "source": self.source,
            "dominant_emotion": self.get_dominant_emotion()[0].value if self.get_dominant_emotion() else None,
            "dominant_emotion_strength": self.get_dominant_emotion()[1] if self.get_dominant_emotion() else 0
        }
    
    def to_emotional_state(self) -> 'EmotionalState':
        """
        转换为 EmotionalState
        
        Returns:
            EmotionalState 实例
        """
        return EmotionalState(
            emotions=self.emotions.copy(),
            valence=self.valence,
            arousal=self.arousal,
            dominance=self.dominance,
            timestamp=self.timestamp
        )


@dataclass
class EmotionEvent:
    """
    情感事件
    
    Attributes:
        text: 触发情感的文本
        emotion_result: 单次情绪检测结果
        emotional_state: 更新后的持续情感状态
        context: 上下文信息
    """
    text: str
    emotion_result: EmotionResult
    emotional_state: Optional[EmotionalState] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
