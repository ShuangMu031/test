"""
工具调用策略

V5 核心组件：工具调用校验和约束。
从 FallbackPolicy 中分离出来，专门处理工具相关逻辑。

改进：
1. 增加 prepare_tool_calls() 方法
2. 处理工具执行前的决策级约束
3. 工具并发、限频、高风险情绪下禁止等策略
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PreparedToolCalls:
    """准备好的工具调用结果"""
    tool_calls: List[Dict[str, Any]]
    suppressed: List[Dict[str, Any]]
    suppressed_reasons: List[str]
    is_valid: bool


class ToolCallPolicy:
    """
    工具调用策略
    
    职责：
    1. 校验工具计划是否合法
    2. 清理工具参数
    3. 过滤无效工具
    4. 准备工具调用（决策级约束）
    
    不负责：
    - 工具选择判断
    - 用户意图理解
    """
    
    HIGH_RISK_EMOTION_TOOLS = {"news", "social"}
    MAX_CONCURRENT_TOOLS = 3
    
    def __init__(self):
        self.stats = {
            "total_validations": 0,
            "invalid_tools": 0,
            "sanitized_args": 0,
            "suppressed_tools": 0
        }
    
    def prepare_tool_calls(
        self,
        tool_plan: List[Dict[str, Any]],
        available_tools: Dict[str, Any],
        turn_context: Any
    ) -> PreparedToolCalls:
        """
        准备工具调用
        
        处理工具执行前的决策级约束：
        1. 过滤无效工具
        2. 去重同类工具
        3. 高风险情绪下禁止某些工具
        4. 限制并发数量
        
        Args:
            tool_plan: 工具计划列表
            available_tools: 可用工具字典
            turn_context: 轮次上下文
            
        Returns:
            PreparedToolCalls
        """
        self.stats["total_validations"] += 1
        
        filtered = []
        suppressed = []
        suppressed_reasons = []
        
        seen_tools = set()
        
        emotion_insight = getattr(turn_context, "emotion_insight", None)
        support_need = getattr(emotion_insight, "support_need", "none") if emotion_insight else "none"
        is_high_risk = support_need == "high"
        
        for tool_call in tool_plan:
            tool_name = tool_call.get("tool_name", "")
            
            if not tool_name:
                suppressed.append(tool_call)
                suppressed_reasons.append("tool_name 为空")
                continue
            
            if tool_name not in available_tools:
                suppressed.append(tool_call)
                suppressed_reasons.append(f"工具 '{tool_name}' 不存在")
                self.stats["suppressed_tools"] += 1
                continue
            
            if tool_name in seen_tools:
                suppressed.append(tool_call)
                suppressed_reasons.append(f"重复工具 '{tool_name}' 已去重")
                self.stats["suppressed_tools"] += 1
                continue
            
            if is_high_risk and tool_name in self.HIGH_RISK_EMOTION_TOOLS:
                suppressed.append(tool_call)
                suppressed_reasons.append(f"高风险情绪下禁止工具 '{tool_name}'")
                self.stats["suppressed_tools"] += 1
                continue
            
            args = tool_call.get("args", {})
            sanitized_args = self.sanitize_tool_args(tool_name, args)
            
            filtered.append({
                "tool_name": tool_name,
                "args": sanitized_args
            })
            seen_tools.add(tool_name)
        
        if len(filtered) > self.MAX_CONCURRENT_TOOLS:
            excess = filtered[self.MAX_CONCURRENT_TOOLS:]
            filtered = filtered[:self.MAX_CONCURRENT_TOOLS]
            for tool_call in excess:
                suppressed.append(tool_call)
                suppressed_reasons.append(f"超过并发限制 {self.MAX_CONCURRENT_TOOLS}")
                self.stats["suppressed_tools"] += 1
        
        is_valid = len(filtered) > 0 or len(tool_plan) == 0
        
        return PreparedToolCalls(
            tool_calls=filtered,
            suppressed=suppressed,
            suppressed_reasons=suppressed_reasons,
            is_valid=is_valid
        )
    
    def validate_tool_plan(
        self,
        tool_plan: List[Dict[str, Any]],
        available_tools: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        校验工具计划
        
        Args:
            tool_plan: 工具计划列表
            available_tools: 可用工具字典
            
        Returns:
            (is_valid, errors)
        """
        self.stats["total_validations"] += 1
        errors = []
        
        if not tool_plan:
            return True, []
        
        for i, tool_call in enumerate(tool_plan):
            tool_name = tool_call.get("tool_name", "")
            
            if not tool_name:
                errors.append(f"工具调用 {i}: tool_name 为空")
                continue
            
            if tool_name not in available_tools:
                errors.append(f"工具调用 {i}: 工具 '{tool_name}' 不存在")
                self.stats["invalid_tools"] += 1
        
        return len(errors) == 0, errors
    
    def sanitize_tool_args(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        清理工具参数
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            清理后的参数
        """
        sanitized = {}
        
        if not isinstance(args, dict):
            self.stats["sanitized_args"] += 1
            return {}
        
        for key, value in args.items():
            if value is None:
                continue
            
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue
            
            sanitized[key] = value
        
        if len(sanitized) != len(args):
            self.stats["sanitized_args"] += 1
        
        return sanitized
    
    def filter_invalid_tools(
        self,
        tool_plan: List[Dict[str, Any]],
        available_tools: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        过滤无效工具
        
        Args:
            tool_plan: 工具计划列表
            available_tools: 可用工具字典
            
        Returns:
            过滤后的工具计划
        """
        filtered = []
        
        for tool_call in tool_plan:
            tool_name = tool_call.get("tool_name", "")
            
            if not tool_name:
                continue
            
            if tool_name not in available_tools:
                logger.warning(f"工具 '{tool_name}' 不存在，已过滤")
                self.stats["invalid_tools"] += 1
                continue
            
            args = tool_call.get("args", {})
            sanitized_args = self.sanitize_tool_args(tool_name, args)
            
            filtered.append({
                "tool_name": tool_name,
                "args": sanitized_args
            })
        
        return filtered
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
