"""
工具注册表

V6 统一工具协议：
- 和 base.py 对齐
- register() 增加兜底（没有 tool_type 时默认 OTHER）
- 去重，避免重复注册
- list_tools_info() 只读取基类约定字段
"""

from typing import Dict, List, Optional
import logging

from infrastructure.tools.base import BaseTool, ToolType, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    工具注册表
    
    管理所有可用工具的注册和发现。
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_types: Dict[ToolType, List[str]] = {
            tool_type: [] for tool_type in ToolType
        }
    
    def register(self, tool: BaseTool) -> None:
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        if tool.name in self._tools:
            logger.warning(f"Tool '{tool.name}' already registered, skipping")
            return
        
        tool_type = getattr(tool, "tool_type", ToolType.OTHER)
        if tool_type is None:
            tool_type = ToolType.OTHER
        
        self._tools[tool.name] = tool
        self._tool_types[tool_type].append(tool.name)
        logger.debug(f"Registered tool: {tool.name} (type: {tool_type.value})")
    
    def unregister(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否成功注销
        """
        if tool_name not in self._tools:
            return False
        
        tool = self._tools.pop(tool_name)
        tool_type = getattr(tool, "tool_type", ToolType.OTHER)
        if tool_name in self._tool_types.get(tool_type, []):
            self._tool_types[tool_type].remove(tool_name)
        logger.debug(f"Unregistered tool: {tool_name}")
        return True
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回 None
        """
        return self._tools.get(tool_name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[BaseTool]:
        """
        获取指定类型的所有工具
        
        Args:
            tool_type: 工具类型
            
        Returns:
            工具列表
        """
        tool_names = self._tool_types.get(tool_type, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def list_tools(self) -> List[str]:
        """
        列出所有已注册的工具名称
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())
    
    def list_tools_info(self) -> List[Dict[str, str]]:
        """
        列出所有工具的详细信息
        
        只读取基类约定字段：name, description, tool_type
        
        Returns:
            工具信息列表
        """
        result = []
        for tool in self._tools.values():
            tool_type = getattr(tool, "tool_type", ToolType.OTHER)
            description = getattr(tool, "description", "")
            result.append({
                "name": tool.name,
                "description": description,
                "type": tool_type.value
            })
        return result
    
    def has_tool(self, tool_name: str) -> bool:
        """
        检查工具是否已注册
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否已注册
        """
        return tool_name in self._tools
    
    def clear(self) -> None:
        """
        清空所有已注册的工具
        """
        self._tools.clear()
        for tool_type in self._tool_types:
            self._tool_types[tool_type] = []
        logger.debug("Cleared all registered tools")


_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """
    获取全局工具注册表
    
    Returns:
        全局工具注册表实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: BaseTool) -> None:
    """
    向全局注册表注册工具
    
    Args:
        tool: 工具实例
    """
    get_global_registry().register(tool)


def get_tool(tool_name: str) -> Optional[BaseTool]:
    """
    从全局注册表获取工具
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具实例
    """
    return get_global_registry().get_tool(tool_name)


def list_tools() -> List[str]:
    """
    列出全局注册表中的所有工具
    
    Returns:
        工具名称列表
    """
    return get_global_registry().list_tools()
