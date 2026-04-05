"""
原生层记忆

V9 三层记忆 - 第一层

职责：
- 角色身份（我是谁）
- 过去经历（我经历过什么）
- 固定偏好（我喜欢什么）
- 关系底稿（我和谁什么关系）
- 世界常识中的"我是谁"

特点：
- 必须保留
- 不做普通遗忘
- 只能低频修改
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CoreMemoryEntry:
    """原生记忆条目"""
    key: str
    value: str
    category: str = "identity"
    importance: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat()
        }


class CoreMemoryService:
    """
    原生记忆服务
    
    管理角色的核心身份记忆
    """
    
    def __init__(self):
        self._entries: Dict[str, CoreMemoryEntry] = {}
    
    def initialize_persona(self, persona_data: Dict[str, Any]) -> None:
        """初始化角色设定"""
        for key, value in persona_data.items():
            if isinstance(value, dict):
                self.set(
                    key=key,
                    value=value.get("value", str(value)),
                    category=value.get("category", "identity"),
                    importance=value.get("importance", 1.0)
                )
            else:
                self.set(key=key, value=str(value))
    
    def get(self, key: str) -> Optional[str]:
        """获取记忆值"""
        entry = self._entries.get(key)
        if entry:
            entry.last_accessed = datetime.now()
            return entry.value
        return None
    
    def set(self, key: str, value: str, category: str = "identity", importance: float = 1.0) -> None:
        """设置记忆"""
        self._entries[key] = CoreMemoryEntry(
            key=key,
            value=value,
            category=category,
            importance=importance
        )
    
    def get_identity(self) -> str:
        """获取身份描述"""
        return self.get("identity") or ""
    
    def get_relationships(self) -> List[CoreMemoryEntry]:
        """获取关系底稿"""
        return [e for e in self._entries.values() if e.category == "relationship"]
    
    def get_preferences(self) -> List[CoreMemoryEntry]:
        """获取偏好"""
        return [e for e in self._entries.values() if e.category == "preference"]
    
    def get_all(self) -> Dict[str, CoreMemoryEntry]:
        """获取所有记忆"""
        return self._entries.copy()
    
    def to_prompt_context(self) -> str:
        """生成 Prompt 上下文"""
        parts = []
        
        identity = self.get_identity()
        if identity:
            parts.append(f"身份: {identity}")
        
        relationships = self.get_relationships()
        if relationships:
            rel_str = ", ".join([f"{r.key}: {r.value}" for r in relationships])
            parts.append(f"关系: {rel_str}")
        
        preferences = self.get_preferences()
        if preferences:
            pref_str = ", ".join([f"{p.key}: {p.value}" for p in preferences])
            parts.append(f"偏好: {pref_str}")
        
        return "\n".join(parts)
    
    def update_identity(self, identity: str) -> None:
        """更新身份（V9 主链接口）"""
        self.set(key="identity", value=identity, category="identity", importance=1.0)
    
    def update_preference(self, key: str, value: str) -> None:
        """更新偏好（V9 主链接口）"""
        self.set(key=key, value=value, category="preference", importance=0.8)
    
    def update_relationship(self, key: str, value: str) -> None:
        """更新关系（V9 主链接口）"""
        self.set(key=key, value=value, category="relationship", importance=0.9)
    
    def get_persona(self) -> Dict[str, Any]:
        """获取完整人设（V9 主链接口）"""
        return {
            "identity": self.get_identity(),
            "relationships": [e.to_dict() for e in self.get_relationships()],
            "preferences": [e.to_dict() for e in self.get_preferences()],
            "all_entries": {k: v.to_dict() for k, v in self._entries.items()}
        }
    
    def get_all_entries(self) -> List[CoreMemoryEntry]:
        """获取所有条目"""
        return list(self._entries.values())
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索核心记忆
        
        V9 修复：添加搜索方法供 MemoryService 使用
        
        Args:
            query: 查询文本
            
        Returns:
            匹配的记忆列表
        """
        query_lower = query.lower()
        results = []
        
        for entry in self._entries.values():
            if query_lower in entry.key.lower() or query_lower in entry.value.lower():
                results.append({
                    "key": entry.key,
                    "value": entry.value,
                    "category": entry.category,
                    "importance": entry.importance
                })
        
        return results
    
    def set_entry(self, key: str, value: str, category: str = "identity") -> None:
        """设置条目（V9 主链接口别名）"""
        self.set(key=key, value=value, category=category)
