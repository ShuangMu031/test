import torch
from datetime import datetime
from typing import Optional, Dict, Any
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _TRANSFORMERS_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    _TRANSFORMERS_IMPORT_ERROR = e

from domain.emotion.models import EmotionResult, EmotionType


class HFSentimentDetector:
    def __init__(
        self,
        model_name: str,
        device: Optional[str] = None,
        max_length: int = 256
    ):
        self.model_name = model_name
        self.max_length = max_length

        if device is None or device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        elif device == "cuda" and not torch.cuda.is_available():
            self.device = "cpu"
        else:
            self.device = device

        if _TRANSFORMERS_IMPORT_ERROR is not None:
            raise RuntimeError(f"transformers 未安装，无法使用 HFSentimentDetector: {_TRANSFORMERS_IMPORT_ERROR}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> EmotionResult:
        if not text or not isinstance(text, str):
            return EmotionResult(
                emotions={},
                valence=0.0,
                arousal=0.0,
                dominance=0.5,
                timestamp=datetime.now().timestamp(),
                source="hf_empty"
            )

        inputs = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        outputs = self.model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0].detach().cpu()

        negative_score = float(probs[0].item())
        positive_score = float(probs[1].item())

        emotions = {}
        valence = positive_score - negative_score

        if positive_score >= negative_score:
            emotions[EmotionType.JOY] = positive_score
            emotions[EmotionType.TRUST] = positive_score * 0.35
            emotions[EmotionType.EXCITEMENT] = positive_score * 0.25
            arousal = min(1.0, 0.45 + positive_score * 0.35)
            dominance = min(1.0, 0.55 + positive_score * 0.25)
        else:
            emotions[EmotionType.SADNESS] = negative_score * 0.55
            emotions[EmotionType.ANGER] = negative_score * 0.25
            emotions[EmotionType.FEAR] = negative_score * 0.20
            arousal = min(1.0, 0.35 + negative_score * 0.30)
            dominance = max(0.0, 0.50 - negative_score * 0.20)

        return EmotionResult(
            emotions=emotions,
            valence=max(-1.0, min(1.0, valence)),
            arousal=arousal,
            dominance=dominance,
            timestamp=datetime.now().timestamp(),
            source=f"hf:{self.model_name}"
        )


# 保留旧命名兼容 agent_factory / __init__ 导入
HuggingFaceSentimentDetector = HFSentimentDetector
