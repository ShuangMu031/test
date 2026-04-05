"""
情绪脑

V5 核心组件：情绪分析和洞察。
"""

from typing import Any, Dict
import logging

from .base import BaseBrain
from application.contracts import EmotionInsight

logger = logging.getLogger(__name__)


class EmotionBrain(BaseBrain):
    """
    情绪脑
    
    职责：
    1. 分析用户情绪
    2. 判断支持需求
    3. 提供情绪洞察
    """
    
    def __init__(self, llm=None, emotion_service=None):
        self.llm = llm
        self.emotion_service = emotion_service
    
    @property
    def name(self) -> str:
        return "emotion"
    
    async def process(self, context: Any) -> EmotionInsight:
        """处理情绪"""
        emotional_state = context.emotional_state
        
        if emotional_state:
            primary_emotion = getattr(emotional_state, "dominant_emotion", (None, 0.0))
            if isinstance(primary_emotion, tuple):
                emotion_name = primary_emotion[0].value if primary_emotion[0] else "neutral"
            else:
                emotion_name = str(primary_emotion)
            
            valence = getattr(emotional_state, "valence", 0.0)
            arousal = getattr(emotional_state, "arousal", 0.5)
        else:
            emotion_name = "neutral"
            valence = 0.0
            arousal = 0.5
        
        support_need = self._determine_support_need(valence, arousal)
        
        context.record_telemetry(
            "emotion",
            valence=valence,
            arousal=arousal,
            primary_emotion=emotion_name,
            support_need=support_need
        )
        
        context.record_monologue(
            "emotion",
            monologue=f"检测到用户情绪为 {emotion_name}，效价 {valence:.2f}，唤醒度 {arousal:.2f}",
            actions=[
                f"分析情绪状态: {emotion_name}",
                f"判断支持需求: {support_need}"
            ],
            interactions=["从 emotional_state 获取情绪数据"]
        )
        
        return EmotionInsight(
            primary_emotion=emotion_name,
            valence=valence,
            arousal=arousal,
            support_need=support_need,
            reasoning=f"基于情绪分析: {emotion_name}"
        )
    
    def _determine_support_need(self, valence: float, arousal: float) -> str:
        """判断支持需求"""
        if valence < -0.5:
            return "high"
        elif valence < -0.2:
            return "medium"
        else:
            return "none"
