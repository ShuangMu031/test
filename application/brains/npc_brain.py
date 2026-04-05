"""
NPC 脑

V9 改版：NPC 交互判断

改进：
1. 接入 npc_manager
2. 使用 npc_manager 获取 NPC 信息
3. 增强对 NPC 的判断逻辑
4. 支持三层记忆上下文
"""

from typing import Any, Dict, List, Optional
import logging

from .base import BaseBrain
from application.contracts import NPCInteractionHint

logger = logging.getLogger(__name__)


class NPCBrain(BaseBrain):
    """
    NPC 脑
    
    V9 职责：
    1. 判断是否需要 NPC 介入
    2. 选择合适的 NPC
    3. 提供对话提示
    4. 接入 npc_manager 获取 NPC 信息
    """
    
    NPC_KEYWORDS = {
        "小明": ["小明", "明哥"],
        "小红": ["小红", "红姐"],
        "老师": ["老师", "教授"]
    }
    
    def __init__(self, llm=None, npc_manager=None):
        self.llm = llm
        self.npc_manager = npc_manager
    
    @property
    def name(self) -> str:
        return "npc"
    
    async def process(self, context: Any) -> NPCInteractionHint:
        """处理 NPC"""
        user_input = context.user_input
        nearby_npcs = getattr(context, "nearby_npcs", [])
        
        npc_id = self._detect_npc_mention(user_input)
        
        if self.npc_manager and not nearby_npcs:
            nearby_npcs = self._get_nearby_npcs_from_manager(context)
        
        should_involve = self._should_involve(user_input, nearby_npcs, npc_id)
        
        intervention_type = self._determine_intervention(user_input)
        
        dialogue_hint = self._generate_dialogue_hint(user_input, npc_id, nearby_npcs)
        
        npc_info = self._get_npc_info(npc_id) if npc_id else None
        
        context.record_telemetry(
            "npc",
            should_involve_npc=should_involve,
            npc_id=npc_id or "",
            intervention_type=intervention_type,
            nearby_npcs_count=len(nearby_npcs)
        )
        
        actions = []
        interactions = []
        
        if npc_id:
            actions.append(f"检测到 NPC 提及: {npc_id}")
            interactions.append(f"→ npc_manager.get_npc_info({npc_id})")
        
        if nearby_npcs:
            actions.append(f"附近有 {len(nearby_npcs)} 个 NPC")
        
        if should_involve:
            actions.append(f"判断需要 NPC 介入，类型: {intervention_type}")
        
        context.record_monologue(
            "npc",
            monologue=f"NPC 分析: 检测到={npc_id or '无'}, 需要介入={should_involve}, 类型={intervention_type}",
            actions=actions,
            interactions=interactions
        )
        
        return NPCInteractionHint(
            should_involve_npc=should_involve,
            npc_id=npc_id,
            intervention_type=intervention_type,
            dialogue_hint=dialogue_hint,
            npc_info=npc_info
        )
    
    def _get_nearby_npcs_from_manager(self, context: Any) -> List[Any]:
        """从 npc_manager 获取附近 NPC"""
        if not self.npc_manager:
            return []
        
        try:
            if hasattr(self.npc_manager, "get_nearby_npcs"):
                location = getattr(context, "current_location", None)
                if location:
                    return self.npc_manager.get_nearby_npcs(location)
            
            if hasattr(self.npc_manager, "get_active_npcs"):
                return self.npc_manager.get_active_npcs()
        except Exception as e:
            logger.warning(f"从 npc_manager 获取附近 NPC 失败: {e}")
        
        return []
    
    def _get_npc_info(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """获取 NPC 信息"""
        if not self.npc_manager or not npc_id:
            return None
        
        try:
            if hasattr(self.npc_manager, "get_npc_info"):
                return self.npc_manager.get_npc_info(npc_id)
            
            if hasattr(self.npc_manager, "get_npc"):
                npc = self.npc_manager.get_npc(npc_id)
                if npc:
                    return {
                        "id": getattr(npc, "id", npc_id),
                        "name": getattr(npc, "name", npc_id),
                        "personality": getattr(npc, "personality", ""),
                        "relationship": getattr(npc, "relationship", "neutral")
                    }
        except Exception as e:
            logger.warning(f"获取 NPC 信息失败: {e}")
        
        return None
    
    def _detect_npc_mention(self, text: str) -> Optional[str]:
        """检测 NPC 提及"""
        for npc_id, keywords in self.NPC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return npc_id
        
        if self.npc_manager and hasattr(self.npc_manager, "get_all_npc_ids"):
            try:
                all_npc_ids = self.npc_manager.get_all_npc_ids()
                for npc_id in all_npc_ids:
                    npc_info = self._get_npc_info(npc_id)
                    if npc_info:
                        name = npc_info.get("name", "")
                        if name and name in text:
                            return npc_id
            except Exception as e:
                logger.debug(f"从 npc_manager 检测 NPC 提及失败: {e}")
        
        return None
    
    def _should_involve(
        self,
        text: str,
        nearby_npcs: List[Any],
        npc_id: Optional[str]
    ) -> bool:
        """判断是否需要 NPC 介入"""
        if npc_id:
            return True
        
        if nearby_npcs and any(k in text for k in ["一起", "我们", "咱们"]):
            return True
        
        if any(k in text for k in ["找人", "有人", "谁在"]):
            return True
        
        return False
    
    def _determine_intervention(self, text: str) -> str:
        """确定介入类型"""
        if any(k in text for k in ["帮忙", "帮助", "协助"]):
            return "assist"
        elif any(k in text for k in ["聊天", "说话", "聊聊"]):
            return "chat"
        elif any(k in text for k in ["一起", "我们"]):
            return "join"
        elif any(k in text for k in ["找人", "有人"]):
            return "search"
        else:
            return "none"
    
    def _generate_dialogue_hint(
        self,
        text: str,
        npc_id: Optional[str],
        nearby_npcs: List[Any]
    ) -> str:
        """生成对话提示"""
        if npc_id:
            npc_info = self._get_npc_info(npc_id)
            if npc_info:
                name = npc_info.get("name", npc_id)
                relationship = npc_info.get("relationship", "neutral")
                return f"用户提到了 {name}（关系: {relationship}）"
            return f"用户提到了 {npc_id}"
        
        if nearby_npcs:
            npc_names = []
            for npc in nearby_npcs[:3]:
                if isinstance(npc, dict):
                    npc_names.append(npc.get("name", str(npc)))
                else:
                    npc_names.append(getattr(npc, "name", str(npc)))
            
            if npc_names:
                return f"附近有: {', '.join(npc_names)}"
        
        return ""
