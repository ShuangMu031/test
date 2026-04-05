"""
情绪检测器

V9 情绪检测基础设施

提供基于深度学习和 HuggingFace 的情绪检测实现
对 transformers 采用软依赖：未安装时不在 import 阶段炸掉整个项目
"""

__all__ = []

try:
    from infrastructure.emotion_detectors.huggingface_sentiment_detector import HuggingfaceSentimentDetector
    __all__.append("HuggingfaceSentimentDetector")
except Exception:
    HuggingfaceSentimentDetector = None

try:
    from infrastructure.emotion_detectors.deep_learning_detector import DeepLearningEmotionDetector
    __all__.append("DeepLearningEmotionDetector")
except Exception:
    DeepLearningEmotionDetector = None
