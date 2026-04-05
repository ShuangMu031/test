"""
上下文层记忆

V9 三层记忆 - 第三层

职责：
- 最近几轮对话
- 当前会话上下文
- 临时印象
- 最近动作轨迹

特点：
- 可截断
- 可摘要
- 强依赖 token/窗口控制
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WorkingMemoryType(Enum):
    """工作记忆类型"""
    DIALOGUE = "dialogue"
    IMPRESSION = "impression"
    ACTION = "action"
    CONTEXT = "context"


@dataclass
class WorkingMemoryEntry:
    """工作记忆条目"""
    entry_id: str
    memory_type: WorkingMemoryType
    content: str
    role: str = "user"
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0
    importance: float = 0.3
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
            "importance": self.importance
        }


class WorkingMemoryService:
    """
    工作记忆服务
    
    管理角色的短期上下文记忆
    
    V10 新增：
    - pending_promises: 待跟进承诺列表
    """
    
    def __init__(self, max_entries: int = 50, max_tokens: int = 4000):
        self._entries: List[WorkingMemoryEntry] = []
        self._max_entries = max_entries
        self._max_tokens = max_tokens
        self._current_tokens = 0
        self._pending_promises: List[Dict[str, Any]] = []
    
    def add_entry(
        self,
        memory_type: WorkingMemoryType,
        content: str,
        role: str = "user",
        token_count: int = 0,
        importance: float = 0.3
    ) -> WorkingMemoryEntry:
        """添加条目"""
        entry_id = f"work_{datetime.now().timestamp()}"
        entry = WorkingMemoryEntry(
            entry_id=entry_id,
            memory_type=memory_type,
            content=content,
            role=role,
            token_count=token_count or len(content.split()),
            importance=importance
        )
        self._entries.append(entry)
        self._current_tokens += entry.token_count
        self._enforce_limits()
        return entry
    
    def add_dialogue(self, role: str, content: str) -> WorkingMemoryEntry:
        """添加对话"""
        return self.add_entry(
            memory_type=WorkingMemoryType.DIALOGUE,
            content=content,
            role=role
        )
    
    def get_context_window(self, max_tokens: int = None) -> List[WorkingMemoryEntry]:
        """获取上下文窗口"""
        max_tokens = max_tokens or self._max_tokens
        result = []
        total = 0
        
        for entry in reversed(self._entries):
            if total + entry.token_count > max_tokens:
                break
            result.append(entry)
            total += entry.token_count
        
        return list(reversed(result))
    
    def get_dialogue_history(self, limit: int = 10) -> List[WorkingMemoryEntry]:
        """获取对话历史"""
        dialogues = [e for e in self._entries if e.memory_type == WorkingMemoryType.DIALOGUE]
        return dialogues[-limit:]
    
    def summarize(self) -> str:
        """生成摘要"""
        if not self._entries:
            return ""
        
        dialogues = self.get_dialogue_history()
        summary_parts = []
        
        for entry in dialogues:
            prefix = "用户" if entry.role == "user" else "AI"
            summary_parts.append(f"{prefix}: {entry.content[:100]}")
        
        return "\n".join(summary_parts)
    
    def clear(self) -> None:
        """清空工作记忆"""
        self._entries.clear()
        self._current_tokens = 0
    
    def _enforce_limits(self) -> None:
        """执行限制"""
        while len(self._entries) > self._max_entries:
            removed = self._entries.pop(0)
            self._current_tokens -= removed.token_count
        
        while self._current_tokens > self._max_tokens and self._entries:
            removed = self._entries.pop(0)
            self._current_tokens -= removed.token_count
    
    def to_prompt_context(self, max_tokens: int = 2000) -> str:
        """生成 Prompt 上下文"""
        entries = self.get_context_window(max_tokens)
        if not entries:
            return ""
        
        parts = ["对话上下文:"]
        for entry in entries:
            if entry.memory_type == WorkingMemoryType.DIALOGUE:
                prefix = "用户" if entry.role == "user" else "AI"
                parts.append(f"{prefix}: {entry.content}")
        
        return "\n".join(parts)
    
    def push_user_input(self, content: str) -> WorkingMemoryEntry:
        """推送用户输入（V9 主链接口）"""
        return self.add_dialogue(role="user", content=content)
    
    def push_assistant_reply(self, content: str) -> WorkingMemoryEntry:
        """推送助手回复（V9 主链接口）"""
        return self.add_dialogue(role="assistant", content=content)
    
    def get_context(self, max_tokens: int = None) -> List[Dict[str, Any]]:
        """获取上下文（V9 主链接口）"""
        entries = self.get_context_window(max_tokens or self._max_tokens)
        return [e.to_dict() for e in entries]
    
    def get_all_entries(self) -> List[WorkingMemoryEntry]:
        """获取所有条目"""
        return list(self._entries)
    
    def get_recent_entries(self, limit: int = 10) -> List[WorkingMemoryEntry]:
        """
        获取最近条目
        
        V9 修复：添加方法供 MemoryFacade 使用
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最近的条目列表
        """
        return self._entries[-limit:] if self._entries else []
    
    def get_token_count(self) -> int:
        """获取当前 token 数"""
        return self._current_tokens
    
    def add_pending_promise(self, content: str) -> None:
        """添加待跟进承诺"""
        self._pending_promises.append({
            "content": content,
            "created_at": datetime.now().isoformat()
        })
    
    def get_pending_promises(self) -> List[str]:
        """获取待跟进承诺内容列表"""
        return [p.get("content", "") for p in self._pending_promises if p.get("content")]
    
    def clear_pending_promise(self, content: str) -> bool:
        """清除指定的待跟进承诺"""
        for i, p in enumerate(self._pending_promises):
            if p.get("content") == content:
                self._pending_promises.pop(i)
                return True
        return False
    
    def get_pending_promises_count(self) -> int:
        """获取待跟进承诺数量"""
        return len(self._pending_promises)
