"""
世界时钟

V9 持续运行世界核心组件

职责：
- 维护唯一世界时间真相
- 定义 tick 推进规则
- 记录上次推进时间
- 支持持久化和恢复

设计原则：
- 世界时间只能由后台 tick 推进
- 读取世界不会改变时间
- 同一时刻只有一个推进过程
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import json


@dataclass
class WorldClock:
    """
    世界时钟
    
    唯一世界时间真相源
    
    Attributes:
        world_datetime: 当前世界时间
        tick_minutes: 每次 tick 推进多少分钟（默认 5 分钟）
        real_tick_seconds: 现实多少秒触发一次 tick（默认 30 秒）
        last_tick_real_ts: 上次推进的现实时间戳
    """
    world_datetime: datetime = field(default_factory=datetime.now)
    tick_minutes: int = 5
    real_tick_seconds: int = 30
    last_tick_real_ts: float = 0.0
    
    def tick(self, minutes: Optional[int] = None) -> None:
        """
        推进世界时间
        
        Args:
            minutes: 推进分钟数，默认使用 tick_minutes
        """
        advance = minutes if minutes is not None else self.tick_minutes
        self.world_datetime += timedelta(minutes=advance)
        self.last_tick_real_ts = datetime.now().timestamp()
    
    def should_tick(self) -> bool:
        """
        判断是否应该推进
        
        Returns:
            是否到达下一个 tick 时间
        """
        now = datetime.now().timestamp()
        return (now - self.last_tick_real_ts) >= self.real_tick_seconds
    
    def get_world_time_str(self) -> str:
        """
        获取世界时间字符串
        
        Returns:
            格式化的时间字符串 (HH:MM)
        """
        return self.world_datetime.strftime("%H:%M")
    
    def get_world_datetime_str(self) -> str:
        """
        获取完整世界时间字符串
        
        Returns:
            格式化的日期时间字符串
        """
        return self.world_datetime.strftime("%Y-%m-%d %H:%M")
    
    def get_time_period(self) -> str:
        """
        获取时间段
        
        Returns:
            时间段名称
        """
        hour = self.world_datetime.hour
        
        if 5 <= hour < 8:
            return "清晨"
        elif 8 <= hour < 11:
            return "上午"
        elif 11 <= hour < 14:
            return "中午"
        elif 14 <= hour < 17:
            return "下午"
        elif 17 <= hour < 19:
            return "傍晚"
        elif 19 <= hour < 22:
            return "晚上"
        else:
            return "深夜"
    
    def is_meal_time(self) -> bool:
        """
        是否是用餐时间
        
        Returns:
            是否是用餐时间
        """
        hour = self.world_datetime.hour
        return (7 <= hour < 9) or (11 <= hour < 13) or (17 <= hour < 19)
    
    def is_sleep_time(self) -> bool:
        """
        是否是睡眠时间
        
        Returns:
            是否是睡眠时间
        """
        hour = self.world_datetime.hour
        return hour >= 23 or hour < 6
    
    def is_quiet_time(self) -> bool:
        """
        是否是安静时段
        
        Returns:
            是否是安静时段
        """
        hour = self.world_datetime.hour
        return hour >= 22 or hour < 7
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "world_datetime": self.world_datetime.isoformat(),
            "tick_minutes": self.tick_minutes,
            "real_tick_seconds": self.real_tick_seconds,
            "last_tick_real_ts": self.last_tick_real_ts,
            "world_time_str": self.get_world_time_str(),
            "time_period": self.get_time_period()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WorldClock":
        """
        从字典创建
        
        Args:
            data: 字典数据
            
        Returns:
            WorldClock 实例
        """
        return cls(
            world_datetime=datetime.fromisoformat(data["world_datetime"]),
            tick_minutes=data.get("tick_minutes", 5),
            real_tick_seconds=data.get("real_tick_seconds", 30),
            last_tick_real_ts=data.get("last_tick_real_ts", 0.0)
        )
    
    def to_json(self) -> str:
        """
        转换为 JSON 字符串
        
        Returns:
            JSON 字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "WorldClock":
        """
        从 JSON 字符串创建
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            WorldClock 实例
        """
        return cls.from_dict(json.loads(json_str))
