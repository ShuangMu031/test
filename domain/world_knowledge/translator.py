"""
现实到世界转译器

V9 第五批新增：把 RealitySignal 转成 WorldContentItem

核心职责：
1. 按 RealitySignalType 分流
2. 做"现实到虚拟"的映射
3. 打标签、算影响范围、给出世界化文本

现实新闻 -> 抽象化 -> 虚拟世界 bulletin / rumor / brief
现实天气 -> 世界天气通告 / 场景氛围
节日/时间 -> 世界中的庆典 / 作息变化 / NPC状态背景
"""

from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime, timedelta

from application.contracts.reality import (
    RealitySignal,
    RealitySignalType,
    WeatherSignal,
    NewsSignal,
    HolidaySignal
)
from domain.world_knowledge.models import (
    WorldContentItem,
    WorldContentType,
    WorldTopicTag,
    WorldContentImpact,
    ImpactLevel
)

logger = logging.getLogger(__name__)


class RealityToWorldTranslator:
    """
    现实到世界转译器
    
    把现实素材转成虚拟世界内容
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self._news_category_mapping = {
            "technology": [WorldTopicTag.TECHNOLOGY],
            "sports": [WorldTopicTag.SPORTS],
            "entertainment": [WorldTopicTag.ENTERTAINMENT],
            "business": [WorldTopicTag.ECONOMY],
            "science": [WorldTopicTag.TECHNOLOGY],
            "health": [WorldTopicTag.DAILY_LIFE],
            "general": [WorldTopicTag.DAILY_LIFE],
            "local": [WorldTopicTag.LOCAL],
            "world": [WorldTopicTag.GLOBAL]
        }
        
        self._weather_impact_locations = {
            "sunny": ["公园", "操场", "街道"],
            "rainy": ["室内", "宿舍", "食堂"],
            "cloudy": ["图书馆", "教室"],
            "snowy": ["宿舍", "食堂"],
            "stormy": []
        }
    
    def translate(self, signal: RealitySignal) -> List[WorldContentItem]:
        """
        转译现实素材为世界内容
        
        Args:
            signal: 现实素材
            
        Returns:
            世界内容项列表（一个信号可能产生多个内容项）
        """
        if signal.signal_type == RealitySignalType.WEATHER:
            return self._translate_weather(signal)
        
        if signal.signal_type == RealitySignalType.NEWS:
            return self._translate_news(signal)
        
        if signal.signal_type == RealitySignalType.HOLIDAY:
            return self._translate_holiday(signal)
        
        if signal.signal_type == RealitySignalType.TIME:
            return self._translate_time(signal)
        
        logger.warning(f"未知的信号类型: {signal.signal_type}")
        return []
    
    def translate_batch(self, signals: List[RealitySignal]) -> List[WorldContentItem]:
        """
        批量转译
        
        Args:
            signals: 现实素材列表
            
        Returns:
            世界内容项列表
        """
        items = []
        for signal in signals:
            try:
                items.extend(self.translate(signal))
            except Exception as e:
                logger.error(f"转译信号失败 {signal.signal_id}: {e}")
        return items
    
    def _translate_weather(self, signal: RealitySignal) -> List[WorldContentItem]:
        """转译天气信号"""
        items = []
        
        weather = signal.payload.get("weather", "unknown").lower()
        temperature = signal.payload.get("temperature")
        city = signal.payload.get("city", "这里")
        
        weather_text = self._generate_weather_world_text(weather, temperature, city)
        
        affected_locations = self._weather_impact_locations.get(weather, [])
        
        impact = WorldContentImpact(
            level=ImpactLevel.LOW,
            affected_locations=affected_locations,
            affected_npcs=[],
            duration_hours=6,
            decay_rate=0.2
        )
        
        item = WorldContentItem(
            id=f"wc_{uuid.uuid4().hex[:8]}",
            content_type=WorldContentType.WEATHER_FEED,
            title=f"今日天气",
            content=weather_text,
            summary=f"{city}天气：{weather}",
            source_type="weather",
            source_id=signal.signal_id,
            original_signal_id=signal.signal_id,
            topic_tags=[WorldTopicTag.WEATHER],
            impact=impact,
            world_text=weather_text,
            importance=0.3,
            confidence=0.9,
            metadata={
                "weather": weather,
                "temperature": temperature,
                "city": city
            }
        )
        
        items.append(item)
        
        if weather in ["rainy", "snowy", "stormy"]:
            alert_item = self._create_weather_alert(weather, city, signal)
            if alert_item:
                items.append(alert_item)
        
        return items
    
    def _generate_weather_world_text(
        self,
        weather: str,
        temperature: Optional[float],
        city: str
    ) -> str:
        """生成天气世界文本"""
        weather_desc = {
            "sunny": "阳光明媚",
            "rainy": "细雨绵绵",
            "cloudy": "多云",
            "snowy": "飘着雪花",
            "stormy": "风雨交加",
            "foggy": "雾气弥漫"
        }.get(weather, "天气一般")
        
        temp_desc = ""
        if temperature is not None:
            if temperature > 30:
                temp_desc = "，气温较高"
            elif temperature < 10:
                temp_desc = "，气温较低"
            else:
                temp_desc = "，气温宜人"
        
        return f"{city}{weather_desc}{temp_desc}。"
    
    def _create_weather_alert(
        self,
        weather: str,
        city: str,
        signal: RealitySignal
    ) -> Optional[WorldContentItem]:
        """创建天气预警"""
        alert_texts = {
            "rainy": f"听说{city}今天有雨，出门记得带伞。",
            "snowy": f"{city}下雪了，路滑注意安全。",
            "stormy": f"{city}有暴风雨，最好待在室内。"
        }
        
        if weather not in alert_texts:
            return None
        
        return WorldContentItem(
            id=f"wc_{uuid.uuid4().hex[:8]}",
            content_type=WorldContentType.RUMOR,
            title="天气提醒",
            content=alert_texts[weather],
            summary=alert_texts[weather][:30],
            source_type="weather",
            source_id=signal.signal_id,
            original_signal_id=signal.signal_id,
            topic_tags=[WorldTopicTag.WEATHER, WorldTopicTag.DAILY_LIFE],
            impact=WorldContentImpact(
                level=ImpactLevel.MEDIUM,
                affected_locations=[],
                affected_npcs=[],
                duration_hours=12,
                decay_rate=0.1
            ),
            world_text=alert_texts[weather],
            importance=0.5,
            confidence=0.8
        )
    
    def _translate_news(self, signal: RealitySignal) -> List[WorldContentItem]:
        """转译新闻信号"""
        items = []
        
        title = signal.title or "未知新闻"
        raw_text = signal.raw_text or ""
        category = signal.payload.get("category", "general")
        
        topic_tags = self._news_category_mapping.get(category, [WorldTopicTag.DAILY_LIFE])
        
        world_text = self._abstract_news_to_world(title, raw_text, category)
        
        importance = self._calculate_news_importance(signal)
        
        impact = WorldContentImpact(
            level=ImpactLevel.MEDIUM if importance > 0.6 else ImpactLevel.LOW,
            affected_locations=[],
            affected_npcs=[],
            duration_hours=48,
            decay_rate=0.05
        )
        
        content_type = WorldContentType.BULLETIN if importance > 0.7 else WorldContentType.BRIEF
        
        item = WorldContentItem(
            id=f"wc_{uuid.uuid4().hex[:8]}",
            content_type=content_type,
            title=self._worldize_title(title),
            content=world_text,
            summary=world_text[:50] if len(world_text) > 50 else world_text,
            source_type="news",
            source_id=signal.signal_id,
            original_signal_id=signal.signal_id,
            topic_tags=topic_tags,
            impact=impact,
            world_text=world_text,
            importance=importance,
            confidence=0.7,
            metadata={
                "original_title": title,
                "category": category
            }
        )
        
        items.append(item)
        
        return items
    
    def _abstract_news_to_world(
        self,
        title: str,
        raw_text: str,
        category: str
    ) -> str:
        """将新闻抽象化为世界文本"""
        if category == "technology":
            return f"听说最近有些新奇的技术发展，不知道会不会影响到我们的生活。"
        
        if category == "sports":
            return f"最近好像有什么比赛，运动场上应该挺热闹的。"
        
        if category == "entertainment":
            return f"城里好像有什么娱乐活动，有人在讨论呢。"
        
        if category == "health":
            return f"最近大家都在关注健康话题。"
        
        if category == "local":
            return f"附近好像发生了些事情，有人在议论。"
        
        return f"最近外面好像有些新闻，不过具体是什么也不太清楚。"
    
    def _worldize_title(self, title: str) -> str:
        """将标题世界化"""
        if len(title) > 20:
            return "城里的消息"
        return f"关于「{title[:15]}」的传闻"
    
    def _calculate_news_importance(self, signal: RealitySignal) -> float:
        """计算新闻重要性"""
        importance = signal.metadata.get("importance", 0.5)
        
        if isinstance(importance, (int, float)):
            return float(importance)
        
        category = signal.payload.get("category", "general")
        high_importance_categories = ["technology", "health", "local"]
        
        if category in high_importance_categories:
            return 0.6
        
        return 0.4
    
    def _translate_holiday(self, signal: RealitySignal) -> List[WorldContentItem]:
        """转译节日信号"""
        items = []
        
        holiday_name = signal.payload.get("name", "某个节日")
        
        world_text = f"今天是{holiday_name}，城里好像有些特别的气氛。"
        
        impact = WorldContentImpact(
            level=ImpactLevel.HIGH,
            affected_locations=["城区", "广场", "商店"],
            affected_npcs=[],
            duration_hours=24,
            decay_rate=0.0
        )
        
        item = WorldContentItem(
            id=f"wc_{uuid.uuid4().hex[:8]}",
            content_type=WorldContentType.EVENT,
            title=f"{holiday_name}",
            content=world_text,
            summary=f"今天是{holiday_name}",
            source_type="holiday",
            source_id=signal.signal_id,
            original_signal_id=signal.signal_id,
            topic_tags=[WorldTopicTag.CULTURE, WorldTopicTag.SOCIAL],
            impact=impact,
            world_text=world_text,
            importance=0.7,
            confidence=1.0,
            metadata={
                "holiday_name": holiday_name
            }
        )
        
        items.append(item)
        
        return items
    
    def _translate_time(self, signal: RealitySignal) -> List[WorldContentItem]:
        """转译时间信号"""
        items = []
        
        hour = signal.payload.get("hour", datetime.now().hour)
        
        time_context = self._get_time_context(hour)
        
        if time_context:
            item = WorldContentItem(
                id=f"wc_{uuid.uuid4().hex[:8]}",
                content_type=WorldContentType.BRIEF,
                title="时间流逝",
                content=time_context,
                summary=time_context[:30],
                source_type="time",
                source_id=signal.signal_id,
                original_signal_id=signal.signal_id,
                topic_tags=[WorldTopicTag.DAILY_LIFE],
                impact=WorldContentImpact(
                    level=ImpactLevel.LOW,
                    affected_locations=[],
                    affected_npcs=[],
                    duration_hours=1,
                    decay_rate=0.5
                ),
                world_text=time_context,
                importance=0.2,
                confidence=1.0,
                metadata={
                    "hour": hour
                }
            )
            items.append(item)
        
        return items
    
    def _get_time_context(self, hour: int) -> str:
        """获取时间上下文"""
        if 5 <= hour < 9:
            return "清晨的阳光洒在街道上，新的一天开始了。"
        elif 9 <= hour < 12:
            return "上午时分，街道上人来人往。"
        elif 12 <= hour < 14:
            return "午间时分，食堂里飘来饭菜的香味。"
        elif 14 <= hour < 18:
            return "下午的阳光温暖，是个适合活动的好时候。"
        elif 18 <= hour < 21:
            return "傍晚时分，天色渐暗，街灯亮了起来。"
        elif 21 <= hour < 24:
            return "夜深了，大部分地方都安静下来。"
        else:
            return "深夜时分，只有零星的灯光还亮着。"
