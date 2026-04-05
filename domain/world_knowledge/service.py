"""
世界知识服务

V9 第五批新增：给 orchestrator / executor 用的服务门面

职责：
1. should_refresh(): 判断是否需要刷新
2. refresh_from_reality(signals): 从现实素材刷新
3. get_latest_content(limit): 获取最新内容
4. search_relevant_content(query) / get_content_by_types(types): 检索内容
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from application.contracts.reality import RealitySignal
from domain.world_knowledge.models import (
    WorldContentItem,
    WorldContentType,
    WorldTopicTag,
    WorldKnowledgeQuery
)
from domain.world_knowledge.translator import RealityToWorldTranslator
from domain.world_knowledge.repository import WorldKnowledgeRepository

logger = logging.getLogger(__name__)


class WorldKnowledgeService:
    """
    世界知识服务
    
    提供世界内容的获取和管理功能
    """
    
    def __init__(
        self,
        translator: Optional[RealityToWorldTranslator] = None,
        repository: Optional[WorldKnowledgeRepository] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        self.translator = translator or RealityToWorldTranslator(self.config.get("translator", {}))
        self.repository = repository or WorldKnowledgeRepository(self.config.get("repository", {}))
        
        self._last_refresh_time: Optional[float] = None
        self._refresh_interval = self.config.get("refresh_interval", 3600)
        
        self._stats = {
            "total_refreshes": 0,
            "total_items_created": 0,
            "total_queries": 0
        }
    
    def should_refresh(self) -> bool:
        """
        判断是否需要刷新
        
        Returns:
            是否需要刷新
        """
        if self._last_refresh_time is None:
            return True
        
        elapsed = datetime.now().timestamp() - self._last_refresh_time
        return elapsed >= self._refresh_interval
    
    async def refresh_from_reality(
        self,
        signals: List[RealitySignal]
    ) -> int:
        """
        从现实素材刷新世界内容
        
        Args:
            signals: 现实素材列表
            
        Returns:
            新增的世界内容数量
        """
        if not signals:
            return 0
        
        logger.info(f"开始刷新世界内容，收到 {len(signals)} 个现实素材")
        
        items = self.translator.translate_batch(signals)
        
        added_count = self.repository.add_items(items)
        
        self._last_refresh_time = datetime.now().timestamp()
        
        self._stats["total_refreshes"] += 1
        self._stats["total_items_created"] += len(items)
        
        logger.info(f"世界内容刷新完成，新增 {added_count} 条内容")
        
        return added_count
    
    def get_latest_content(self, limit: int = 5) -> List[WorldContentItem]:
        """
        获取最新内容
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最新的世界内容列表
        """
        self._stats["total_queries"] += 1
        return self.repository.get_latest(limit)
    
    def get_content_by_types(
        self,
        types: List[str],
        limit: int = 5
    ) -> List[WorldContentItem]:
        """
        按类型获取内容
        
        Args:
            types: 内容类型字符串列表
            limit: 返回数量限制
            
        Returns:
            匹配的世界内容列表
        """
        self._stats["total_queries"] += 1
        
        content_types = []
        for t in types:
            try:
                content_types.append(WorldContentType(t))
            except ValueError:
                logger.warning(f"未知的内容类型: {t}")
        
        if not content_types:
            return []
        
        return self.repository.get_by_types(content_types, limit)
    
    def search_relevant_content(
        self,
        query: str,
        limit: int = 5
    ) -> List[WorldContentItem]:
        """
        搜索相关内容
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            匹配的世界内容列表
        """
        self._stats["total_queries"] += 1
        return self.repository.search(query, limit)
    
    def query(self, query_obj: WorldKnowledgeQuery) -> List[WorldContentItem]:
        """
        使用查询对象查询
        
        Args:
            query_obj: 查询对象
            
        Returns:
            匹配的世界内容列表
        """
        self._stats["total_queries"] += 1
        return self.repository.query(query_obj)
    
    def get_content_for_prompt(
        self,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 3
    ) -> str:
        """
        获取用于 prompt 的世界内容文本
        
        Args:
            context: 上下文信息
            limit: 返回数量限制
            
        Returns:
            格式化的世界内容文本
        """
        items = self.get_latest_content(limit)
        
        if not items:
            return "暂无最新的世界动态。"
        
        lines = ["## 世界动态"]
        for item in items:
            lines.append(f"- {item.world_text or item.content}")
        
        return "\n".join(lines)
    
    def get_content_summary(self) -> Dict[str, Any]:
        """
        获取内容摘要
        
        Returns:
            内容摘要信息
        """
        latest = self.get_latest_content(5)
        
        return {
            "total_items": len(self.repository._items),
            "latest_count": len(latest),
            "latest_titles": [item.title for item in latest],
            "last_refresh": self._last_refresh_time,
            "stats": self._stats,
            "repository_stats": self.repository.get_stats()
        }
    
    def expire_old_content(self) -> int:
        """
        过期旧内容
        
        Returns:
            过期的数量
        """
        return self.repository.expire_old_items()
    
    def clear(self) -> None:
        """清空所有内容"""
        self.repository.clear()
        self._last_refresh_time = None
        logger.info("世界知识服务已清空")
    
    def add_content_directly(
        self,
        item: WorldContentItem
    ) -> bool:
        """
        直接添加世界内容
        
        Args:
            item: 世界内容项
            
        Returns:
            是否添加成功
        """
        count = self.repository.add_items([item])
        return count > 0
