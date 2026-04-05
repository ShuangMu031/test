"""
Mock LLM 提供者

V5 核心组件：测试用 Mock 提供者。
"""

from typing import Dict, Any, Optional, List
import json
import logging

from .base_provider import BaseLLMProvider, LLMResponse, LLMProviderType

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM 提供者
    
    用于测试，不调用真实 API。
    """
    
    @property
    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.MOCK
    
    @property
    def default_model(self) -> str:
        return "mock-model"
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """生成文本"""
        response_text = self._generate_mock_response(prompt)
        
        return LLMResponse(
            content=response_text,
            model=model or self.default_model,
            provider=self.provider_type.value,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
    
    async def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """结构化输出"""
        return self._generate_mock_structured(prompt, schema)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """聊天模式"""
        last_message = messages[-1] if messages else {"content": ""}
        return await self.generate(last_message.get("content", ""), model, temperature, max_tokens, **kwargs)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """生成 Mock 响应"""
        if "情绪" in prompt or "情感" in prompt:
            return json.dumps({
                "primary_emotion": "neutral",
                "valence": 0.0,
                "arousal": 0.5,
                "support_need": "none"
            }, ensure_ascii=False)
        
        if "记忆" in prompt or "存储" in prompt:
            return json.dumps({
                "should_store": True,
                "importance": 0.5,
                "tags": ["对话"]
            }, ensure_ascii=False)
        
        if "行为" in prompt or "决策" in prompt:
            return json.dumps({
                "mode": "chat",
                "primary_action": "respond",
                "priority": 5,
                "confidence": 0.8
            }, ensure_ascii=False)
        
        return "这是一个模拟响应。"
    
    def _generate_mock_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """生成 Mock 结构化响应"""
        properties = schema.get("properties", {})
        result = {}
        
        for key, prop in properties.items():
            prop_type = prop.get("type", "string")
            
            if prop_type == "string":
                result[key] = "mock_value"
            elif prop_type == "number":
                result[key] = 0.5
            elif prop_type == "integer":
                result[key] = 5
            elif prop_type == "boolean":
                result[key] = True
            elif prop_type == "array":
                result[key] = []
            elif prop_type == "object":
                result[key] = {}
        
        return result
