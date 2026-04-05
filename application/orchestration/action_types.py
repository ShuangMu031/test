"""
动作类型定义

V5 核心枚举：从 domain/decision/models.py 迁出。
所有 V5 主线组件应从此处导入 ActionType。
"""

from enum import Enum


class ActionType(Enum):
    """动作类型"""
    RESPOND = "respond"
    COMFORT = "comfort"
    REST = "rest"
    EAT = "eat"
    SOCIALIZE = "socialize"
    EXPLORE = "explore"
    LEARN = "learn"
    TOOL_USE = "tool_use"
    WORLD_CONTENT_READ = "world_content_read"
