"""
LLM 提供者基类

V5 核心组件：LLM 接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProviderType(Enum):
    """LLM 提供者类型"""
    OPENAI = "openai"
    SILICONFLOW = "siliconflow"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = None
    raw_response: Any = None
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = {}


class BaseLLMProvider(ABC):
    """
    LLM 提供者基类
    
    所有 LLM 提供者必须实现：
    - generate(): 生成文本
    - generate_with_schema(): 结构化输出
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @property
    @abstractmethod
    def provider_type(self) -> LLMProviderType:
        """提供者类型"""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """默认模型"""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本
        
        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse
        """
        pass
    
    @abstractmethod
    async def generate_with_schema(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        结构化输出
        
        Args:
            prompt: 输入提示
            schema: JSON Schema
            model: 模型名称
            **kwargs: 其他参数
            
        Returns:
            符合 schema 的字典
        """
        pass
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> LLMResponse:
        """
        聊天模式
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse
        """
        prompt = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages
        )
        return await self.generate(prompt, model, temperature, max_tokens, **kwargs)
