"""
Mock LLM

V6 新增：实现 BaseLLM 接口的模拟 LLM。
用于测试和 fallback 场景。

职责：
- 实现 BaseLLM 所有抽象方法
- 提供可预测的响应
- 支持测试场景
"""

from typing import Dict, Any, List, AsyncGenerator
import json

from infrastructure.llm.base import BaseLLM


class MockLLM(BaseLLM):
    """
    模拟 LLM
    
    实现 BaseLLM 接口，用于测试和 fallback。
    """
    
    def __init__(self, model_name: str = "mock-llm"):
        self.model_name = model_name
        self._call_count = 0
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        self._call_count += 1
        
        if "天气" in prompt:
            return "今天天气不错，阳光明媚。"
        elif "新闻" in prompt:
            return "今天有一些有趣的新闻。"
        elif "情绪" in prompt or "情感" in prompt:
            return json.dumps({
                "primary_emotion": "neutral",
                "valence": 0.5,
                "arousal": 0.5
            }, ensure_ascii=False)
        elif "计划" in prompt or "行为" in prompt:
            return json.dumps({
                "primary_action": "reply",
                "reasoning": "用户需要回复"
            }, ensure_ascii=False)
        else:
            return f"[MockLLM] 收到请求，这是一个模拟响应。调用次数: {self._call_count}"
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        self._call_count += 1
        
        last_message = messages[-1] if messages else {}
        content = last_message.get("content", "")
        
        if "你好" in content or "hello" in content.lower():
            return "你好！我是 AI 助手，很高兴为你服务。"
        elif "怎么样" in content:
            return "我很好，谢谢关心！"
        else:
            return f"[MockLLM] 我收到了你的消息: {content[:50]}..."
    
    async def structured(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """结构化输出"""
        self._call_count += 1
        
        properties = response_format.get("properties", {})
        
        result = {}
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            if prop_type == "string":
                result[key] = f"mock_{key}"
            elif prop_type == "number":
                result[key] = 0.5
            elif prop_type == "boolean":
                if key == "should_send":
                    result[key] = True
                else:
                    result[key] = False
            elif prop_type == "array":
                result[key] = []
            elif prop_type == "object":
                result[key] = {}
        
        return result
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成文本"""
        self._call_count += 1
        response = f"[MockLLM Stream] 这是一个模拟的流式响应。"
        for char in response:
            yield char
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.model_name,
            "type": "mock",
            "call_count": self._call_count,
            "capabilities": ["generate", "chat", "structured", "stream"]
        }
