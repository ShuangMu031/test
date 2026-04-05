"""
SiliconFlow LLM Provider

SiliconFlow API 的 LLM 实现。
支持多档位模型配置。
"""

import os
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator

from infrastructure.llm.base import BaseLLM

logger = logging.getLogger(__name__)

TIER_MODEL_MAP = {
    "cheap": None,
    "standard": None,
    "top": None,
}


class SiliconFlowLLM(BaseLLM):
    """
    SiliconFlow LLM 实现
    
    支持：
    - 文本生成
    - 对话
    - 结构化输出
    - 流式生成
    - 多档位模型
    """
    
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: float = 60.0,
        tier: str = "standard"
    ):
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self.base_url = base_url or os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.tier = tier
        
        if model:
            self.model = model
        else:
            self.model = self._get_model_for_tier(tier)
        
        self._client = None
        self._validate_config()
    
    def _get_model_for_tier(self, tier: str) -> str:
        """根据档位获取模型名称"""
        tier_models = {
            "cheap": os.getenv("SF_MODEL_CHEAP", "Qwen/Qwen2.5-7B-Instruct"),
            "standard": os.getenv("SF_MODEL_STANDARD", "Qwen/Qwen2.5-72B-Instruct"),
            "top": os.getenv("SF_MODEL_TOP", "deepseek-ai/DeepSeek-V3"),
        }
        return tier_models.get(tier, tier_models["standard"])
    
    def _validate_config(self) -> None:
        """验证配置"""
        if not self.api_key:
            raise ValueError("未设置 SILICONFLOW_API_KEY")
        if not self.model:
            raise ValueError("未指定模型")
    
    def _get_client(self):
        """获取 OpenAI 兼容客户端"""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
            except ImportError:
                raise RuntimeError("请安装 openai 包: pip install openai")
        return self._client
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成文本"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """对话生成"""
        client = self._get_client()
        
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"SiliconFlow API 调用失败: {e}")
            raise
    
    async def structured(
        self,
        messages: List[Dict[str, str]],
        response_format: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """结构化输出"""
        client = self._get_client()
        
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            import json
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"SiliconFlow 结构化输出失败: {e}")
            raise
    
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """流式生成"""
        client = self._get_client()
        messages = [{"role": "user", "content": prompt}]
        
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        try:
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"SiliconFlow 流式生成失败: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "siliconflow",
            "model": self.model,
            "tier": self.tier,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
