"""
本地世界适配器 -> 世界引擎

V9 持续运行世界核心组件

改版：
- 使用 WorldClock 作为唯一时间源
- get_world_snapshot() 只读，不推进时间
- 添加 tick() 方法实现后台推进
- 添加状态演化规则
- 添加 NPC 日程系统
- 添加事件生成器

设计原则：
- 世界时间只能由后台 tick 推进
- 读取世界不会改变状态
- 同一时刻只有一个推进过程
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import logging

from domain.world_state.port import (
    WorldRuntimePort,
    WorldSnapshot,
    WorldEvent
)
from domain.world_state.clock import WorldClock
from domain.world_state.store import WorldStore, WorldStateData

logger = logging.getLogger(__name__)


class NPCSchedule:
    """
    NPC 日程
    
    定义 NPC 在不同时间段的位置
    """
    
    SCHEDULES = {
        "npc_001": {
            "name": "小明",
            "default_location": "宿舍",
            "slots": [
                (8, 11, "图书馆"),
                (11, 13, "食堂"),
                (14, 17, "教室"),
                (19, 22, "图书馆"),
            ]
        },
        "npc_002": {
            "name": "小红",
            "default_location": "宿舍",
            "slots": [
                (8, 11, "教室"),
                (11, 13, "食堂"),
                (14, 17, "图书馆"),
                (17, 19, "公园"),
            ]
        },
        "npc_003": {
            "name": "小刚",
            "default_location": "宿舍",
            "slots": [
                (8, 11, "教室"),
                (14, 17, "操场"),
                (19, 21, "健身房"),
            ]
        }
    }
    
    @classmethod
    def get_location(cls, npc_id: str, hour: int) -> str:
        """
        获取 NPC 在指定时间的位置
        
        Args:
            npc_id: NPC ID
            hour: 小时
            
        Returns:
            位置
        """
        schedule = cls.SCHEDULES.get(npc_id)
        if not schedule:
            return "宿舍"
        
        for start, end, location in schedule.get("slots", []):
            if start <= hour < end:
                return location
        
        return schedule.get("default_location", "宿舍")
    
    @classmethod
    def get_name(cls, npc_id: str) -> str:
        """获取 NPC 名称"""
        schedule = cls.SCHEDULES.get(npc_id)
        return schedule.get("name", "未知") if schedule else "未知"


class LocalWorldAdapter(WorldRuntimePort):
    """
    世界引擎
    
    V9 持续运行世界核心
    
    职责：
    - 维护唯一世界状态真相
    - 后台 tick 推进世界
    - 状态演化规则
    - NPC 日程管理
    - 事件生成
    - 持久化支持
    """
    
    def __init__(self, save_path: Optional[str] = None, auto_load: bool = True, auto_save: bool = True):
        self._store = WorldStore(save_path)
        self._version = 1
        self._auto_save = auto_save
        
        self._clock = WorldClock()
        self._weather = "晴朗"
        self._location = "宿舍"
        self._energy = 0.8
        self._hunger = 0.3
        self._npcs = self._create_default_npcs()
        self._events: List[WorldEvent] = []
        self._event_counter = 0
        self._user_actor_id: Optional[str] = None
        
        self._last_time_period = self._clock.get_time_period()
        self._last_weather = self._weather
        
        if auto_load:
            self._load_from_store()
    
    def _create_default_npcs(self) -> List[Dict[str, Any]]:
        """创建默认 NPC"""
        return [
            {
                "npc_id": "npc_001",
                "name": "小明",
                "location": "图书馆",
                "mood": "平静",
                "relationship": 0.5
            },
            {
                "npc_id": "npc_002",
                "name": "小红",
                "location": "食堂",
                "mood": "开心",
                "relationship": 0.7
            },
            {
                "npc_id": "npc_003",
                "name": "小刚",
                "location": "操场",
                "mood": "兴奋",
                "relationship": 0.3
            }
        ]
    
    async def get_world_snapshot(self) -> WorldSnapshot:
        """
        获取世界快照
        
        V9 改造：只读，不推进时间
        V9 改版：添加调试字段
        """
        snapshot_id = f"snap_{datetime.now().timestamp()}"
        
        return WorldSnapshot(
            snapshot_id=snapshot_id,
            world_time=self._clock.get_world_time_str(),
            weather=self._weather,
            location=self._location,
            npcs=self._npcs,
            recent_events=[e.to_dict() for e in self._events[-5:]],
            version=self._version,
            time_period=self._clock.get_time_period(),
            energy=self._energy,
            hunger=self._hunger
        )
    
    async def get_recent_events(self, limit: int = 10) -> List[WorldEvent]:
        """获取最近事件"""
        return self._events[-limit:]
    
    async def get_npcs_at_location(self, location: str) -> List[Dict[str, Any]]:
        """获取指定位置的 NPC"""
        return [npc for npc in self._npcs if npc["location"] == location]
    
    async def inject_user_actor(self, user_id: str) -> str:
        """注入用户角色"""
        self._user_actor_id = f"user_{user_id}"
        return self._user_actor_id
    
    async def enqueue_world_action(self, action: Dict[str, Any]) -> bool:
        """
        提交世界动作
        
        V9 改造：统一动作处理
        """
        return await self.apply_action(action)
    
    async def tick(self, minutes: Optional[int] = None) -> List[WorldEvent]:
        """
        世界 tick 推进
        
        V9 核心：后台调用的世界推进方法
        
        Args:
            minutes: 推进分钟数，默认使用 clock.tick_minutes
            
        Returns:
            生成的事件列表
        """
        events = []
        
        before_snapshot = self._capture_state()
        
        self._clock.tick(minutes)
        
        events.extend(self._update_needs(minutes or self._clock.tick_minutes))
        
        events.extend(self._update_weather())
        
        events.extend(self._update_npc_schedule())
        
        events.extend(self._generate_events_from_transitions(before_snapshot))
        
        for event in events:
            self._events.append(event)
            self._event_counter += 1
        
        self._version += 1
        
        if events:
            logger.debug(f"World tick 完成，生成 {len(events)} 个事件")
        
        if self._auto_save:
            self.save()
        
        return events
    
    async def apply_action(self, action: Dict[str, Any]) -> bool:
        """
        应用世界动作
        
        V9 核心：统一动作处理入口
        
        Args:
            action: 动作字典
            
        Returns:
            是否成功
        """
        action_type = action.get("type")
        
        if action_type == "tick":
            minutes = int(action.get("minutes", self._clock.tick_minutes))
            await self.tick(minutes)
            self._add_event("tick", f"时间推进 {minutes} 分钟")
        
        elif action_type == "move":
            old_location = self._location
            self._location = action.get("location", self._location)
            self._add_event("move", f"从 {old_location} 移动到 {self._location}")
        
        elif action_type == "interact":
            npc_id = action.get("npc_id")
            npc_name = NPCSchedule.get_name(npc_id)
            self._add_event("interact", f"与 {npc_name} 互动", participants=[npc_id])
            
            for npc in self._npcs:
                if npc["npc_id"] == npc_id:
                    npc["relationship"] = min(1.0, npc.get("relationship", 0.5) + 0.05)
        
        elif action_type == "rest":
            self._energy = min(1.0, self._energy + 0.2)
            self._add_event("rest", "休息了一会儿")
        
        elif action_type == "eat":
            self._hunger = max(0.0, self._hunger - 0.4)
            self._add_event("eat", "吃了一些东西")
        
        else:
            logger.warning(f"未知动作类型: {action_type}")
            return False
        
        return True
    
    def _capture_state(self) -> Dict[str, Any]:
        """
        捕获当前状态
        
        Returns:
            状态快照
        """
        return {
            "time_period": self._clock.get_time_period(),
            "weather": self._weather,
            "energy": self._energy,
            "hunger": self._hunger,
            "npcs": [(n["npc_id"], n["location"]) for n in self._npcs]
        }
    
    def _update_needs(self, minutes: int) -> List[WorldEvent]:
        """
        更新需求状态
        
        Args:
            minutes: 推进的分钟数
            
        Returns:
            生成的事件列表
        """
        events = []
        
        hours = minutes / 60.0
        
        if self._clock.is_sleep_time():
            self._energy = min(1.0, self._energy + 0.1 * hours)
        else:
            self._energy = max(0.0, self._energy - 0.05 * hours)
        
        if self._clock.is_meal_time():
            self._hunger = min(1.0, self._hunger + 0.15 * hours)
        else:
            self._hunger = min(1.0, self._hunger + 0.08 * hours)
        
        if self._hunger > 0.8 and not self._clock.is_meal_time():
            events.append(WorldEvent(
                event_id=f"evt_needs_{datetime.now().timestamp()}",
                event_type="need_alert",
                description="感到有些饿了",
                participants=[]
            ))
        
        if self._energy < 0.3:
            events.append(WorldEvent(
                event_id=f"evt_needs_{datetime.now().timestamp()}",
                event_type="need_alert",
                description="感到有些疲惫",
                participants=[]
            ))
        
        return events
    
    def _update_weather(self) -> List[WorldEvent]:
        """
        更新天气
        
        Returns:
            生成的事件列表
        """
        events = []
        
        if random.random() < 0.05:
            weather_options = ["晴朗", "多云", "阴天", "小雨"]
            weights = [0.4, 0.3, 0.2, 0.1]
            
            if self._clock.get_time_period() in ["傍晚", "晚上"]:
                weights = [0.3, 0.3, 0.25, 0.15]
            
            new_weather = random.choices(weather_options, weights=weights)[0]
            
            if new_weather != self._weather:
                old_weather = self._weather
                self._weather = new_weather
                events.append(WorldEvent(
                    event_id=f"evt_weather_{datetime.now().timestamp()}",
                    event_type="weather_change",
                    description=f"天气从 {old_weather} 变为 {new_weather}",
                    participants=[]
                ))
        
        return events
    
    def _update_npc_schedule(self) -> List[WorldEvent]:
        """
        更新 NPC 日程
        
        V9 改版：添加 mood 和 relationship 的动态变化
        
        Returns:
            生成的事件列表
        """
        events = []
        hour = self._clock.world_datetime.hour
        time_period = self._clock.get_time_period()
        
        for npc in self._npcs:
            npc_id = npc["npc_id"]
            old_location = npc["location"]
            new_location = NPCSchedule.get_location(npc_id, hour)
            
            if new_location != old_location:
                npc["location"] = new_location
                npc_name = NPCSchedule.get_name(npc_id)
                events.append(WorldEvent(
                    event_id=f"evt_npc_{datetime.now().timestamp()}_{npc_id}",
                    event_type="npc_move",
                    description=f"{npc_name} 从 {old_location} 去了 {new_location}",
                    participants=[npc_id]
                ))
            
            if self._weather in ["小雨", "阴天"]:
                if npc["mood"] == "开心":
                    npc["mood"] = "平静"
            elif self._weather == "晴朗":
                if npc["mood"] == "平静" and random.random() < 0.1:
                    npc["mood"] = "开心"
            
            if time_period in ["深夜"]:
                if npc["mood"] in ["开心", "兴奋"]:
                    npc["mood"] = "平静"
            elif time_period in ["早晨", "上午"]:
                if npc["mood"] == "平静" and random.random() < 0.05:
                    npc["mood"] = "开心"
            
            if npc.get("relationship", 0.5) > 0.3:
                npc["relationship"] = max(0.3, npc["relationship"] - 0.001)
            
            if npc["relationship"] < 0.9:
                npc["relationship"] = min(0.9, npc["relationship"] + 0.0005)
        
        return events
    
    def _generate_events_from_transitions(self, before: Dict[str, Any]) -> List[WorldEvent]:
        """
        从状态转换生成事件
        
        Args:
            before: 之前的状态快照
            
        Returns:
            生成的事件列表
        """
        events = []
        
        old_period = before.get("time_period")
        new_period = self._clock.get_time_period()
        
        if old_period != new_period:
            events.append(WorldEvent(
                event_id=f"evt_period_{datetime.now().timestamp()}",
                event_type="time_period_change",
                description=f"时间从 {old_period} 进入 {new_period}",
                participants=[]
            ))
        
        return events
    
    def _add_event(
        self,
        event_type: str,
        description: str,
        participants: List[str] = None
    ) -> WorldEvent:
        """添加事件"""
        self._event_counter += 1
        event = WorldEvent(
            event_id=f"evt_{self._event_counter}",
            event_type=event_type,
            description=description,
            participants=participants or []
        )
        self._events.append(event)
        return event
    
    def get_world_state(self) -> Dict[str, Any]:
        """
        获取完整世界状态
        
        Returns:
            世界状态字典
        """
        return {
            "version": self._version,
            "clock": self._clock.to_dict(),
            "weather": self._weather,
            "location": self._location,
            "energy": self._energy,
            "hunger": self._hunger,
            "npcs": self._npcs,
            "event_count": len(self._events)
        }
    
    def save(self) -> bool:
        """
        保存世界状态
        
        Returns:
            是否保存成功
        """
        state_data = WorldStateData(
            world_version=self._version,
            world_datetime=self._clock.world_datetime.isoformat(),
            tick_minutes=self._clock.tick_minutes,
            real_tick_seconds=self._clock.real_tick_seconds,
            last_tick_real_ts=self._clock.last_tick_real_ts,
            location=self._location,
            weather=self._weather,
            energy=self._energy,
            hunger=self._hunger,
            npcs={npc["npc_id"]: npc for npc in self._npcs},
            recent_events=[e.to_dict() for e in self._events[-20:]]
        )
        
        result = self._store.save(state_data)
        if result:
            logger.info(f"世界状态已保存: version={self._version}")
        return result
    
    def _load_from_store(self) -> bool:
        """
        从存储加载世界状态
        
        Returns:
            是否加载成功
        """
        state_data = self._store.load()
        if not state_data:
            logger.info("使用默认世界状态")
            return False
        
        try:
            self._version = state_data.world_version
            
            if state_data.world_datetime:
                self._clock.world_datetime = datetime.fromisoformat(state_data.world_datetime)
            self._clock.tick_minutes = state_data.tick_minutes
            self._clock.real_tick_seconds = state_data.real_tick_seconds
            self._clock.last_tick_real_ts = state_data.last_tick_real_ts
            
            self._location = state_data.location
            self._weather = state_data.weather
            self._energy = state_data.energy
            self._hunger = state_data.hunger
            
            if state_data.npcs:
                self._npcs = list(state_data.npcs.values())
            
            self._last_time_period = self._clock.get_time_period()
            self._last_weather = self._weather
            
            logger.info(f"世界状态已加载: version={self._version}, time={self._clock.get_world_time_str()}")
            return True
            
        except Exception as e:
            logger.error(f"加载世界状态失败: {e}")
            return False
    
    def get_version(self) -> int:
        """获取世界版本"""
        return self._version
    
    def get_save_info(self) -> Dict[str, Any]:
        """获取保存信息"""
        return self._store.get_save_info()
