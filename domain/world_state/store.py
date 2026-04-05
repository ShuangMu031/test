"""
世界状态持久化

V9 持续运行世界核心组件

职责：
- 保存世界状态到文件
- 从文件恢复世界状态
- 管理世界版本
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorldStateData:
    """
    世界状态数据
    
    持久化的世界状态结构
    """
    world_version: int = 1
    world_datetime: str = ""
    tick_minutes: int = 5
    real_tick_seconds: int = 30
    last_tick_real_ts: float = 0.0
    
    location: str = "宿舍"
    weather: str = "晴朗"
    energy: float = 0.8
    hunger: float = 0.3
    
    npcs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recent_events: list = field(default_factory=list)
    
    saved_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldStateData":
        return cls(
            world_version=data.get("world_version", 1),
            world_datetime=data.get("world_datetime", ""),
            tick_minutes=data.get("tick_minutes", 5),
            real_tick_seconds=data.get("real_tick_seconds", 30),
            last_tick_real_ts=data.get("last_tick_real_ts", 0.0),
            location=data.get("location", "宿舍"),
            weather=data.get("weather", "晴朗"),
            energy=data.get("energy", 0.8),
            hunger=data.get("hunger", 0.3),
            npcs=data.get("npcs", {}),
            recent_events=data.get("recent_events", []),
            saved_at=data.get("saved_at", "")
        )


class WorldStore:
    """
    世界状态存储
    
    负责世界状态的持久化和恢复
    """
    
    DEFAULT_SAVE_PATH = "world_state.json"
    
    def __init__(self, save_path: Optional[str] = None):
        self.save_path = save_path or self.DEFAULT_SAVE_PATH
    
    def save(self, state_data: WorldStateData) -> bool:
        """
        保存世界状态
        
        Args:
            state_data: 世界状态数据
            
        Returns:
            是否保存成功
        """
        try:
            state_data.saved_at = datetime.now().isoformat()
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(state_data.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.info(f"世界状态已保存: version={state_data.world_version}, time={state_data.world_datetime}")
            return True
            
        except Exception as e:
            logger.error(f"保存世界状态失败: {e}")
            return False
    
    def load(self) -> Optional[WorldStateData]:
        """
        加载世界状态
        
        Returns:
            世界状态数据，如果不存在则返回 None
        """
        try:
            if not os.path.exists(self.save_path):
                logger.info("世界状态文件不存在，将使用默认状态")
                return None
            
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state_data = WorldStateData.from_dict(data)
            logger.info(f"世界状态已加载: version={state_data.world_version}, time={state_data.world_datetime}")
            return state_data
            
        except Exception as e:
            logger.error(f"加载世界状态失败: {e}")
            return None
    
    def exists(self) -> bool:
        """
        检查世界状态文件是否存在
        
        Returns:
            是否存在
        """
        return os.path.exists(self.save_path)
    
    def delete(self) -> bool:
        """
        删除世界状态文件
        
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
                logger.info("世界状态文件已删除")
            return True
        except Exception as e:
            logger.error(f"删除世界状态失败: {e}")
            return False
    
    def get_save_info(self) -> Dict[str, Any]:
        """
        获取保存信息
        
        Returns:
            保存信息字典
        """
        if not self.exists():
            return {"exists": False}
        
        try:
            stat = os.stat(self.save_path)
            return {
                "exists": True,
                "path": self.save_path,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception:
            return {"exists": True, "path": self.save_path}
