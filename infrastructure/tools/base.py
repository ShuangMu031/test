"""
工具基类

V6 统一工具协议：
- ToolType 枚举
- ToolResult 统一字段（含 source）
- BaseTool 强制字段（name, description, tool_type）

========================================
模块边界约束（第四次整改）
========================================

【正确定位】
工具层尽量做成"输入参数，输出标准结果"的纯执行单元。

【必须保留】
- 标准 execute(**kwargs) -> ToolResult
- 工具名 (name)
- 工具类型 (tool_type)
- 描述 (description)
- 错误封装

【绝对禁止】
- 编排主链
- 直接决定回复内容
- 碰 TurnContext
- 决定 world update
- 直接走 UI/投递

【执行规范】
工具只负责执行，不负责决策。
输入参数 -> 执行 -> 输出标准 ToolResult。

【输出规范】
输出 ToolResult，包含 success, data, error, tool_name, source, metadata。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ToolType(Enum):
    """工具类型枚举"""
    WEATHER = "weather"
    NEWS = "news"
    MAP = "map"
    SEARCH = "search"
    CALCULATOR = "calculator"
    OTHER = "other"


@dataclass
class ToolResult:
    """
    工具执行结果
    
    统一字段：
    - success: 是否成功
    - data: 返回数据
    - error: 错误信息
    - tool_name: 工具名称
    - source: 结果来源
    - metadata: 额外元数据
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    tool_name: str = ""
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "tool_name": self.tool_name,
            "source": self.source,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    工具基类
    
    所有工具必须实现：
    - name: 工具名称
    - description: 工具描述
    - tool_type: 工具类型
    - execute(): 执行方法
    - get_schema(): 获取工具 schema
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @property
    @abstractmethod
    def tool_type(self) -> ToolType:
        """工具类型"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具 schema"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": {}
        }
