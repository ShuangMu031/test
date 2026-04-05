"""
地图工具

V6 统一工具协议：
- 所有返回都包含 tool_name 和 source
- 统一返回结构：action, query_time, payload
"""

from typing import Dict, Any, List
from datetime import datetime
import math

from infrastructure.tools.base import BaseTool, ToolResult, ToolType


class MapTool(BaseTool):
    """地图查询工具"""
    
    @property
    def name(self) -> str:
        return "map"
    
    @property
    def description(self) -> str:
        return "查询位置信息和路线规划"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.MAP
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._locations = {
            "北京": {"lat": 39.9042, "lng": 116.4074, "description": "中国首都，政治文化中心"},
            "上海": {"lat": 31.2304, "lng": 121.4737, "description": "国际大都市，经济金融中心"},
            "广州": {"lat": 23.1291, "lng": 113.2644, "description": "南方门户，商贸重镇"},
            "深圳": {"lat": 22.5431, "lng": 114.0579, "description": "创新之城，科技高地"},
            "成都": {"lat": 30.5728, "lng": 104.0668, "description": "天府之国，休闲之都"},
            "杭州": {"lat": 30.2741, "lng": 120.1551, "description": "人间天堂，互联网之城"},
            "西安": {"lat": 34.3416, "lng": 108.9398, "description": "古都长安，历史名城"},
            "南京": {"lat": 32.0603, "lng": 118.7969, "description": "六朝古都，文化名城"},
        }
        
        self._pois = {
            "北京": [
                {"name": "故宫", "type": "景点", "rating": 4.8},
                {"name": "天安门广场", "type": "景点", "rating": 4.7},
                {"name": "颐和园", "type": "景点", "rating": 4.6},
                {"name": "北京大学", "type": "教育", "rating": 4.5},
                {"name": "清华大学", "type": "教育", "rating": 4.6},
            ],
            "上海": [
                {"name": "外滩", "type": "景点", "rating": 4.7},
                {"name": "东方明珠", "type": "景点", "rating": 4.5},
                {"name": "迪士尼乐园", "type": "娱乐", "rating": 4.6},
                {"name": "复旦大学", "type": "教育", "rating": 4.5},
            ],
            "成都": [
                {"name": "大熊猫基地", "type": "景点", "rating": 4.8},
                {"name": "宽窄巷子", "type": "景点", "rating": 4.5},
                {"name": "锦里古街", "type": "景点", "rating": 4.4},
            ]
        }
    
    async def execute(self, action: str = "search", **kwargs) -> ToolResult:
        """
        执行地图操作
        
        Args:
            action: 操作类型（search/route/poi）
            **kwargs: 操作参数
            
        Returns:
            操作结果
        """
        query_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        try:
            if action == "search":
                result = await self._search_location(**kwargs)
            elif action == "route":
                result = await self._plan_route(**kwargs)
            elif action == "poi":
                result = await self._search_poi(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"未知操作类型: {action}",
                    tool_name=self.name,
                    source="map_tool",
                    metadata={"action": action, "query_time": query_time}
                )
            
            if result.metadata is None:
                result.metadata = {}
            result.metadata["action"] = action
            result.metadata["query_time"] = query_time
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                tool_name=self.name,
                source="map_tool",
                metadata={"action": action, "query_time": query_time}
            )
    
    async def _search_location(self, location: str = None, **kwargs) -> ToolResult:
        """搜索位置"""
        if not location:
            return ToolResult(
                success=False,
                data=None,
                error="请提供位置名称",
                tool_name=self.name,
                source="map_tool"
            )
        
        if location in self._locations:
            data = self._locations[location].copy()
            data["name"] = location
            
            return ToolResult(
                success=True,
                data={"action": "search", "payload": data},
                tool_name=self.name,
                source="map_tool"
            )
        else:
            return ToolResult(
                success=False,
                data=None,
                error=f"未找到位置: {location}",
                tool_name=self.name,
                source="map_tool"
            )
    
    async def _plan_route(self, origin: str = None, destination: str = None, **kwargs) -> ToolResult:
        """规划路线"""
        if not origin or not destination:
            return ToolResult(
                success=False,
                data=None,
                error="请提供起点和终点",
                tool_name=self.name,
                source="map_tool"
            )
        
        if origin not in self._locations:
            return ToolResult(
                success=False,
                data=None,
                error=f"未找到起点: {origin}",
                tool_name=self.name,
                source="map_tool"
            )
        
        if destination not in self._locations:
            return ToolResult(
                success=False,
                data=None,
                error=f"未找到终点: {destination}",
                tool_name=self.name,
                source="map_tool"
            )
        
        origin_data = self._locations[origin]
        dest_data = self._locations[destination]
        
        distance = self._calculate_distance(
            origin_data["lat"], origin_data["lng"],
            dest_data["lat"], dest_data["lng"]
        )
        
        route_data = {
            "origin": origin,
            "destination": destination,
            "distance_km": round(distance, 1),
            "estimated_time_hours": round(distance / 800 * 10, 1),
            "transport_modes": [
                {"mode": "飞机", "time": f"{int(distance/800)}小时", "cost": f"约{int(distance*0.6)}元"},
                {"mode": "高铁", "time": f"{int(distance/300)}小时", "cost": f"约{int(distance*0.4)}元"},
                {"mode": "自驾", "time": f"{int(distance/100)}小时", "cost": f"约{int(distance*0.8)}元油费"}
            ]
        }
        
        return ToolResult(
            success=True,
            data={"action": "route", "payload": route_data},
            tool_name=self.name,
            source="map_tool"
        )
    
    async def _search_poi(self, city: str = None, poi_type: str = None, **kwargs) -> ToolResult:
        """搜索兴趣点"""
        if not city:
            return ToolResult(
                success=False,
                data=None,
                error="请提供城市名称",
                tool_name=self.name,
                source="map_tool"
            )
        
        if city not in self._pois:
            return ToolResult(
                success=False,
                data=None,
                error=f"未找到城市: {city}",
                tool_name=self.name,
                source="map_tool"
            )
        
        pois = self._pois[city]
        
        if poi_type:
            pois = [p for p in pois if p["type"] == poi_type]
        
        return ToolResult(
            success=True,
            data={
                "action": "poi",
                "payload": {
                    "city": city,
                    "pois": pois,
                    "count": len(pois)
                }
            },
            tool_name=self.name,
            source="map_tool"
        )
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """计算两点之间的距离（公里）"""
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["search", "route", "poi"]
                    },
                    "location": {
                        "type": "string",
                        "description": "位置名称（用于search）"
                    },
                    "origin": {
                        "type": "string",
                        "description": "起点（用于route）"
                    },
                    "destination": {
                        "type": "string",
                        "description": "终点（用于route）"
                    },
                    "city": {
                        "type": "string",
                        "description": "城市名称（用于poi）"
                    },
                    "poi_type": {
                        "type": "string",
                        "description": "兴趣点类型"
                    }
                },
                "required": ["action"]
            }
        }
