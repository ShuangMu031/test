"""
统一配置模块

负责：
- 加载 .env 文件
- 校验关键环境变量
- 暴露配置对象

所有入口（CLI、API、测试）都从这里拿配置。

第三次整改：
- 增加 RUNTIME_MODE 配置（dev/prod）
- STRICT_LLM_INIT 控制严格初始化
- 提供运行模式判断方法
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


class RuntimeMode:
    """运行模式"""
    DEV = "dev"
    PROD = "prod"


class Settings:
    """
    统一配置类
    
    第三次整改：
    - 增加 RUNTIME_MODE 配置
    - STRICT_LLM_INIT 控制严格初始化
    - 提供 is_dev_mode() / is_prod_mode() 方法
    """
    
    SILICONFLOW_API_KEY: Optional[str] = os.getenv("SILICONFLOW_API_KEY")
    SILICONFLOW_BASE_URL: str = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    
    SF_MODEL_CHEAP: Optional[str] = os.getenv("SF_MODEL_CHEAP")
    SF_MODEL_STANDARD: Optional[str] = os.getenv("SF_MODEL_STANDARD")
    SF_MODEL_TOP: Optional[str] = os.getenv("SF_MODEL_TOP")
    
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL_CHEAP: str = os.getenv("OPENAI_MODEL_CHEAP", "gpt-4o-mini")
    OPENAI_MODEL_STANDARD: str = os.getenv("OPENAI_MODEL_STANDARD", "gpt-4.1-mini")
    OPENAI_MODEL_TOP: str = os.getenv("OPENAI_MODEL_TOP", "gpt-4.1")
    
    RUNTIME_MODE: str = os.getenv("RUNTIME_MODE", "dev").lower()
    STRICT_LLM_INIT: bool = os.getenv("STRICT_LLM_INIT", "false").lower() == "true"
    
    @property
    def has_siliconflow(self) -> bool:
        return bool(self.SILICONFLOW_API_KEY)
    
    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)
    
    @property
    def siliconflow_models_configured(self) -> bool:
        return all([self.SF_MODEL_CHEAP, self.SF_MODEL_STANDARD, self.SF_MODEL_TOP])
    
    def is_dev_mode(self) -> bool:
        """是否为开发模式"""
        return self.RUNTIME_MODE == RuntimeMode.DEV
    
    def is_prod_mode(self) -> bool:
        """是否为正式模式"""
        return self.RUNTIME_MODE == RuntimeMode.PROD
    
    def is_strict_mode(self) -> bool:
        """
        是否为严格模式
        
        严格模式下：
        - provider 缺失就启动失败
        - router 未完整注册就启动失败
        - 关键 service 缺失就启动失败
        - 禁止使用 mock
        """
        return self.STRICT_LLM_INIT or self.is_prod_mode()
    
    def get_available_llm_types(self) -> List[str]:
        """获取可用的 LLM 类型"""
        available = []
        if self.has_siliconflow:
            available.append("siliconflow")
        if self.has_openai:
            available.append("openai")
        available.append("ollama")
        return available
    
    def validate_siliconflow(self) -> List[str]:
        """校验 SiliconFlow 配置"""
        errors = []
        if not self.SILICONFLOW_API_KEY:
            errors.append("SILICONFLOW_API_KEY 未设置")
        if not self.SF_MODEL_CHEAP:
            errors.append("SF_MODEL_CHEAP 未设置")
        if not self.SF_MODEL_STANDARD:
            errors.append("SF_MODEL_STANDARD 未设置")
        if not self.SF_MODEL_TOP:
            errors.append("SF_MODEL_TOP 未设置")
        return errors
    
    def validate_openai(self) -> List[str]:
        """校验 OpenAI 配置"""
        errors = []
        if not self.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY 未设置")
        return errors
    
    def validate_llm_config(self, llm_type: str, enable_multi_model: bool = True) -> List[str]:
        """
        校验 LLM 配置
        
        Args:
            llm_type: LLM 类型
            enable_multi_model: 是否启用多模型
            
        Returns:
            错误列表
        """
        errors = []
        
        if llm_type == "siliconflow":
            errors.extend(self.validate_siliconflow())
        elif llm_type == "openai":
            errors.extend(self.validate_openai())
        elif llm_type == "ollama":
            pass
        else:
            if not self.has_siliconflow and not self.has_openai:
                errors.append("未检测到可用的 LLM 配置（需要 SILICONFLOW_API_KEY 或 OPENAI_API_KEY）")
        
        return errors
    
    def get_status(self) -> dict:
        """获取配置状态"""
        return {
            "runtime_mode": self.RUNTIME_MODE,
            "strict_mode": self.is_strict_mode(),
            "siliconflow": {
                "api_key_set": bool(self.SILICONFLOW_API_KEY),
                "base_url": self.SILICONFLOW_BASE_URL,
                "models": {
                    "cheap": self.SF_MODEL_CHEAP,
                    "standard": self.SF_MODEL_STANDARD,
                    "top": self.SF_MODEL_TOP
                }
            },
            "openai": {
                "api_key_set": bool(self.OPENAI_API_KEY),
                "models": {
                    "cheap": self.OPENAI_MODEL_CHEAP,
                    "standard": self.OPENAI_MODEL_STANDARD,
                    "top": self.OPENAI_MODEL_TOP
                }
            },
            "available_llm_types": self.get_available_llm_types()
        }


settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


def validate_startup(llm_type: str = None, enable_multi_model: bool = True) -> None:
    """
    启动前校验
    
    Args:
        llm_type: LLM 类型
        enable_multi_model: 是否启用多模型
        
    Raises:
        RuntimeError: 配置校验失败
    """
    if llm_type is None:
        llm_type = "siliconflow" if settings.has_siliconflow else "openai" if settings.has_openai else "ollama"
    
    errors = settings.validate_llm_config(llm_type, enable_multi_model)
    
    if errors:
        error_msg = f"配置校验失败 ({llm_type}):\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info(f"配置校验通过，LLM 类型: {llm_type}")
