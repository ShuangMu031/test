"""
深度学习情感检测器

基于BERT模型的情绪识别实现。
"""

import sys
import os
import torch
import json
try:
    from transformers import BertTokenizer
    _TRANSFORMERS_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    BertTokenizer = None
    _TRANSFORMERS_IMPORT_ERROR = e
import numpy as np
from datetime import datetime

from domain.emotion.models import EmotionalState, EmotionType


class DataPreprocessor:
    """
    数据预处理器
    """
    
    def clean_text(self, text, language='chinese'):
        """
        清洗文本
        
        Args:
            text: 原始文本
            language: 语言类型
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 去除多余的空白字符
        text = ' '.join(text.strip().split())
        
        # 去除特殊字符（保留中文、英文、数字）
        if language == 'chinese':
            import re
            text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
        
        return text


class EmotionRecognitionModel(torch.nn.Module):
    """
    情感识别模型
    """
    
    def __init__(self, config):
        """
        初始化模型
        
        Args:
            config: 模型配置
        """
        super().__init__()
        from transformers import BertModel
        
        self.config = config
        self.pretrained_model = BertModel.from_pretrained(config.get('pretrained_model_name', 'bert-base-chinese'))
        
        # 情绪分类头
        self.emotion_classifier = torch.nn.Linear(
            self.pretrained_model.config.hidden_size,
            config.get('num_emotion_labels', 14)
        )
        
        # 主观性分类头
        self.subjectivity_classifier = torch.nn.Linear(
            self.pretrained_model.config.hidden_size,
            config.get('num_subjectivity_labels', 2)
        )
        
        self.dropout = torch.nn.Dropout(config.get('dropout_rate', 0.1))
    
    def forward(self, input_ids, attention_mask, token_type_ids=None):
        """
        前向传播
        
        Args:
            input_ids: 输入IDs
            attention_mask: 注意力掩码
            token_type_ids: token类型IDs
            
        Returns:
            模型输出
        """
        outputs = self.pretrained_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids
        )
        
        pooled_output = outputs[1]
        pooled_output = self.dropout(pooled_output)
        
        emotion_logits = self.emotion_classifier(pooled_output)
        subjectivity_logits = self.subjectivity_classifier(pooled_output)
        
        return {
            'emotion_logits': emotion_logits,
            'subjectivity_logits': subjectivity_logits
        }


class DeepLearningEmotionDetector:
    """
    深度学习情感检测器
    """
    
    def __init__(self, model_dir=None, device=None):
        """
        初始化情感检测器
        
        Args:
            model_dir: 模型目录
            device: 设备
        """
        if _TRANSFORMERS_IMPORT_ERROR is not None:
            raise RuntimeError(f"transformers 未安装，无法使用 DeepLearningEmotionDetector: {_TRANSFORMERS_IMPORT_ERROR}")

        # 设置设备
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 定义情绪标签映射
        self.LABELS = [
            'joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust',
            'trust', 'anticipation', 'love', 'admiration',
            'confusion', 'curiosity', 'excitement', 'gratitude'
        ]
        
        # 情绪类型映射
        self.EMOTION_TYPE_MAP = {
            'joy': EmotionType.JOY,
            'sadness': EmotionType.SADNESS,
            'anger': EmotionType.ANGER,
            'fear': EmotionType.FEAR,
            'surprise': EmotionType.SURPRISE,
            'disgust': EmotionType.DISGUST,
            'trust': EmotionType.TRUST,
            'anticipation': EmotionType.ANTICIPATION,
            'love': EmotionType.LOVE,
            'admiration': EmotionType.ADMIRATION,
            'confusion': EmotionType.CONFUSION,
            'curiosity': EmotionType.CURIOSITY,
            'excitement': EmotionType.EXCITEMENT,
            'gratitude': EmotionType.GRATITUDE
        }
        
        # 初始化数据预处理器
        self.preprocessor = DataPreprocessor()
        
        # 加载模型
        self.model = None
        self.tokenizer = None
        
        if model_dir and os.path.exists(model_dir):
            self._load_model(model_dir)
        else:
            # 尝试从默认路径加载
            default_model_dir = os.path.join(
                os.path.dirname(__file__),
                '..', '..', '..', 'models', 'saved', 'bert_emotion_model_chinese'
            )
            if os.path.exists(default_model_dir):
                self._load_model(default_model_dir)
            else:
                print("⚠️  未找到模型文件，将使用基于规则的情感分析")
    
    def _load_model(self, model_dir):
        """
        加载模型
        
        Args:
            model_dir: 模型目录
        """
        try:
            # 加载tokenizer
            tokenizer_path = os.path.join(model_dir, 'tokenizer')
            if not os.path.exists(tokenizer_path):
                # 如果没有单独的tokenizer目录，尝试直接加载
                self.tokenizer = BertTokenizer.from_pretrained(model_dir)
            else:
                self.tokenizer = BertTokenizer.from_pretrained(tokenizer_path)
            
            # 加载模型配置
            config_path = os.path.join(model_dir, 'config.json')
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 创建模型
            self.model = EmotionRecognitionModel(self.config)
            
            # 查找并加载模型权重
            model_path = os.path.join(model_dir, 'best_model.bin')
            if not os.path.exists(model_path):
                model_path = os.path.join(model_dir, 'model_epoch_3.bin')  # 尝试最后一个epoch的模型
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"没有找到模型文件: {model_path}")
            
            # 加载模型权重
            state_dict = torch.load(model_path, map_location=self.device)
            load_result = self.model.load_state_dict(state_dict, strict=False)
            
            if load_result.missing_keys:
                print(f"⚠️  缺失的键: {load_result.missing_keys[:5]}...")
            if load_result.unexpected_keys:
                print(f"⚠️  意外的键: {load_result.unexpected_keys[:5]}...")
            
            self.model.to(self.device)
            self.model.eval()
            print(f"✅ 模型成功加载: {model_path}")
            
        except Exception as e:
            import traceback
            print(f"❌ 模型加载失败: {e}")
            traceback.print_exc()
            self.model = None
    
    def detect(self, text, context=None):
        """
        检测文本中的情绪
        
        Args:
            text: 要分析的文本
            context: 上下文信息
            
        Returns:
            情感状态
        """
        if not text or not isinstance(text, str):
            return EmotionalState(
                emotions={},
                valence=0.0,
                arousal=0.0,
                dominance=0.5,
                timestamp=datetime.now().timestamp()
            )
        
        try:
            if self.model and self.tokenizer:
                # 使用深度学习模型
                return self._detect_with_model(text)
            else:
                # 使用基于规则的方法
                return self._detect_with_rules(text)
                
        except Exception as e:
            print(f"情绪识别错误: {e}")
            # 回退到基于规则的方法
            return self._detect_with_rules(text)
    
    def _detect_with_model(self, text):
        """
        使用模型检测情绪
        
        Args:
            text: 要分析的文本
            
        Returns:
            情感状态
        """
        # 清洗文本
        cleaned_text = self.preprocessor.clean_text(text, language='chinese')
        
        # 文本编码
        inputs = self.tokenizer(
            cleaned_text,
            padding='max_length',
            truncation=True,
            max_length=128,
            return_tensors='pt'
        )
        
        # 模型推理
        with torch.no_grad():
            input_ids = inputs['input_ids'].to(self.device)
            attention_mask = inputs['attention_mask'].to(self.device)
            token_type_ids = inputs.get('token_type_ids', None)
            if token_type_ids is not None:
                token_type_ids = token_type_ids.to(self.device)
            
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                token_type_ids=token_type_ids
            )
            
            # 获取情绪概率
            emotion_probs = torch.sigmoid(outputs['emotion_logits']).cpu().numpy()[0]
            
            # 获取主客观概率
            subjectivity_probs = torch.softmax(outputs['subjectivity_logits'], dim=1).cpu().numpy()[0]
            subjectivity_score = subjectivity_probs[1]  # 1表示主观
        
        # 构建情绪结果
        emotions = {}
        for i, prob in enumerate(emotion_probs):
            emotion_label = self.LABELS[i]
            if emotion_label in self.EMOTION_TYPE_MAP:
                emotions[self.EMOTION_TYPE_MAP[emotion_label]] = float(prob)
        
        # 计算效价和唤醒度
        valence, arousal = self._calculate_valence_arousal(emotions)
        
        return EmotionalState(
            emotions=emotions,
            valence=valence,
            arousal=arousal,
            dominance=0.5,  # 默认值
            timestamp=datetime.now().timestamp()
        )
    
    def _detect_with_rules(self, text):
        """
        使用规则检测情绪
        
        Args:
            text: 要分析的文本
            
        Returns:
            情感状态
        """
        # 关键词规则
        emotion_keywords = {
            EmotionType.JOY: ['开心', '快乐', '高兴', '喜悦', '兴奋', '愉快'],
            EmotionType.SADNESS: ['难过', '悲伤', '伤心', '悲痛', '沮丧', '忧郁'],
            EmotionType.ANGER: ['生气', '愤怒', '恼火', '气愤', '暴怒', '恼怒'],
            EmotionType.FEAR: ['害怕', '恐惧', '担心', '焦虑', '恐慌', '惧怕'],
            EmotionType.SURPRISE: ['惊讶', '惊奇', '震惊', '意外', '吃惊', '诧异'],
            EmotionType.DISGUST: ['厌恶', '恶心', '反感', '讨厌', '嫌弃', '憎恶'],
            EmotionType.TRUST: ['信任', '相信', '信赖', '信任', '确信', '放心'],
            EmotionType.ANTICIPATION: ['期待', '期望', '盼望', '等待', '期望', '憧憬'],
            EmotionType.LOVE: ['爱', '喜欢', '热爱', '关爱', '喜爱', '疼爱'],
            EmotionType.ADMIRATION: ['钦佩', '敬佩', '佩服', '敬仰', '钦佩', '赞佩'],
            EmotionType.CONFUSION: ['困惑', '迷茫', '疑惑', '不解', '困惑', '茫然'],
            EmotionType.CURIOSITY: ['好奇', '兴趣', '新奇', '好奇', '兴趣', '求知'],
            EmotionType.EXCITEMENT: ['兴奋', '激动', '亢奋', '兴奋', '激动', '亢奋'],
            EmotionType.GRATITUDE: ['感谢', '感激', '感恩', '谢谢', '致谢', '报恩']
        }
        
        emotions = {}
        for emotion_type, keywords in emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text:
                    score += 0.2
            if score > 0:
                emotions[emotion_type] = min(1.0, score)
        
        # 计算效价和唤醒度
        valence, arousal = self._calculate_valence_arousal(emotions)
        
        return EmotionalState(
            emotions=emotions,
            valence=valence,
            arousal=arousal,
            dominance=0.5,
            timestamp=datetime.now().timestamp()
        )
    
    def _calculate_valence_arousal(self, emotions):
        """
        计算效价和唤醒度
        
        Args:
            emotions: 情绪字典
            
        Returns:
            (valence, arousal)
        """
        # 情绪效价映射
        valence_map = {
            EmotionType.JOY: 0.8,
            EmotionType.SADNESS: -0.7,
            EmotionType.ANGER: -0.5,
            EmotionType.FEAR: -0.6,
            EmotionType.SURPRISE: 0.5,
            EmotionType.DISGUST: -0.6,
            EmotionType.TRUST: 0.6,
            EmotionType.ANTICIPATION: 0.4,
            EmotionType.LOVE: 0.9,
            EmotionType.ADMIRATION: 0.7,
            EmotionType.CONFUSION: -0.1,
            EmotionType.CURIOSITY: 0.3,
            EmotionType.EXCITEMENT: 0.7,
            EmotionType.GRATITUDE: 0.6
        }
        
        # 情绪唤醒度映射
        arousal_map = {
            EmotionType.JOY: 0.6,
            EmotionType.SADNESS: 0.3,
            EmotionType.ANGER: 0.8,
            EmotionType.FEAR: 0.7,
            EmotionType.SURPRISE: 0.8,
            EmotionType.DISGUST: 0.5,
            EmotionType.TRUST: 0.3,
            EmotionType.ANTICIPATION: 0.5,
            EmotionType.LOVE: 0.7,
            EmotionType.ADMIRATION: 0.4,
            EmotionType.CONFUSION: 0.4,
            EmotionType.CURIOSITY: 0.5,
            EmotionType.EXCITEMENT: 0.9,
            EmotionType.GRATITUDE: 0.3
        }
        
        if not emotions:
            return 0.0, 0.0
        
        # 计算加权平均
        total_weight = sum(emotions.values())
        valence = 0.0
        arousal = 0.0
        
        for emotion_type, strength in emotions.items():
            if emotion_type in valence_map:
                valence += valence_map[emotion_type] * strength
            if emotion_type in arousal_map:
                arousal += arousal_map[emotion_type] * strength
        
        if total_weight > 0:
            valence /= total_weight
            arousal /= total_weight
        
        return valence, arousal