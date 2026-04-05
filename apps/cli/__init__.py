"""
CLI 应用层

V9 改版：命令行入口
"""

from apps.cli.main import main, main_async, CLIInterface

__all__ = ["main", "main_async", "CLIInterface"]
