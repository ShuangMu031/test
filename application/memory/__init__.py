"""
记忆服务模块

V9 三层记忆系统：
- MemoryFacade: 记忆服务门面，提供主链调用的统一接口
- MemoryRouter: 记忆路由器，根据输入和情绪判断生成三层候选
- MemoryDocumentStore: 记忆文档存储，统一读写三层记忆文档
- SessionFinalizer: 会话清算器，会话结束时清算升级删除
- MemoryDecayEngine: 记忆衰减引擎，定时衰减事件记忆

三层记忆定义：
- 短期记忆: 当前会话态工作记忆，5-10分钟，会话结束后清空
- 事件记忆: 带情绪、情境、后果的事件档案，动态衰减
- 长期记忆: 稳定偏好、关系、身份事实，近永久保留
"""

from application.memory.facade import MemoryFacade
from application.memory.memory_router import (
    MemoryRouter,
    MemoryAnalysisDocument,
    ShortTermCandidate,
    EpisodicCandidate,
    LongTermCandidate,
    MemoryLayer,
    EventType,
    LongTermCategory
)
from application.memory.memory_document_store import (
    MemoryDocumentStore,
    ShortTermSession,
    EpisodicEvent,
    LongTermMemory
)
from application.memory.session_finalizer import SessionFinalizer
from application.memory.memory_decay_engine import MemoryDecayEngine

__all__ = [
    "MemoryFacade",
    "MemoryRouter",
    "MemoryAnalysisDocument",
    "ShortTermCandidate",
    "EpisodicCandidate",
    "LongTermCandidate",
    "MemoryLayer",
    "EventType",
    "LongTermCategory",
    "MemoryDocumentStore",
    "ShortTermSession",
    "EpisodicEvent",
    "LongTermMemory",
    "SessionFinalizer",
    "MemoryDecayEngine"
]
