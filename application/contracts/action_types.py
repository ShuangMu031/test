"""
动作类型定义

V5 核心枚举：从 domain/decision/models.py 迁出。
V9 改版：移至 contracts 目录，避免循环导入。
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
