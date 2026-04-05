"""
情绪服务

V5 核心组件：情绪分析和管理。

========================================
模块边界约束（第四次整改）
========================================

【正确定位】
emotion 模块只回答一个问题：
> 当前角色的情绪状态是什么，以及如何平滑更新。

【必须保留】
- 情绪状态对象 (EmotionalState)
- 情绪更新规则
- 情绪强度/趋势
- 情绪标签 (EmotionType)
- 情绪历史摘要

【绝对禁止】
- 直接决定最终回复
- 直接决定是否调用工具
- 直接决定是否发主动消息
- 直接写入长期记忆
- 直接改 world state
- 跨模块控制逻辑

【输出规范】
只为 EmotionBrain 提供底层支持，输出 EmotionInsight 正式 schema。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """情绪类型"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"


@dataclass
class EmotionalState:
    """情绪状态"""
    emotions: Dict[str, float]
    valence: float = 0.0
    arousal: float = 0.5
    
    def get_dominant_emotion(self) -> tuple:
        """获取主导情绪"""
        if not self.emotions:
            return (EmotionType.NEUTRAL, 0.0)
        
        dominant = max(self.emotions.items(), key=lambda x: x[1])
        return (EmotionType(dominant[0]), dominant[1])


class EmotionService:
    """
    情绪服务
    
    分析和管理情绪状态。
    """
    
    EMOTION_KEYWORDS = {
        "joy": ["开心", "高兴", "快乐", "幸福", "喜欢", "爱"],
        "sadness": ["难过", "伤心", "悲伤", "郁闷", "不开心"],
        "anger": ["生气", "愤怒", "烦", "讨厌", "气死"],
        "fear": ["害怕", "担心", "恐惧", "紧张"],
        "surprise": ["惊讶", "意外", "没想到", "居然"]
    }
    
    def __init__(self):
        self.current_state: Optional[EmotionalState] = None
        self.history: List[EmotionalState] = []
    
    def analyze(self, text: str) -> EmotionalState:
        """分析文本情绪"""
        emotions = {}
        text_lower = text.lower()
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            emotions[emotion] = min(1.0, score * 0.3)
        
        if not any(emotions.values()):
            emotions["neutral"] = 0.5
        
        valence = self._calculate_valence(emotions)
        arousal = self._calculate_arousal(emotions)
        
        return EmotionalState(
            emotions=emotions,
            valence=valence,
            arousal=arousal
        )
    
    def analyze_and_update(self, text: str) -> EmotionalState:
        """分析并更新情绪状态"""
        state = self.analyze(text)
        self.current_state = state
        self.history.append(state)
        
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        return state
    
    def _calculate_valence(self, emotions: Dict[str, float]) -> float:
        """计算愉悦度"""
        positive = emotions.get("joy", 0) + emotions.get("surprise", 0) * 0.5
        negative = emotions.get("sadness", 0) + emotions.get("anger", 0) + emotions.get("fear", 0)
        return positive - negative
    
    def _calculate_arousal(self, emotions: Dict[str, float]) -> float:
        """计算激活度"""
        high_arousal = emotions.get("anger", 0) + emotions.get("fear", 0) + emotions.get("surprise", 0)
        low_arousal = emotions.get("sadness", 0)
        return 0.5 + high_arousal * 0.3 - low_arousal * 0.2
    
    def get_current_state(self) -> Optional[EmotionalState]:
        """获取当前情绪状态"""
        return self.current_state
