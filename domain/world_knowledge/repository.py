"""
世界知识仓库

V9 第五批新增：存放已生成的世界内容

职责：
- 去重
- 过期
- 最近内容窗口
- 标签检索
- 类型检索
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from domain.world_knowledge.models import (
    WorldContentItem,
    WorldContentType,
    WorldTopicTag,
    WorldKnowledgeQuery
)

logger = logging.getLogger(__name__)


class WorldKnowledgeRepository:
    """
    世界知识仓库
    
    存储和管理世界内容项
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self._items: Dict[str, WorldContentItem] = {}
        
        self._type_index: Dict[WorldContentType, List[str]] = {
            ct: [] for ct in WorldContentType
        }
        
        self._tag_index: Dict[WorldTopicTag, List[str]] = {
            tag: [] for tag in WorldTopicTag
        }
        
        self._max_items = self.config.get("max_items", 100)
        self._default_expire_hours = self.config.get("default_expire_hours", 48)
        
        self._stats = {
            "total_added": 0,
            "total_expired": 0,
            "total_deduplicated": 0
        }
    
    def add_items(self, items: List[WorldContentItem]) -> int:
        """
        添加世界内容项
        
        Args:
            items: 世界内容项列表
            
        Returns:
            实际添加的数量
        """
        added_count = 0
        
        for item in items:
            if self._add_single_item(item):
                added_count += 1
        
        self._cleanup_if_needed()
        
        return added_count
    
    def _add_single_item(self, item: WorldContentItem) -> bool:
        """添加单个项目"""
        if self._is_duplicate(item):
            self._stats["total_deduplicated"] += 1
            logger.debug(f"重复内容已跳过: {item.id}")
            return False
        
        if item.expires_at is None:
            item.expires_at = datetime.now().timestamp() + self._default_expire_hours * 3600
        
        self._items[item.id] = item
        
        if item.content_type in self._type_index:
            self._type_index[item.content_type].append(item.id)
        
        for tag in item.topic_tags:
            if tag in self._tag_index:
                self._tag_index[tag].append(item.id)
        
        self._stats["total_added"] += 1
        return True
    
    def _is_duplicate(self, item: WorldContentItem) -> bool:
        """检查是否重复"""
        if item.original_signal_id:
            for existing in self._items.values():
                if existing.original_signal_id == item.original_signal_id:
                    return True
        
        for existing in self._items.values():
            if (existing.title == item.title and 
                existing.content_type == item.content_type):
                return True
        
        return False
    
    def get_latest(self, limit: int = 5) -> List[WorldContentItem]:
        """
        获取最新内容
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最新的世界内容项列表
        """
        self._expire_old_items()
        
        sorted_items = sorted(
            self._items.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        
        return sorted_items[:limit]
    
    def get_by_types(
        self,
        types: List[WorldContentType],
        limit: int = 5
    ) -> List[WorldContentItem]:
        """
        按类型获取内容
        
        Args:
            types: 内容类型列表
            limit: 返回数量限制
            
        Returns:
            匹配的世界内容项列表
        """
        self._expire_old_items()
        
        item_ids = set()
        for ct in types:
            item_ids.update(self._type_index.get(ct, []))
        
        items = [self._items[iid] for iid in item_ids if iid in self._items]
        
        sorted_items = sorted(
            items,
            key=lambda x: (x.get_current_importance(), x.created_at),
            reverse=True
        )
        
        return sorted_items[:limit]
    
    def get_by_tags(
        self,
        tags: List[WorldTopicTag],
        limit: int = 5
    ) -> List[WorldContentItem]:
        """
        按标签获取内容
        
        Args:
            tags: 话题标签列表
            limit: 返回数量限制
            
        Returns:
            匹配的世界内容项列表
        """
        self._expire_old_items()
        
        item_ids = set()
        for tag in tags:
            item_ids.update(self._tag_index.get(tag, []))
        
        items = [self._items[iid] for iid in item_ids if iid in self._items]
        
        sorted_items = sorted(
            items,
            key=lambda x: (x.get_current_importance(), x.created_at),
            reverse=True
        )
        
        return sorted_items[:limit]
    
    def search(
        self,
        query: str,
        limit: int = 5
    ) -> List[WorldContentItem]:
        """
        搜索内容
        
        Args:
            query: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            匹配的世界内容项列表
        """
        self._expire_old_items()
        
        query_lower = query.lower()
        
        matches = []
        for item in self._items.values():
            score = self._calculate_match_score(item, query_lower)
            if score > 0:
                matches.append((item, score))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return [item for item, _ in matches[:limit]]
    
    def _calculate_match_score(self, item: WorldContentItem, query: str) -> float:
        """计算匹配分数"""
        score = 0.0
        
        if query in item.title.lower():
            score += 2.0
        
        if query in item.content.lower():
            score += 1.0
        
        if query in item.summary.lower():
            score += 0.5
        
        if query in item.world_text.lower():
            score += 0.5
        
        for tag in item.topic_tags:
            if query in tag.value.lower():
                score += 0.3
        
        score *= item.get_current_importance()
        
        return score
    
    def query(self, query_obj: WorldKnowledgeQuery) -> List[WorldContentItem]:
        """
        使用查询对象查询
        
        Args:
            query_obj: 查询对象
            
        Returns:
            匹配的世界内容项列表
        """
        self._expire_old_items()
        
        candidates = list(self._items.values())
        
        if query_obj.content_types:
            candidates = [
                item for item in candidates
                if item.content_type in query_obj.content_types
            ]
        
        if query_obj.topic_tags:
            candidates = [
                item for item in candidates
                if any(tag in item.topic_tags for tag in query_obj.topic_tags)
            ]
        
        if query_obj.min_importance > 0:
            candidates = [
                item for item in candidates
                if item.get_current_importance() >= query_obj.min_importance
            ]
        
        if query_obj.max_age_hours is not None:
            cutoff = datetime.now().timestamp() - query_obj.max_age_hours * 3600
            candidates = [
                item for item in candidates
                if item.created_at >= cutoff
            ]
        
        if query_obj.query_text:
            query_lower = query_obj.query_text.lower()
            scored = [
                (item, self._calculate_match_score(item, query_lower))
                for item in candidates
            ]
            scored = [(item, score) for item, score in scored if score > 0]
            scored.sort(key=lambda x: x[1], reverse=True)
            candidates = [item for item, _ in scored]
        else:
            candidates.sort(
                key=lambda x: (x.get_current_importance(), x.created_at),
                reverse=True
            )
        
        return candidates[:query_obj.limit]
    
    def expire_old_items(self) -> int:
        """
        过期旧内容
        
        Returns:
            过期的数量
        """
        return self._expire_old_items()
    
    def _expire_old_items(self) -> int:
        """内部过期处理"""
        now = datetime.now().timestamp()
        expired_ids = [
            item_id for item_id, item in self._items.items()
            if item.is_expired()
        ]
        
        for item_id in expired_ids:
            self._remove_item(item_id)
            self._stats["total_expired"] += 1
        
        if expired_ids:
            logger.debug(f"过期了 {len(expired_ids)} 个世界内容项")
        
        return len(expired_ids)
    
    def _remove_item(self, item_id: str) -> None:
        """移除项目"""
        if item_id not in self._items:
            return
        
        item = self._items[item_id]
        
        if item.content_type in self._type_index:
            if item_id in self._type_index[item.content_type]:
                self._type_index[item.content_type].remove(item_id)
        
        for tag in item.topic_tags:
            if tag in self._tag_index:
                if item_id in self._tag_index[tag]:
                    self._tag_index[tag].remove(item_id)
        
        del self._items[item_id]
    
    def _cleanup_if_needed(self) -> None:
        """如果超出限制则清理"""
        if len(self._items) <= self._max_items:
            return
        
        self._expire_old_items()
        
        if len(self._items) <= self._max_items:
            return
        
        sorted_items = sorted(
            self._items.values(),
            key=lambda x: (x.get_current_importance(), x.created_at)
        )
        
        to_remove = len(self._items) - self._max_items
        for item in sorted_items[:to_remove]:
            self._remove_item(item.id)
        
        logger.debug(f"清理了 {to_remove} 个低优先级世界内容项")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "current_items": len(self._items),
            "max_items": self._max_items,
            **self._stats
        }
    
    def clear(self) -> None:
        """清空仓库"""
        self._items.clear()
        for ct in self._type_index:
            self._type_index[ct] = []
        for tag in self._tag_index:
            self._tag_index[tag] = []
        logger.info("世界知识仓库已清空")
