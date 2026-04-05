"""
虚拟世界状态模型

定义虚拟世界的状态数据结构。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class WeatherType(Enum):
    """天气类型"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"
    WINDY = "windy"


class LocationType(Enum):
    """位置类型"""
    DORMITORY = "dormitory"
    CLASSROOM = "classroom"
    LIBRARY = "library"
    CAFETERIA = "cafeteria"
    PARK = "park"


class ActivityType(Enum):
    """活动类型"""
    STUDYING = "studying"
    EATING = "eating"
    RESTING = "resting"
    EXERCISING = "exercising"
    SOCIALIZING = "socializing"
    WALKING = "walking"


@dataclass
class Location:
    """
    位置
    
    Attributes:
        name: 位置名称
        description: 位置描述
        activities: 可进行的活动
        location_type: 位置类型
    """
    name: str
    description: str
    activities: List[ActivityType]
    location_type: Optional[LocationType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "activities": [act.value for act in self.activities],
            "location_type": self.location_type.value if self.location_type else None
        }


@dataclass
class WorldTime:
    """
    世界时间
    
    Attributes:
        hour: 小时
        minute: 分钟
        second: 秒
    """
    hour: int
    minute: int
    second: int
    
    def to_dict(self) -> Dict[str, int]:
        """
        转换为字典
        """
        return {
            "hour": self.hour,
            "minute": self.minute,
            "second": self.second
        }


Time = WorldTime


class TimeOfDay(Enum):
    """时段类型"""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"


class LightLevel(Enum):
    """光照水平"""
    DAWN = "dawn"
    BRIGHT = "bright"
    DUSK = "dusk"
    DARK = "dark"


class AtmosphereType(Enum):
    """氛围类型"""
    QUIET = "quiet"
    LIVELY = "lively"
    MISTY = "misty"
    COLD = "cold"
    WARM = "warm"
    COZY = "cozy"


@dataclass
class WorldState:
    """
    虚拟世界状态
    
    Attributes:
        time: 当前时间
        location: 当前位置
        weather: 当前天气
        temperature: 当前温度
        activity: 当前活动
        energy: 能量值
        hunger: 饥饿值
        boredom: 无聊值
        light_level: 光照水平
        atmosphere: 当前氛围
        activity_started_at: 当前活动开始时间
        location_scene_hint: 场景提示
    """
    time: WorldTime
    location: Location
    weather: WeatherType
    temperature: float
    activity: ActivityType
    energy: float
    hunger: float
    boredom: float = 0.0
    light_level: LightLevel = LightLevel.BRIGHT
    atmosphere: AtmosphereType = AtmosphereType.QUIET
    activity_started_at: Optional[float] = None
    location_scene_hint: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        """
        return {
            "time": self.time.to_dict(),
            "location": self.location.to_dict(),
            "weather": self.weather.value,
            "temperature": self.temperature,
            "activity": self.activity.value,
            "energy": self.energy,
            "hunger": self.hunger,
            "boredom": self.boredom,
            "light_level": self.light_level.value,
            "atmosphere": self.atmosphere.value,
            "activity_started_at": self.activity_started_at,
            "location_scene_hint": self.location_scene_hint
        }
    
    def get_time_of_day(self) -> TimeOfDay:
        """
        获取当前时段
        
        Returns:
            时段类型
        """
        hour = self.time.hour
        if 6 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= hour < 22:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def get_scene_description(self) -> str:
        """
        获取场景描述
        
        Returns:
            场景描述文本
        """
        time_desc = {
            TimeOfDay.MORNING: "清晨",
            TimeOfDay.AFTERNOON: "午后",
            TimeOfDay.EVENING: "傍晚",
            TimeOfDay.NIGHT: "夜晚"
        }
        
        atmosphere_desc = {
            AtmosphereType.QUIET: "安静",
            AtmosphereType.LIVELY: "热闹",
            AtmosphereType.MISTY: "朦胧",
            AtmosphereType.COLD: "清冷",
            AtmosphereType.WARM: "温暖",
            AtmosphereType.COZY: "舒适"
        }
        
        return f"{time_desc[self.get_time_of_day()]}的{self.location.name}，{atmosphere_desc[self.atmosphere]}"
