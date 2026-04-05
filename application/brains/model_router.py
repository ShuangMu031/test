"""
模型路由器

V6 核心组件：多模型分配。

第三次整改：
- 成为"严格路由器"，不是"温柔兜底器"
- 提供 register() / get_llm_for_tier() / has_tier() / validate_registry()
- 启动时必须校验 cheap/standard/top 都已注册
- 未注册时抛出异常而非静默返回 None

档位命名统一：
- cheap: 快速、低成本
- standard: 标准能力
- top: 高级能力

兼容旧命名：
- fast -> cheap
- premium -> top
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """
    模型档位枚举
    
    统一档位命名：
    - CHEAP: 快速、低成本
    - STANDARD: 标准能力
    - TOP: 高级能力
    
    第三次整改：
    - 成为项目内唯一的正式 tier 定义
    - settings / router / supervisor / debug 输出都使用此枚举
    """
    CHEAP = "cheap"
    STANDARD = "standard"
    TOP = "top"
    
    @classmethod
    def normalize(cls, tier: str) -> "ModelTier":
        """
        标准化档位名称
        
        兼容旧命名：
        - fast -> cheap
        - premium -> top
        """
        tier_map = {
            "cheap": cls.CHEAP,
            "fast": cls.CHEAP,
            "standard": cls.STANDARD,
            "top": cls.TOP,
            "premium": cls.TOP,
        }
        return tier_map.get(tier.lower(), cls.STANDARD)


class ModelRouter:
    """
    模型路由器 - 严格路由器
    
    第三次整改：
    - 只做四件事：register / get_llm_for_tier / has_tier / validate_registry
    - 启动时必须校验 cheap/standard/top 都已注册
    - 未注册时抛出异常而非静默返回 None
    - default 必须指向一个明确 tier
    
    管理不同档位的 LLM 实例：
    - cheap: 快速、低成本
    - standard: 标准能力
    - top: 高级能力
    """
    
    REQUIRED_TIERS = ["cheap", "standard", "top"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, strict_mode: bool = True):
        self.config = config or {}
        self._models: Dict[str, Any] = {}
        self._default_tier: str = "standard"
        self._strict_mode = strict_mode
    
    def register(self, tier: str, model: Any) -> None:
        """
        注册模型
        
        Args:
            tier: 档位名称 (cheap/standard/top)
            model: LLM 实例
        """
        normalized_tier = ModelTier.normalize(tier).value
        self._models[normalized_tier] = model
        logger.info(f"模型注册: {tier} -> {normalized_tier}")
    
    def set_default_tier(self, tier: str) -> None:
        """
        设置默认档位
        
        Args:
            tier: 档位名称
        """
        normalized = ModelTier.normalize(tier).value
        if normalized not in self._models:
            raise ValueError(f"无法设置默认档位: {tier} 未注册")
        self._default_tier = normalized
        logger.info(f"默认档位设置为: {self._default_tier}")
    
    def get_cheap_llm(self) -> Any:
        """获取低成本模型"""
        return self._get_tier_llm("cheap")
    
    def get_standard_llm(self) -> Any:
        """获取标准模型"""
        return self._get_tier_llm("standard")
    
    def get_top_llm(self) -> Any:
        """获取高级模型"""
        return self._get_tier_llm("top")
    
    def get_llm_for_tier(self, tier: str) -> Any:
        """
        根据档位获取模型
        
        第三次整改：严格模式，未注册时抛出异常
        
        Args:
            tier: 档位名称，支持：
                - cheap / fast: 低成本模型
                - standard: 标准模型
                - top / premium: 高级模型
        
        Returns:
            对应档位的 LLM 实例
            
        Raises:
            ValueError: 档位未注册且严格模式开启
        """
        normalized = ModelTier.normalize(tier)
        
        tier_getters = {
            ModelTier.CHEAP: self.get_cheap_llm,
            ModelTier.STANDARD: self.get_standard_llm,
            ModelTier.TOP: self.get_top_llm,
        }
        
        getter = tier_getters.get(normalized, self.get_standard_llm)
        return getter()
    
    def get_model_for_tier(self, tier: str) -> Any:
        """
        根据档位获取模型（兼容别名）
        
        Args:
            tier: 档位名称
            
        Returns:
            对应档位的 LLM 实例
        """
        return self.get_llm_for_tier(tier)
    
    def has_tier(self, tier: str) -> bool:
        """
        检查档位是否已注册
        
        第三次整改新增方法。
        
        Args:
            tier: 档位名称
            
        Returns:
            是否已注册
        """
        normalized = ModelTier.normalize(tier).value
        return normalized in self._models
    
    def validate_registry(self) -> Tuple[bool, List[str]]:
        """
        校验注册状态
        
        第三次整改新增方法。
        检查 cheap/standard/top 是否都已注册，default 是否指向有效 tier。
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        for tier in self.REQUIRED_TIERS:
            if tier not in self._models:
                errors.append(f"档位 {tier} 未注册")
        
        if self._default_tier not in self._models:
            errors.append(f"默认档位 {self._default_tier} 未注册")
        
        return len(errors) == 0, errors
    
    def validate_registry_strict(self) -> None:
        """
        严格校验注册状态
        
        第三次整改新增方法。
        校验失败时抛出异常。
        
        Raises:
            RuntimeError: 注册校验失败
        """
        is_valid, errors = self.validate_registry()
        if not is_valid:
            raise RuntimeError(
                "ModelRouter 注册校验失败:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        logger.info("ModelRouter 注册校验通过")
    
    def _get_tier_llm(self, tier: str) -> Any:
        """
        获取指定档位的 LLM
        
        Args:
            tier: 档位名称
            
        Returns:
            LLM 实例
            
        Raises:
            ValueError: 档位未注册且严格模式开启
        """
        if tier in self._models:
            return self._models[tier]
        
        if self._strict_mode:
            raise ValueError(f"档位 {tier} 未注册（严格模式）")
        
        if self._default_tier in self._models:
            logger.warning(f"档位 {tier} 未注册，回退到默认档位 {self._default_tier}")
            return self._models[self._default_tier]
        
        if "standard" in self._models:
            logger.warning(f"档位 {tier} 未注册，回退到 standard")
            return self._models["standard"]
        
        raise ValueError(f"档位 {tier} 未注册，且没有可用的回退档位")
    
    def list_registered_tiers(self) -> list:
        """列出已注册的档位"""
        return list(self._models.keys())
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        获取注册状态
        
        第三次整改新增方法。
        用于 debug 输出。
        
        Returns:
            注册状态字典
        """
        return {
            "registered_tiers": self.list_registered_tiers(),
            "default_tier": self._default_tier,
            "required_tiers": self.REQUIRED_TIERS,
            "missing_tiers": [t for t in self.REQUIRED_TIERS if t not in self._models],
            "strict_mode": self._strict_mode
        }
