"""
记忆相关 Schema

V9 改版：三层记忆路由决策

从"单条存储判断"改成"三层记忆路由决策"：
- write_working: 是否写入 working memory
- write_episodic: 是否升级到 episodic memory
- write_core: 是否写入 core memory
- should_consolidate: 是否触发 consolidation
- working_payload: working 层的 payload
- episodic_payload: episodic 层的 payload
- core_payload: core 层的 payload
- importance: 重要性（0-1）
- emotional_impact: 情感影响（0-1）
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class MemoryDecision:
    """
    记忆决策 V9
    
    三层记忆路由决策器的输出。
    
    不再只是"要不要存一条"，而是：
    - working: 是否写入工作记忆（最近对话）
    - episodic: 是否升级到事件记忆（重大事件）
    - core: 是否写入核心记忆（身份/偏好）
    - consolidation: 是否触发记忆固化
    
    字段说明：
    - write_working: 是否写入 working memory
    - write_episodic: 是否升级到 episodic memory
    - write_core: 是否写入 core memory
    - should_consolidate: 是否触发 consolidation
    - working_payload: working 层的 payload
    - episodic_payload: episodic 层的 payload
    - core_payload: core 层的 payload
    - importance: 重要性（0-1）
    - emotional_impact: 情感影响（0-1）
    - reasoning: 推理说明
    """
    write_working: bool = True
    write_episodic: bool = False
    write_core: bool = False
    should_consolidate: bool = False
    
    working_payload: Dict[str, Any] = field(default_factory=dict)
    episodic_payload: Dict[str, Any] = field(default_factory=dict)
    core_payload: Optional[Dict[str, Any]] = None
    
    importance: float = 0.5
    emotional_impact: float = 0.0
    
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "write_working": self.write_working,
            "write_episodic": self.write_episodic,
            "write_core": self.write_core,
            "should_consolidate": self.should_consolidate,
            "working_payload": self.working_payload,
            "episodic_payload": self.episodic_payload,
            "core_payload": self.core_payload,
            "importance": self.importance,
            "emotional_impact": self.emotional_impact,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryDecision":
        return cls(
            write_working=data.get("write_working", True),
            write_episodic=data.get("write_episodic", False),
            write_core=data.get("write_core", False),
            should_consolidate=data.get("should_consolidate", False),
            working_payload=data.get("working_payload", {}),
            episodic_payload=data.get("episodic_payload", {}),
            core_payload=data.get("core_payload"),
            importance=data.get("importance", 0.5),
            emotional_impact=data.get("emotional_impact", 0.0),
            reasoning=data.get("reasoning", "")
        )
