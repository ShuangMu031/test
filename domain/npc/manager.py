"""
NPC管理器

V9 改版：角色行为与关系变化引擎

========================================
模块边界约束（第四次整改）
========================================

【正确定位】
npc 模块应该是：
> 角色行为与关系变化引擎

【必须保留】
- NPC 状态 (NPC, NPCState)
- NPC 关系 (relationships)
- NPC 对事件的反应
- NPC 行为建议
- NPC 互动候选

【绝对禁止】
- 直接投递正式消息
- 直接决定最终回复文案
- 直接调用 tool
- 直接改 orchestrator phase
- 直接改 world state

【正式落地流程】
NPC 的正式落地流程应该是：
NPC 模块 -> NPCInteractionHint -> ExecutablePlan.npc_actions -> Executor -> Outbound/World

而不是 NPC 模块自己下场讲话。

【输出规范】
输出 NPCInteractionHint，供主链编译和执行。

V9 新增：
- get_nearby_npcs: 获取附近 NPC
- get_npc_info: 获取 NPC 信息
- get_all_npc_ids: 获取所有 NPC ID
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from .models import NPC, NPCState, NPCPersonality

logger = logging.getLogger(__name__)


class NPCManager:
    """
    NPC管理器
    
    V9 核心功能:
    1. 角色管理：创建、更新、删除NPC
    2. 状态追踪：监控NPC的状态和位置
    3. 关系管理：维护NPC之间的关系
    4. 交互调度：协调NPC之间的交互
    5. 主链支持：提供主链需要的方法
    """
    
    def __init__(self):
        self.npcs: Dict[str, NPC] = {}
        
        self.location_npcs: Dict[str, List[str]] = {}
        
        self.interaction_history: List[Dict[str, Any]] = []
        
        self._init_default_npcs()
        
        logger.info("NPCManager initialized")
    
    def _init_default_npcs(self) -> None:
        """初始化默认NPC"""
        default_npcs = [
            {
                "id": "xiaoyu",
                "name": "小雨",
                "personality": NPCPersonality.CARING,
                "description": "温柔体贴的女孩，喜欢帮助别人",
                "location": "宿舍",
                "hobbies": ["阅读", "听音乐", "散步"],
                "skills": ["倾听", "安慰", "建议"]
            },
            {
                "id": "ming",
                "name": "小明",
                "personality": NPCPersonality.OUTGOING,
                "description": "活泼开朗的男生，喜欢运动",
                "location": "公园",
                "hobbies": ["篮球", "游戏", "旅行"],
                "skills": ["运动", "社交", "娱乐"]
            },
            {
                "id": "fang",
                "name": "小芳",
                "personality": NPCPersonality.SHY,
                "description": "内向安静的女孩，喜欢读书",
                "location": "图书馆",
                "hobbies": ["读书", "写作", "绘画"],
                "skills": ["写作", "绘画", "观察"]
            },
            {
                "id": "qiang",
                "name": "小强",
                "personality": NPCPersonality.HUMOROUS,
                "description": "幽默风趣的男生，总能让人开心",
                "location": "食堂",
                "hobbies": ["讲笑话", "看电影", "美食"],
                "skills": ["幽默", "表演", "烹饪"]
            }
        ]
        
        for npc_data in default_npcs:
            npc = NPC(
                id=npc_data["id"],
                name=npc_data["name"],
                personality=npc_data["personality"],
                description=npc_data["description"],
                location=npc_data["location"],
                hobbies=npc_data["hobbies"],
                skills=npc_data["skills"]
            )
            self.npcs[npc.id] = npc
            self._update_location_index(npc)
    
    def _update_location_index(self, npc: NPC) -> None:
        """更新位置索引"""
        for loc_list in self.location_npcs.values():
            if npc.id in loc_list:
                loc_list.remove(npc.id)
        
        if npc.location not in self.location_npcs:
            self.location_npcs[npc.location] = []
        
        if npc.id not in self.location_npcs[npc.location]:
            self.location_npcs[npc.location].append(npc.id)
    
    def create_npc(self, npc_id: str, name: str, personality: NPCPersonality,
                   description: str, location: str = "未知",
                   hobbies: List[str] = None, skills: List[str] = None) -> NPC:
        """创建新NPC"""
        if npc_id in self.npcs:
            raise ValueError(f"NPC with id {npc_id} already exists")
        
        npc = NPC(
            id=npc_id,
            name=name,
            personality=personality,
            description=description,
            location=location,
            hobbies=hobbies or [],
            skills=skills or []
        )
        
        self.npcs[npc_id] = npc
        self._update_location_index(npc)
        
        logger.info(f"Created NPC: {name}")
        return npc
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """获取NPC"""
        return self.npcs.get(npc_id)
    
    def get_npc_by_name(self, name: str) -> Optional[NPC]:
        """通过名称获取NPC"""
        for npc in self.npcs.values():
            if npc.name == name:
                return npc
        return None
    
    def get_npc_info(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """
        V10: 获取NPC信息（字典格式）
        
        Args:
            npc_id: NPC ID
            
        Returns:
            NPC 信息字典
        """
        npc = self.npcs.get(npc_id)
        if not npc:
            return None
        
        return {
            "id": npc.id,
            "name": npc.name,
            "personality": npc.personality.value,
            "description": npc.description,
            "location": npc.location,
            "state": npc.state.value,
            "mood": npc.mood,
            "energy": npc.energy,
            "hobbies": npc.hobbies,
            "skills": npc.skills,
            "relationship": self._get_user_relationship(npc_id)
        }
    
    def _get_user_relationship(self, npc_id: str) -> str:
        """获取用户与 NPC 的关系"""
        npc = self.npcs.get(npc_id)
        if not npc:
            return "neutral"
        
        return "neutral"
    
    def get_all_npc_ids(self) -> List[str]:
        """
        V10: 获取所有 NPC ID
        
        Returns:
            NPC ID 列表
        """
        return list(self.npcs.keys())
    
    def get_nearby_npcs(self, location: str) -> List[Dict[str, Any]]:
        """
        V10: 获取附近 NPC（字典格式）
        
        Args:
            location: 位置
            
        Returns:
            NPC 信息列表
        """
        npc_ids = self.location_npcs.get(location, [])
        npcs = []
        for nid in npc_ids:
            if nid in self.npcs:
                npc = self.npcs[nid]
                npcs.append({
                    "id": npc.id,
                    "name": npc.name,
                    "personality": npc.personality.value,
                    "location": npc.location,
                    "state": npc.state.value,
                    "mood": npc.mood
                })
        return npcs
    
    def update_npc_state(self, npc_id: str, state: NPCState) -> bool:
        """更新NPC状态"""
        npc = self.npcs.get(npc_id)
        if not npc:
            return False
        
        npc.state = state
        logger.debug(f"Updated NPC {npc.name} state to {state.value}")
        return True
    
    def update_npc_location(self, npc_id: str, location: str) -> bool:
        """更新NPC位置"""
        npc = self.npcs.get(npc_id)
        if not npc:
            return False
        
        npc.location = location
        self._update_location_index(npc)
        logger.debug(f"Updated NPC {npc.name} location to {location}")
        return True
    
    def update_npc_mood(self, npc_id: str, mood_delta: float) -> bool:
        """更新NPC心情"""
        npc = self.npcs.get(npc_id)
        if not npc:
            return False
        
        npc.mood = max(0.0, min(1.0, npc.mood + mood_delta))
        return True
    
    def get_npcs_at_location(self, location: str) -> List[NPC]:
        """获取指定位置的NPC"""
        npc_ids = self.location_npcs.get(location, [])
        return [self.npcs[nid] for nid in npc_ids if nid in self.npcs]
    
    def update_relationship(self, npc_id1: str, npc_id2: str, delta: float) -> bool:
        """更新NPC之间的关系"""
        npc1 = self.npcs.get(npc_id1)
        npc2 = self.npcs.get(npc_id2)
        
        if not npc1 or not npc2:
            return False
        
        npc1.relationships[npc_id2] = max(-1.0, min(1.0,
            npc1.relationships.get(npc_id2, 0.0) + delta))
        npc2.relationships[npc_id1] = max(-1.0, min(1.0,
            npc2.relationships.get(npc_id1, 0.0) + delta))
        
        return True
    
    def get_relationship(self, npc_id1: str, npc_id2: str) -> float:
        """获取NPC之间的关系值"""
        npc1 = self.npcs.get(npc_id1)
        if not npc1:
            return 0.0
        
        return npc1.relationships.get(npc_id2, 0.0)
    
    def record_interaction(self, npc_id1: str, npc_id2: str,
                          interaction_type: str, content: str = "") -> None:
        """记录NPC之间的交互"""
        self.interaction_history.append({
            "npc1": npc_id1,
            "npc2": npc_id2,
            "type": interaction_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.interaction_history) > 1000:
            self.interaction_history = self.interaction_history[-1000:]
        
        npc1 = self.npcs.get(npc_id1)
        npc2 = self.npcs.get(npc_id2)
        
        if npc1:
            npc1.last_interaction = datetime.now()
        if npc2:
            npc2.last_interaction = datetime.now()
    
    def get_all_npcs(self) -> List[NPC]:
        """获取所有NPC"""
        return list(self.npcs.values())
    
    def get_active_npcs(self) -> List[NPC]:
        """获取活跃的NPC"""
        return [npc for npc in self.npcs.values()
                if npc.state == NPCState.ACTIVE]
    
    def get_npc_summary(self, npc_id: str) -> Dict[str, Any]:
        """获取NPC摘要信息"""
        npc = self.npcs.get(npc_id)
        if not npc:
            return {}
        
        return {
            "id": npc.id,
            "name": npc.name,
            "personality": npc.personality.value,
            "location": npc.location,
            "state": npc.state.value,
            "mood": npc.mood,
            "energy": npc.energy,
            "relationship_count": len(npc.relationships),
            "recent_interactions": [
                h for h in self.interaction_history[-10:]
                if h["npc1"] == npc_id or h["npc2"] == npc_id
            ]
        }
    
    def export_npcs(self, filepath: str) -> None:
        """导出NPC数据"""
        data = {
            "npcs": [npc.to_dict() for npc in self.npcs.values()],
            "interaction_history": self.interaction_history[-100:]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported NPC data to {filepath}")
    
    def import_npcs(self, filepath: str) -> int:
        """导入NPC数据"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        for npc_data in data.get("npcs", []):
            try:
                npc = NPC.from_dict(npc_data)
                self.npcs[npc.id] = npc
                self._update_location_index(npc)
                imported_count += 1
            except Exception as e:
                logger.error(f"Error importing NPC: {e}")
        
        if "interaction_history" in data:
            self.interaction_history.extend(data["interaction_history"])
        
        logger.info(f"Imported {imported_count} NPCs")
        return imported_count
