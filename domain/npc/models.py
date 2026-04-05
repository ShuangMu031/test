"""
NPC数据模型

定义NPC相关的数据结构
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NPCState(Enum):
    """NPC状态"""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    SLEEPING = "sleeping"
    AWAY = "away"


class NPCPersonality(Enum):
    """NPC性格类型"""
    FRIENDLY = "friendly"
    SHY = "shy"
    OUTGOING = "outgoing"
    SERIOUS = "serious"
    PLAYFUL = "playful"
    CARING = "caring"
    HUMOROUS = "humorous"


@dataclass
class NPC:
    """NPC角色"""
    id: str
    name: str
    personality: NPCPersonality
    description: str
    
    location: str = "未知"
    state: NPCState = NPCState.IDLE
    
    mood: float = 0.5
    energy: float = 0.7
    
    relationships: Dict[str, float] = field(default_factory=dict)
    memory: List[str] = field(default_factory=list)
    
    hobbies: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    last_interaction: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality.value,
            "description": self.description,
            "location": self.location,
            "state": self.state.value,
            "mood": self.mood,
            "energy": self.energy,
            "relationships": self.relationships,
            "hobbies": self.hobbies,
            "skills": self.skills,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        npc = cls(
            id=data["id"],
            name=data["name"],
            personality=NPCPersonality(data["personality"]),
            description=data["description"],
            location=data.get("location", "未知"),
            state=NPCState(data.get("state", "idle")),
            mood=data.get("mood", 0.5),
            energy=data.get("energy", 0.7),
            relationships=data.get("relationships", {}),
            hobbies=data.get("hobbies", []),
            skills=data.get("skills", [])
        )
        
        if data.get("last_interaction"):
            npc.last_interaction = datetime.fromisoformat(data["last_interaction"])
        
        return npc
