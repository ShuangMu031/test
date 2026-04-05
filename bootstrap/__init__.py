"""
Bootstrap 层

V9 改版：应用初始化层

职责：
- 系统初始化
- 依赖注入
- 配置加载
"""

from bootstrap.initializer import V9Initializer, create_v9_application

__all__ = ["V9Initializer", "create_v9_application"]
