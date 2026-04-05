"""
LLM 工厂

统一创建 LLM 实例，支持多种后端。

第三次整改：
- 成为"全项目唯一正式 LLM 实例创建口"
- 提供 create_default_llm() / create_by_tier() / validate_provider_config() / get_provider_name()
- 支持严格模式和开发模式
- 禁止业务层自己 new provider

Beta-1 更新：
- 正式支持 SiliconFlow 作为 llm_type
- 优先级：SiliconFlow > OpenAI > Ollama
- 支持按档位创建 SiliconFlow 实例
"""

import logging
import os
from typing import Any, Dict, Optional, List, Tuple

from config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMFactory:
    """
    LLM 工厂类 - 全项目唯一正式 LLM 实例创建口
    
    第三次整改：
    - 封装 LLM 创建逻辑，支持多种后端
    - 提供统一的创建、校验、查询接口
    - 支持严格模式（正式环境）和开发模式
    
    使用规则：
    - 任何地方想拿模型，只允许调 LLM factory 或通过 AgentFactory 注入好的实例
    - 禁止业务层自己 new provider
    - 禁止 reply 层自己找模型
    - 禁止 brain 里自己拼模型实例
    - 禁止临时按环境变量直接实例化模型
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._settings = get_settings()
        self._provider_name: Optional[str] = None
    
    def create(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        创建 LLM 实例
        
        Args:
            provider: 提供商类型 ('ollama', 'openai', 'siliconflow')
            model: 模型名称
            **kwargs: 额外参数
            
        Returns:
            LLM 实例
        """
        if provider:
            return _create_llm_by_type(provider, model=model, **kwargs)
        
        return create_llm_from_env(**kwargs)
    
    def create_default_llm(self, **kwargs) -> Any:
        """
        创建默认 LLM 实例
        
        第三次整改新增方法。
        按优先级自动选择可用的 provider。
        
        Returns:
            LLM 实例
        """
        llm = create_llm_from_env(**kwargs)
        self._provider_name = self._detect_provider_name()
        return llm
    
    def create_by_tier(self, tier: str = "standard", **kwargs) -> Any:
        """
        按档位创建 LLM 实例
        
        Args:
            tier: 模型层级 (cheap/standard/top)
            **kwargs: 额外参数
            
        Returns:
            LLM 实例
        """
        llm = create_siliconflow_llm_by_tier(tier=tier, **kwargs)
        self._provider_name = "siliconflow"
        return llm
    
    def validate_provider_config(self, provider: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        校验 provider 配置是否完整
        
        第三次整改新增方法。
        
        Args:
            provider: 提供商类型，如果为 None 则检测当前可用的
            
        Returns:
            (是否有效, 错误列表)
        """
        if provider is None:
            provider = self._detect_provider_name()
        
        return _validate_provider_config(provider)
    
    def get_provider_name(self) -> Optional[str]:
        """
        获取当前使用的 provider 名称
        
        第三次整改新增方法。
        
        Returns:
            provider 名称或 None
        """
        return self._provider_name
    
    def get_available_types(self) -> List[str]:
        """获取可用的 LLM 类型列表"""
        return get_available_llm_types()
    
    def _detect_provider_name(self) -> str:
        """检测当前使用的 provider 名称"""
        if self._settings.has_siliconflow:
            return "siliconflow"
        elif self._settings.has_openai:
            return "openai"
        else:
            return "ollama"


def _validate_provider_config(provider: str) -> Tuple[bool, List[str]]:
    """
    校验 provider 配置
    
    Args:
        provider: 提供商类型
        
    Returns:
        (是否有效, 错误列表)
    """
    errors = []
    settings = get_settings()
    
    if provider == "siliconflow":
        errors.extend(settings.validate_siliconflow())
    elif provider == "openai":
        errors.extend(settings.validate_openai())
    elif provider == "ollama":
        pass
    else:
        errors.append(f"未知的 provider: {provider}")
    
    return len(errors) == 0, errors


def create_llm_from_env(
    llm_type: Optional[str] = None,
    **kwargs
) -> Any:
    """
    从环境变量创建 LLM 实例
    
    Args:
        llm_type: LLM 类型 ('ollama', 'openai', 'siliconflow')，如果为 None 则自动检测
        **kwargs: 额外参数
        
    Returns:
        LLM 实例
        
    Raises:
        RuntimeError: 当没有可用的 LLM 时抛出异常
    """
    if llm_type:
        return _create_llm_by_type(llm_type, **kwargs)
    
    available_types = _detect_available_llm_types()
    
    if not available_types:
        raise RuntimeError(
            "未检测到可用的 LLM！\n"
            "请确保满足以下条件之一：\n"
            "1. 设置 SILICONFLOW_API_KEY 环境变量以使用 SiliconFlow API\n"
            "2. 设置 OPENAI_API_KEY 环境变量以使用 OpenAI API\n"
            "3. 安装并运行 Ollama 服务（默认端口 11434）\n"
            "4. 在调用时指定 llm_type 参数"
        )
    
    for candidate_type in available_types:
        try:
            return _create_llm_by_type(candidate_type, **kwargs)
        except Exception as e:
            logger.warning(f"尝试创建 {candidate_type} 失败: {e}，尝试下一个后端")
            continue
    
    raise RuntimeError(
        "所有可用的 LLM 后端初始化均失败！\n"
        "请检查配置或服务状态。"
    )


def _create_llm_by_type(llm_type: str, **kwargs) -> Any:
    """
    根据类型创建 LLM 实例
    
    Args:
        llm_type: LLM 类型
        **kwargs: 额外参数
        
    Returns:
        LLM 实例
    """
    if llm_type == "ollama":
        return _create_ollama_llm(**kwargs)
    elif llm_type == "openai":
        return _create_openai_llm(**kwargs)
    elif llm_type == "siliconflow":
        return _create_siliconflow_llm(**kwargs)
    else:
        raise ValueError(f"不支持的 LLM 类型: {llm_type}，支持: ollama, openai, siliconflow")


def _detect_available_llm_types() -> List[str]:
    """
    检测可用的 LLM 类型列表
    
    优先级：SiliconFlow > OpenAI > Ollama
    
    Returns:
        可用的 LLM 类型列表，按优先级排序
    """
    available = []
    
    if os.getenv("SILICONFLOW_API_KEY"):
        try:
            from infrastructure.llm.providers.siliconflow_provider import SiliconFlowLLM
            available.append("siliconflow")
            logger.info("检测到 SiliconFlow API (有 API Key)")
        except ImportError:
            logger.debug("SiliconFlowLLM 导入失败")
    
    if os.getenv("OPENAI_API_KEY"):
        try:
            from infrastructure.llm.providers.openai_provider import OpenAILLM
            available.append("openai")
            logger.info("检测到 OpenAI API (有 API Key)")
        except ImportError:
            logger.debug("OpenAI 包未安装")
    
    try:
        from infrastructure.llm.providers.ollama_provider import OllamaLLM
        available.append("ollama")
        logger.info("检测到 OllamaLLM")
    except ImportError:
        logger.debug("OllamaLLM 未安装")
    
    return available


def _create_ollama_llm(**kwargs) -> Any:
    """
    创建 Ollama LLM 实例
    
    Args:
        **kwargs: 额外参数
        
    Returns:
        OllamaLLM 实例
        
    Raises:
        RuntimeError: 创建失败时抛出异常
    """
    try:
        from infrastructure.llm.providers.ollama_provider import OllamaLLM
        llm = OllamaLLM(
            model=kwargs.get('model', 'llama3:latest'),
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000)
        )
        logger.info("成功初始化 OllamaLLM")
        return llm
    except ImportError:
        raise RuntimeError("OllamaLLM 导入失败，请确保已安装所需依赖")
    except Exception as e:
        raise RuntimeError(f"OllamaLLM 初始化失败: {e}")


def _create_openai_llm(**kwargs) -> Any:
    """
    创建 OpenAI LLM 实例
    
    Args:
        **kwargs: 额外参数，支持：
            - model: 模型名称
            - api_key: API Key
            - base_url: API 基础 URL
            - temperature: 温度参数
            - max_tokens: 最大 token 数
            - timeout: 请求超时时间
        
    Returns:
        OpenAILLM 实例
        
    Raises:
        RuntimeError: 创建失败时抛出异常
    """
    try:
        from infrastructure.llm.providers.openai_provider import OpenAILLM
        api_key = kwargs.get('api_key', os.getenv('OPENAI_API_KEY'))
        if not api_key:
            raise ValueError("未设置 API Key，请设置 OPENAI_API_KEY 环境变量或传入 api_key 参数")
        
        llm = OpenAILLM(
            model=kwargs.get('model', 'gpt-3.5-turbo'),
            api_key=api_key,
            base_url=kwargs.get('base_url'),
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            timeout=kwargs.get('timeout', 60.0)
        )
        logger.info("成功初始化 OpenAI LLM")
        return llm
    except Exception as e:
        raise RuntimeError(f"OpenAI LLM 初始化失败: {e}")


def _create_siliconflow_llm(**kwargs) -> Any:
    """
    创建 SiliconFlow LLM 实例
    
    Args:
        **kwargs: 额外参数，支持：
            - tier: 模型层级 (cheap/standard/top)
            - model: 模型名称（可选，优先从环境变量读取）
            - api_key: API Key（可选，优先从环境变量读取）
            - base_url: API 基础 URL（可选）
            - temperature: 温度参数
            - max_tokens: 最大 token 数
            - timeout: 请求超时时间
        
    Returns:
        SiliconFlowLLM 实例
        
    Raises:
        RuntimeError: 创建失败时抛出异常
    """
    try:
        from infrastructure.llm.providers.siliconflow_provider import SiliconFlowLLM
        
        tier = kwargs.get('tier', 'standard')
        
        llm = SiliconFlowLLM(
            model=kwargs.get('model'),
            api_key=kwargs.get('api_key'),
            base_url=kwargs.get('base_url'),
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            timeout=kwargs.get('timeout', 60.0),
            tier=tier
        )
        logger.info(f"成功初始化 SiliconFlow LLM (tier={tier})")
        return llm
    except Exception as e:
        raise RuntimeError(f"SiliconFlow LLM 初始化失败: {e}")


def create_siliconflow_llm_by_tier(tier: str = "standard", **kwargs) -> Any:
    """
    按档位创建 SiliconFlow LLM 实例
    
    Args:
        tier: 模型层级 (cheap/standard/top)
        **kwargs: 额外参数
        
    Returns:
        SiliconFlowLLM 实例
    """
    return _create_siliconflow_llm(tier=tier, **kwargs)


def get_available_llm_types() -> List[str]:
    """
    获取可用的 LLM 类型列表
    
    Returns:
        可用的 LLM 类型列表
    """
    return _detect_available_llm_types()
