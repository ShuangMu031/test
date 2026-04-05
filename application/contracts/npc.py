"""
NPC 相关 Schema

V6 统一字段体系：
- should_involve_npc: 是否涉及 NPC
- npc_id: NPC ID
- intervention_type: 介入类型
- dialogue_hint: 对话提示

第二次整改：
- 补充 from_dict() 方法

V9 修复：
- 添加 npc_info 字段支持 NPC 可视化
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class NPCInteractionHint:
    """
    NPC 交互提示
    
    来自 NPCBrain 的输出，包含 NPC 介入建议。
    
    统一字段说明：
    - should_involve_npc: 是否应该涉及 NPC
    - npc_id: NPC 标识符
    - intervention_type: 介入类型（passive_mention/active_dialogue/quest_trigger）
    - dialogue_hint: 对话提示
    - npc_info: NPC 详细信息（V9 新增，用于可视化）
    """
    should_involve_npc: bool
    npc_id: str
    intervention_type: str
    dialogue_hint: str
    npc_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_involve_npc": self.should_involve_npc,
            "npc_id": self.npc_id,
            "intervention_type": self.intervention_type,
            "dialogue_hint": self.dialogue_hint,
            "npc_info": self.npc_info
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPCInteractionHint":
        return cls(
            should_involve_npc=data.get("should_involve_npc", False),
            npc_id=data.get("npc_id", ""),
            intervention_type=data.get("intervention_type", "passive_mention"),
            dialogue_hint=data.get("dialogue_hint", ""),
            npc_info=data.get("npc_info")
        )
