"""
现实素材采集模块

V9 第五批新增：负责从各种工具采集现实素材

核心组件：
- collector: 现实素材采集器
"""

from infrastructure.reality_sources.collector import RealitySourceCollector

__all__ = ["RealitySourceCollector"]
