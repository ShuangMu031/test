"""
脑子基类

V5 核心组件：所有脑子的基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class BaseBrain(ABC):
    """
    脑子基类
    
    所有脑子必须实现：
    - name: 脑子名称
    - process(): 处理方法
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """脑子名称"""
        pass
    
    @abstractmethod
    async def process(self, context: Any) -> Any:
        """
        处理上下文
        
        Args:
            context: TurnContext
            
        Returns:
            处理结果
        """
        pass

    async def execute(self, context: Any) -> Any:
        """兼容旧示例入口，等价于 process。"""
        return await self.process(context)
    
    def _log(self, message: str, level: str = "info") -> None:
        """日志输出"""
        getattr(logger, level)(f"[{self.name}] {message}")
