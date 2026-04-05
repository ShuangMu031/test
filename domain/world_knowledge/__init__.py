"""
世界知识模块

V9 第五批新增：虚拟世界内容管理

核心组件：
- models: 世界内容模型
- translator: 现实到世界转译器
- repository: 世界知识仓库
- service: 世界知识服务
"""

from domain.world_knowledge.models import (
    WorldContentType,
    WorldTopicTag,
    ImpactLevel,
    WorldContentImpact,
    WorldContentItem,
    WorldKnowledgeQuery
)
from domain.world_knowledge.translator import RealityToWorldTranslator
from domain.world_knowledge.repository import WorldKnowledgeRepository
from domain.world_knowledge.service import WorldKnowledgeService

__all__ = [
    "WorldContentType",
    "WorldTopicTag",
    "ImpactLevel",
    "WorldContentImpact",
    "WorldContentItem",
    "WorldKnowledgeQuery",
    "RealityToWorldTranslator",
    "WorldKnowledgeRepository",
    "WorldKnowledgeService"
]
