"""
天气工具

V6 统一工具协议：
- 所有返回都包含 tool_name 和 source
- 输出字段统一：temperature, weather, humidity, wind
"""

from typing import Dict, Any
from datetime import datetime
import random

from infrastructure.tools.base import BaseTool, ToolResult, ToolType


class WeatherTool(BaseTool):
    """天气查询工具"""
    
    @property
    def name(self) -> str:
        return "weather"
    
    @property
    def description(self) -> str:
        return "查询指定城市的天气信息"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.WEATHER
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._mock_data = {
            "北京": {"temp": 22, "weather": "晴朗", "humidity": 45, "wind": "北风3级"},
            "上海": {"temp": 26, "weather": "多云", "humidity": 60, "wind": "东南风2级"},
            "广州": {"temp": 30, "weather": "阵雨", "humidity": 75, "wind": "南风2级"},
            "深圳": {"temp": 29, "weather": "晴间多云", "humidity": 70, "wind": "东风2级"},
            "成都": {"temp": 24, "weather": "阴天", "humidity": 55, "wind": "微风"},
            "杭州": {"temp": 25, "weather": "晴朗", "humidity": 50, "wind": "东风2级"},
        }
    
    async def execute(self, city: str = "北京", **kwargs) -> ToolResult:
        """
        查询天气
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息
        """
        try:
            weather_data = self._get_weather_data(city)
            
            return ToolResult(
                success=True,
                data=weather_data,
                tool_name=self.name,
                source="weather_tool"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                tool_name=self.name,
                source="weather_tool"
            )
    
    def _get_weather_data(self, city: str) -> Dict[str, Any]:
        """获取天气数据（模拟或真实API）"""
        if city in self._mock_data:
            base_data = self._mock_data[city].copy()
        else:
            base_data = {
                "temp": random.randint(15, 35),
                "weather": random.choice(["晴朗", "多云", "阴天", "小雨"]),
                "humidity": random.randint(30, 80),
                "wind": "微风"
            }
        
        temp_variation = random.uniform(-2, 2)
        base_data["temp"] = round(base_data["temp"] + temp_variation, 1)
        
        return {
            "city": city,
            "temperature": base_data["temp"],
            "weather": base_data["weather"],
            "humidity": base_data["humidity"],
            "wind": base_data["wind"],
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "suggestion": self._get_suggestion(base_data["temp"], base_data["weather"])
        }
    
    def _get_suggestion(self, temp: float, weather: str) -> str:
        """生成穿衣建议"""
        suggestions = []
        
        if temp < 10:
            suggestions.append("天气较冷，建议穿厚外套")
        elif temp < 20:
            suggestions.append("天气凉爽，适合穿薄外套")
        elif temp < 28:
            suggestions.append("天气舒适，适合穿长袖或薄衫")
        else:
            suggestions.append("天气炎热，建议穿短袖短裤")
        
        if "雨" in weather:
            suggestions.append("记得带伞")
        elif weather == "晴朗":
            suggestions.append("紫外线较强，注意防晒")
        
        return "；".join(suggestions)
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "要查询的城市名称"
                    }
                },
                "required": ["city"]
            }
        }
