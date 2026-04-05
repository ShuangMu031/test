"""
记忆服务门面

V9 修复：提供统一的记忆服务接口

职责：
- 提供主链调用的统一接口名
- 内部映射到三层记忆（core/episodic/working）
- 不让 orchestrator 直接理解三层记忆细节

V9 第二批修复：
- store_memory() 参数名修正
- store_message() 角色归一化
- get_recent_messages() id字段修正
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from domain.memory.episodic.service import EpisodicEventType
from domain.memory.working.service import WorkingMemoryType

logger = logging.getLogger(__name__)


class MemoryFacade:
    """
    记忆服务门面
    
    提供主链调用的统一接口，内部映射到三层记忆
    
    主链调用接口：
    - store_message(role, content): 存储对话消息
    - get_recent_messages(limit): 获取最近对话
    - retrieve_memories(query, limit): 检索相关记忆
    - store_memory(content, memory_type, tags, importance): 存储记忆
    
    内部映射：
    - 对话消息 -> working memory
    - 事件记忆 -> episodic memory
    - 身份/偏好 -> core memory
    """
    
    def __init__(
        self,
        core_memory=None,
        episodic_memory=None,
        working_memory=None
    ):
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
        
        self._message_counter = 0
    
    def _normalize_role(self, role: str) -> str:
        """
        角色归一化
        
        V9 修复：统一角色名称
        
        Args:
            role: 原始角色名
            
        Returns:
            归一化后的角色名
        """
        if role in ("human", "user"):
            return "user"
        if role in ("assistant", "ai"):
            return "assistant"
        return role
    
    def store_message(self, role: str, content: str) -> Any:
        """
        存储对话消息
        
        Args:
            role: 角色 (human/assistant)
            content: 消息内容
            
        Returns:
            消息对象
        """
        self._message_counter += 1
        message_id = f"msg_{self._message_counter}"
        
        normalized_role = self._normalize_role(role)
        
        if self.working_memory:
            self.working_memory.add_dialogue(normalized_role, content)
        
        class Message:
            def __init__(self, id, role, content):
                self.id = id
                self.role = role
                self.content = content
                self.timestamp = datetime.now().timestamp()
        
        return Message(message_id, normalized_role, content)
    
    def get_recent_messages(self, limit: int = 10) -> List[Any]:
        """
        获取最近对话消息
        
        Args:
            limit: 返回数量限制
            
        Returns:
            消息列表
        """
        if not self.working_memory:
            return []
        
        entries = self.working_memory.get_recent_entries(limit)
        
        messages = []
        for entry in entries:
            class Message:
                def __init__(self, entry):
                    self.id = getattr(entry, 'entry_id', 'unknown')
                    self.role = getattr(entry, 'role', 'unknown')
                    self.content = getattr(entry, 'content', '')
                    self.timestamp = getattr(entry, 'timestamp', 0)
            
            messages.append(Message(entry))
        
        return messages
    
    def retrieve_memories(self, query: str, limit: int = 5) -> List[Any]:
        """
        检索相关记忆
        
        Args:
            query: 查询文本
            limit: 返回数量限制
            
        Returns:
            记忆列表
        """
        memories = []
        
        if self.episodic_memory:
            events = self.episodic_memory.search_events(query, limit)
            for event in events:
                class Memory:
                    def __init__(self, event):
                        self.id = getattr(event, 'id', 'unknown')
                        self.content = getattr(event, 'content', getattr(event, 'summary', ''))
                        self.importance = getattr(event, 'importance', 0.5)
                        self.timestamp = getattr(event, 'timestamp', 0)
                        self.source = 'episodic'
                
                memories.append(Memory(event))
        
        if self.core_memory and len(memories) < limit:
            if hasattr(self.core_memory, 'search'):
                results = self.core_memory.search(query)
                for item in results:
                    if len(memories) >= limit:
                        break
                    
                    class Memory:
                        def __init__(self, item):
                            self.id = item.get('key', 'unknown')
                            self.content = item.get('value', '')
                            self.importance = item.get('importance', 0.8)
                            self.timestamp = 0
                            self.source = 'core'
                    
                    memories.append(Memory(item))
            else:
                all_entries = self.core_memory.get_all() if hasattr(self.core_memory, 'get_all') else []
                for entry in all_entries:
                    if len(memories) >= limit:
                        break
                    
                    if isinstance(entry, dict):
                        value = entry.get('value', '')
                    else:
                        value = str(entry)
                    
                    if query.lower() in value.lower():
                        class Memory:
                            def __init__(self, entry):
                                self.id = entry.get('key', 'unknown') if isinstance(entry, dict) else 'unknown'
                                self.content = value
                                self.importance = 0.8
                                self.timestamp = 0
                                self.source = 'core'
                        
                        memories.append(Memory(entry))
        
        return memories[:limit]
    
    def store_memory(
        self,
        content: str,
        memory_type: str = "general",
        tags: List[str] = None,
        importance: float = 0.5
    ) -> Any:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            tags: 标签列表
            importance: 重要性
            
        Returns:
            记忆对象
        """
        class MemoryResult:
            def __init__(self, content, memory_type):
                self.id = f"mem_{datetime.now().timestamp()}"
                self.content = content
                self.memory_type = memory_type
                self.success = True
        
        if memory_type in ["identity", "preference", "relationship"]:
            if self.core_memory:
                key = tags[0] if tags else memory_type
                self.core_memory.set_entry(key, content, memory_type)
                return MemoryResult(content, memory_type)
        
        if memory_type in ["event", "episodic", "important"]:
            if self.episodic_memory:
                event_type_map = {
                    "event": EpisodicEventType.USER_INTERACTION,
                    "episodic": EpisodicEventType.USER_INTERACTION,
                    "important": EpisodicEventType.EMOTIONAL_PEAK
                }
                self.episodic_memory.add_event(
                    event_type=event_type_map.get(memory_type, EpisodicEventType.USER_INTERACTION),
                    description=content,
                    importance=importance,
                    metadata={"tags": tags or []}
                )
                return MemoryResult(content, memory_type)
        
        if self.working_memory:
            self.working_memory.add_entry(
                memory_type=WorkingMemoryType.CONTEXT,
                content=content,
                role="user",
                importance=importance
            )
            return MemoryResult(content, memory_type)
        
        return MemoryResult(content, memory_type)
    
    def get_context_for_prompt(self) -> str:
        """
        获取用于 prompt 的记忆上下文
        
        Returns:
            格式化的记忆上下文文本
        """
        parts = []
        
        if self.core_memory:
            core_context = self.core_memory.to_prompt_context()
            if core_context:
                parts.append(f"## 核心记忆\n{core_context}")
        
        if self.episodic_memory:
            episodic_context = self.episodic_memory.to_prompt_context()
            if episodic_context:
                parts.append(f"## 事件记忆\n{episodic_context}")
        
        if self.working_memory:
            working_context = self.working_memory.to_prompt_context()
            if working_context:
                parts.append(f"## 工作记忆\n{working_context}")
        
        return "\n\n".join(parts) if parts else "暂无相关记忆。"
    
    def clear_working_memory(self) -> None:
        """清空工作记忆"""
        if self.working_memory:
            self.working_memory.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "core_entries": len(self.core_memory.get_all()) if self.core_memory else 0,
            "episodic_entries": len(self.episodic_memory.get_recent_events(1000)) if self.episodic_memory else 0,
            "working_entries": len(self.working_memory._entries) if self.working_memory else 0,
            "total_messages": self._message_counter
        }
