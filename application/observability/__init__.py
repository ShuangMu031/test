"""
可观测层

V7 新增模块：
- trace_models: 视图模型定义
- trace_builder: 视图构建器
- cli_exporter: CLI 输出器

职责：
- 从 TurnContext 构建展示视图
- 不直接读业务对象，只读视图模型
- 支持多种输出格式（CLI/API/Web）
"""

from application.observability.trace_models import (
    TurnTraceView,
    BrainTraceView,
    ExecutionTraceView,
    ReplyGateView,
    PlanDiffView,
    DecisionChainView
)
from application.observability.trace_builder import TraceBuilder
from application.observability.cli_exporter import CLIExporter

__all__ = [
    "TurnTraceView",
    "BrainTraceView",
    "ExecutionTraceView",
    "ReplyGateView",
    "PlanDiffView",
    "DecisionChainView",
    "TraceBuilder",
    "CLIExporter"
]
