"""
现实素材采集器

V9 第五批新增：真正调用工具层，采集 RealitySignal

职责：
- 调用 NewsTool / WeatherTool 等工具
- 统一生成 RealitySignal
- 不做世界化映射（由 translator 负责）
- 不做 NPC 影响（由 npc_manager 负责）
- 不做 prompt 拼装（由 prompt_builder 负责）
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from application.contracts.reality import (
    RealitySignal,
    RealitySignalType,
    WeatherSignal,
    NewsSignal,
    HolidaySignal
)

logger = logging.getLogger(__name__)


class RealitySourceCollector:
    """
    现实素材采集器
    
    负责从各种工具采集现实素材，统一生成 RealitySignal
    """
    
    def __init__(
        self,
        news_tool=None,
        weather_tool=None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.news_tool = news_tool
        self.weather_tool = weather_tool
        self.config = config or {}
        
        self._default_city = self.config.get("default_city", "北京")
        self._default_news_limit = self.config.get("default_news_limit", 3)
        
        self._last_collection_time: Optional[float] = None
        self._collection_interval = self.config.get("collection_interval", 3600)
        
        self._stats = {
            "total_collections": 0,
            "total_signals": 0,
            "news_collected": 0,
            "weather_collected": 0,
            "holiday_collected": 0
        }
    
    async def collect_signals(self) -> List[RealitySignal]:
        """
        采集所有现实素材
        
        Returns:
            RealitySignal 列表
        """
        signals = []
        
        if self.weather_tool:
            try:
                weather_signals = await self._collect_weather()
                signals.extend(weather_signals)
            except Exception as e:
                logger.error(f"采集天气失败: {e}")
        
        if self.news_tool:
            try:
                news_signals = await self._collect_news()
                signals.extend(news_signals)
            except Exception as e:
                logger.error(f"采集新闻失败: {e}")
        
        try:
            holiday_signals = self._collect_holidays()
            signals.extend(holiday_signals)
        except Exception as e:
            logger.error(f"采集节日失败: {e}")
        
        try:
            time_signal = self._collect_time()
            if time_signal:
                signals.append(time_signal)
        except Exception as e:
            logger.error(f"采集时间失败: {e}")
        
        self._last_collection_time = datetime.now().timestamp()
        self._stats["total_collections"] += 1
        self._stats["total_signals"] += len(signals)
        
        logger.info(f"采集完成，共 {len(signals)} 个现实素材")
        
        return signals
    
    async def _collect_weather(self) -> List[RealitySignal]:
        """采集天气"""
        signals = []
        
        result = await self.weather_tool.execute(city=self._default_city)
        
        if result.success and result.data:
            data = result.data
            
            signal = WeatherSignal(
                title=f"{data.get('city', self._default_city)}天气",
                raw_text=f"{data.get('weather', '未知')}，温度 {data.get('temperature', '?')}°C",
                payload={
                    "weather": data.get("weather", "unknown"),
                    "temperature": data.get("temperature"),
                    "humidity": data.get("humidity"),
                    "wind": data.get("wind"),
                    "city": data.get("city", self._default_city),
                    "suggestion": data.get("suggestion", "")
                },
                source="weather_tool"
            )
            
            signals.append(signal)
            self._stats["weather_collected"] += 1
        
        return signals
    
    async def _collect_news(self) -> List[RealitySignal]:
        """采集新闻"""
        signals = []
        
        result = await self.news_tool.execute(limit=self._default_news_limit)
        
        if result.success and result.data:
            for news_item in result.data:
                signal = NewsSignal(
                    title=news_item.get("title", ""),
                    raw_text=news_item.get("summary", ""),
                    payload={
                        "category": news_item.get("category", "general"),
                        "source": news_item.get("source", ""),
                        "url": news_item.get("url"),
                        "publish_time": news_item.get("publish_time")
                    },
                    source="news_tool",
                    metadata={
                        "news_id": news_item.get("id"),
                        "importance": self._calculate_news_importance(news_item)
                    }
                )
                
                signals.append(signal)
            
            self._stats["news_collected"] += len(signals)
        
        return signals
    
    def _calculate_news_importance(self, news_item: Dict[str, Any]) -> float:
        """计算新闻重要性"""
        category = news_item.get("category", "").lower()
        
        high_importance = ["科技", "technology", "健康", "health"]
        medium_importance = ["财经", "business", "国际", "world"]
        
        if category in high_importance:
            return 0.7
        elif category in medium_importance:
            return 0.5
        else:
            return 0.3
    
    def _collect_holidays(self) -> List[RealitySignal]:
        """采集节日"""
        signals = []
        
        today = datetime.now()
        month = today.month
        day = today.day
        
        holidays = self._get_holidays_for_date(month, day)
        
        for holiday in holidays:
            signal = HolidaySignal(
                title=holiday["name"],
                raw_text=f"今天是{holiday['name']}",
                payload={
                    "name": holiday["name"],
                    "date": today.strftime("%Y-%m-%d"),
                    "type": holiday.get("type", "general")
                },
                source="holiday_calendar"
            )
            
            signals.append(signal)
        
        if signals:
            self._stats["holiday_collected"] += len(signals)
        
        return signals
    
    def _get_holidays_for_date(self, month: int, day: int) -> List[Dict[str, Any]]:
        """获取指定日期的节日"""
        holidays = []
        
        holiday_calendar = {
            (1, 1): [{"name": "元旦", "type": "national"}],
            (2, 14): [{"name": "情人节", "type": "social"}],
            (3, 8): [{"name": "妇女节", "type": "social"}],
            (5, 1): [{"name": "劳动节", "type": "national"}],
            (6, 1): [{"name": "儿童节", "type": "social"}],
            (10, 1): [{"name": "国庆节", "type": "national"}],
            (12, 25): [{"name": "圣诞节", "type": "social"}],
        }
        
        return holiday_calendar.get((month, day), [])
    
    def _collect_time(self) -> Optional[RealitySignal]:
        """采集时间信息"""
        now = datetime.now()
        
        return RealitySignal(
            signal_type=RealitySignalType.TIME,
            title="当前时间",
            raw_text=now.strftime("%Y-%m-%d %H:%M:%S"),
            payload={
                "hour": now.hour,
                "minute": now.minute,
                "weekday": now.weekday(),
                "date": now.strftime("%Y-%m-%d"),
                "time_of_day": self._get_time_of_day(now.hour)
            },
            source="system_clock"
        )
    
    def _get_time_of_day(self, hour: int) -> str:
        """获取时间段"""
        if 5 <= hour < 9:
            return "morning"
        elif 9 <= hour < 12:
            return "forenoon"
        elif 12 <= hour < 14:
            return "noon"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 21:
            return "evening"
        else:
            return "night"
    
    def should_collect(self) -> bool:
        """判断是否需要采集"""
        if self._last_collection_time is None:
            return True
        
        elapsed = datetime.now().timestamp() - self._last_collection_time
        return elapsed >= self._collection_interval
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "last_collection_time": self._last_collection_time,
            "collection_interval": self._collection_interval
        }
