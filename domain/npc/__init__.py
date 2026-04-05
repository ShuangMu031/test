"""
NPC管理模块

提供多角色管理能力
"""

from .manager import NPCManager
from .models import NPC, NPCState, NPCPersonality

__all__ = [
    "NPCManager",
    "NPC",
    "NPCState",
    "NPCPersonality"
]
