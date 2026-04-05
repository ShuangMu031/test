"""
基础LLM接口

定义语言模型的通用接口，所有LLM实现都应该继承这个接口。

Beta-1 更新：
- 新增 chat() 方法支持消息列表
- 新增 structured() 方法支持结构化输出
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncGenerator


class BaseLLM(ABC):
    """
    基础LLM接口
    
    定义语言模型的通用方法，包括文本生成、流式生成、对话、结构化输出等。
    """
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 额外参数
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        对话生成
        
        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 额外参数
            
        Returns:
            生成的文本
        """
        pass
    
    @abstractmethod
    async def structured(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        结构化输出
        
        Args:
            messages: 消息列表
            response_format: 响应格式定义（JSON Schema）
            **kwargs: 额外参数
            
        Returns:
            结构化数据字典
        """
        pass
    
    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 额外参数
            
        Yields:
            生成的文本片段
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息
        """
        pass
