"""
功能开关

V9 改版：控制各模块的启用/禁用

设计原则：
- 成熟的默认开
- 不成熟的默认关
- 可通过配置覆盖
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os


@dataclass
class FeatureFlags:
    """
    功能开关配置
    
    控制各模块的启用/禁用状态
    """
    
    enable_world_tick: bool = True
    enable_proactivity: bool = False
    enable_world_content: bool = False
    enable_memory_consolidation: bool = True
    enable_observability: bool = False
    enable_mock_llm: bool = False
    enable_npc_brain: bool = False
    enable_emotion_detection: bool = False
    enable_auto_save: bool = True
    enable_reality_sources: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enable_world_tick": self.enable_world_tick,
            "enable_proactivity": self.enable_proactivity,
            "enable_world_content": self.enable_world_content,
            "enable_memory_consolidation": self.enable_memory_consolidation,
            "enable_observability": self.enable_observability,
            "enable_mock_llm": self.enable_mock_llm,
            "enable_npc_brain": self.enable_npc_brain,
            "enable_emotion_detection": self.enable_emotion_detection,
            "enable_auto_save": self.enable_auto_save,
            "enable_reality_sources": self.enable_reality_sources,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlags":
        """从字典创建"""
        return cls(
            enable_world_tick=data.get("enable_world_tick", True),
            enable_proactivity=data.get("enable_proactivity", False),
            enable_world_content=data.get("enable_world_content", False),
            enable_memory_consolidation=data.get("enable_memory_consolidation", True),
            enable_observability=data.get("enable_observability", False),
            enable_mock_llm=data.get("enable_mock_llm", False),
            enable_npc_brain=data.get("enable_npc_brain", False),
            enable_emotion_detection=data.get("enable_emotion_detection", False),
            enable_auto_save=data.get("enable_auto_save", True),
            enable_reality_sources=data.get("enable_reality_sources", False),
        )
    
    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """从环境变量创建"""
        def get_bool(key: str, default: bool) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ("true", "1", "yes", "on")
        
        return cls(
            enable_world_tick=get_bool("V9_ENABLE_WORLD_TICK", True),
            enable_proactivity=get_bool("V10_ENABLE_PROACTIVITY", False),
            enable_world_content=get_bool("V9_ENABLE_WORLD_CONTENT", False),
            enable_memory_consolidation=get_bool("V9_ENABLE_MEMORY_CONSOLIDATION", True),
            enable_observability=get_bool("V9_ENABLE_OBSERVABILITY", False),
            enable_mock_llm=get_bool("V9_ENABLE_MOCK_LLM", False),
            enable_npc_brain=get_bool("V9_ENABLE_NPC_BRAIN", False),
            enable_emotion_detection=get_bool("V9_ENABLE_EMOTION_DETECTION", False),
            enable_auto_save=get_bool("V9_ENABLE_AUTO_SAVE", True),
            enable_reality_sources=get_bool("V9_ENABLE_REALITY_SOURCES", False),
        )
    
    def is_enabled(self, feature: str) -> bool:
        """
        检查功能是否启用
        
        Args:
            feature: 功能名称
            
        Returns:
            是否启用
        """
        return getattr(self, f"enable_{feature}", False)


_default_flags: Optional[FeatureFlags] = None


def get_feature_flags() -> FeatureFlags:
    """
    获取全局功能开关
    
    Returns:
        FeatureFlags 实例
    """
    global _default_flags
    if _default_flags is None:
        _default_flags = FeatureFlags.from_env()
    return _default_flags


def set_feature_flags(flags: FeatureFlags) -> None:
    """
    设置全局功能开关
    
    Args:
        flags: FeatureFlags 实例
    """
    global _default_flags
    _default_flags = flags


def is_feature_enabled(feature: str) -> bool:
    """
    检查功能是否启用
    
    Args:
        feature: 功能名称
        
    Returns:
        是否启用
    """
    return get_feature_flags().is_enabled(feature)
