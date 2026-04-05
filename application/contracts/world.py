"""
世界相关 Schema

V6 统一字段体系：
- WorldUpdateProposal: 世界更新提案
- WorldContentProposal: 世界内容提案
- WorldBrainOutput: 世界脑输出（聚合结构）

第二次整改：
- 补充 from_dict() 方法
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class WorldUpdateProposal:
    """
    世界更新提案
    
    来自 WorldBrain 的输出，包含世界状态更新建议。
    
    统一字段说明：
    - time_advance_minutes: 时间推进分钟数
    - suggested_location: 建议位置
    - npc_context_hint: NPC 上下文提示
    - world_commit_needed: 是否需要世界提交
    - reasoning: 推理说明
    - change_trigger: 变化触发器
    - confidence: 置信度（0-1）
    """
    time_advance_minutes: int
    suggested_location: Optional[str]
    npc_context_hint: str
    world_commit_needed: bool
    reasoning: str
    change_trigger: str = "none"
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_advance_minutes": self.time_advance_minutes,
            "suggested_location": self.suggested_location,
            "npc_context_hint": self.npc_context_hint,
            "world_commit_needed": self.world_commit_needed,
            "reasoning": self.reasoning,
            "change_trigger": self.change_trigger,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldUpdateProposal":
        return cls(
            time_advance_minutes=data.get("time_advance_minutes", 0),
            suggested_location=data.get("suggested_location"),
            npc_context_hint=data.get("npc_context_hint", ""),
            world_commit_needed=data.get("world_commit_needed", False),
            reasoning=data.get("reasoning", ""),
            change_trigger=data.get("change_trigger", "none"),
            confidence=data.get("confidence", 0.5)
        )


@dataclass
class WorldContentProposal:
    """
    世界内容提案
    
    来自 WorldBrain 的输出，包含世界内容查询建议。
    
    统一字段说明：
    - user_is_asking_world_content: 用户是否在询问世界内容
    - content_types_needed: 需要的内容类型列表
    - content_category: 内容类别
    - retrieval_query: 检索查询
    """
    user_is_asking_world_content: bool
    content_types_needed: List[str]
    content_category: str
    retrieval_query: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_is_asking_world_content": self.user_is_asking_world_content,
            "content_types_needed": self.content_types_needed,
            "content_category": self.content_category,
            "retrieval_query": self.retrieval_query
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldContentProposal":
        return cls(
            user_is_asking_world_content=data.get("user_is_asking_world_content", False),
            content_types_needed=data.get("content_types_needed", []),
            content_category=data.get("content_category", "general"),
            retrieval_query=data.get("retrieval_query", "")
        )


@dataclass
class WorldBrainOutput:
    """
    世界脑输出
    
    单一返回结构，包含：
    - world_update_proposal: 世界更新提案
    - world_content_proposal: 世界内容提案（可选）
    - should_apply_update: 是否应该应用更新
    - should_read_world_content: 是否应该读取世界内容
    
    第二次整改：
    - 补充 from_dict() 方法
    """
    world_update_proposal: WorldUpdateProposal
    world_content_proposal: Optional[WorldContentProposal] = None
    should_apply_update: bool = False
    should_read_world_content: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "world_update_proposal": self.world_update_proposal.to_dict(),
            "world_content_proposal": self.world_content_proposal.to_dict() if self.world_content_proposal else None,
            "should_apply_update": self.should_apply_update,
            "should_read_world_content": self.should_read_world_content
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldBrainOutput":
        world_update_proposal = None
        if data.get("world_update_proposal"):
            world_update_proposal = WorldUpdateProposal.from_dict(data["world_update_proposal"])
        
        world_content_proposal = None
        if data.get("world_content_proposal"):
            world_content_proposal = WorldContentProposal.from_dict(data["world_content_proposal"])
        
        return cls(
            world_update_proposal=world_update_proposal,
            world_content_proposal=world_content_proposal,
            should_apply_update=data.get("should_apply_update", False),
            should_read_world_content=data.get("should_read_world_content", False)
        )
