"""
配置管理

V5 核心组件：配置加载和管理。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "mock"
    model: str = "mock-model"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


@dataclass
class AppConfig:
    """应用配置"""
    debug: bool = False
    log_level: str = "INFO"
    
    llm_config: LLMConfig = None
    
    enable_tools: bool = True
    enable_npc: bool = False
    enable_world_content: bool = True
    enable_multi_model: bool = False
    
    world_tick_interval: int = 60
    proactive_check_interval: int = 300
    
    def __post_init__(self):
        if self.llm_config is None:
            self.llm_config = LLMConfig()


class ConfigManager:
    """
    配置管理器
    
    从环境变量和配置文件加载配置。
    """
    
    DEFAULT_CONFIG_PATH = "config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = AppConfig()
    
    def load(self) -> AppConfig:
        """加载配置"""
        self._load_from_env()
        
        self._load_from_file()
        
        return self.config
    
    def _load_from_env(self) -> None:
        """从环境变量加载"""
        if os.getenv("DEBUG", "").lower() == "true":
            self.config.debug = True
        
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            self.config.log_level = log_level
        
        llm_provider = os.getenv("LLM_PROVIDER")
        if llm_provider:
            self.config.llm_config.provider = llm_provider
        
        llm_model = os.getenv("LLM_MODEL")
        if llm_model:
            self.config.llm_config.model = llm_model
        
        api_key = os.getenv("LLM_API_KEY")
        if api_key:
            self.config.llm_config.api_key = api_key
        
        base_url = os.getenv("LLM_BASE_URL")
        if base_url:
            self.config.llm_config.base_url = base_url
    
    def _load_from_file(self) -> None:
        """从配置文件加载"""
        if not os.path.exists(self.config_path):
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "debug" in data:
                self.config.debug = data["debug"]
            
            if "log_level" in data:
                self.config.log_level = data["log_level"]
            
            if "llm" in data:
                llm_data = data["llm"]
                self.config.llm_config.provider = llm_data.get("provider", self.config.llm_config.provider)
                self.config.llm_config.model = llm_data.get("model", self.config.llm_config.model)
                self.config.llm_config.temperature = llm_data.get("temperature", self.config.llm_config.temperature)
                self.config.llm_config.max_tokens = llm_data.get("max_tokens", self.config.llm_config.max_tokens)
            
            if "features" in data:
                features = data["features"]
                self.config.enable_tools = features.get("enable_tools", self.config.enable_tools)
                self.config.enable_npc = features.get("enable_npc", self.config.enable_npc)
                self.config.enable_world_content = features.get("enable_world_content", self.config.enable_world_content)
                self.config.enable_multi_model = features.get("enable_multi_model", self.config.enable_multi_model)
            
            if "intervals" in data:
                intervals = data["intervals"]
                self.config.world_tick_interval = intervals.get("world_tick", self.config.world_tick_interval)
                self.config.proactive_check_interval = intervals.get("proactive_check", self.config.proactive_check_interval)
            
            logger.info(f"配置已从文件加载: {self.config_path}")
            
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取配置"""
        return self.config
