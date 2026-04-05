"""
新闻工具

V6 统一工具协议：
- 所有返回都包含 tool_name 和 source
- 每条新闻统一字段：id, title, category, source, summary, description, publish_time
"""

from typing import Dict, Any, List
from datetime import datetime
import random

from infrastructure.tools.base import BaseTool, ToolResult, ToolType


class NewsTool(BaseTool):
    """新闻查询工具"""
    
    @property
    def name(self) -> str:
        return "news"
    
    @property
    def description(self) -> str:
        return "查询最新新闻资讯"
    
    @property
    def tool_type(self) -> ToolType:
        return ToolType.NEWS
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._mock_news = [
            {
                "title": "人工智能技术持续突破，大模型应用场景不断拓展",
                "category": "科技",
                "source": "科技日报",
                "summary": "最新研究表明，大语言模型在多个领域展现出强大的应用潜力..."
            },
            {
                "title": "全球气候峰会达成新协议，各国承诺加速减排",
                "category": "国际",
                "source": "环球时报",
                "summary": "在最新一轮气候峰会上，各国代表就减排目标达成共识..."
            },
            {
                "title": "新能源汽车销量创新高，市场渗透率持续提升",
                "category": "财经",
                "source": "经济观察报",
                "summary": "数据显示，今年新能源汽车销量同比增长显著..."
            },
            {
                "title": "健康生活方式受关注，运动健身成为新风尚",
                "category": "健康",
                "source": "健康时报",
                "summary": "越来越多的人开始重视健康生活方式..."
            },
            {
                "title": "教育改革深入推进，素质教育理念深入人心",
                "category": "教育",
                "source": "教育周刊",
                "summary": "新课程改革方案出台，强调学生综合素质培养..."
            }
        ]
    
    async def execute(self, category: str = None, limit: int = 5, **kwargs) -> ToolResult:
        """
        查询新闻
        
        Args:
            category: 新闻类别（科技、国际、财经、健康、教育等）
            limit: 返回数量
            
        Returns:
            新闻列表
        """
        try:
            news_list = self._get_news_data(category, limit)
            
            return ToolResult(
                success=True,
                data=news_list,
                tool_name=self.name,
                source="news_tool"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                tool_name=self.name,
                source="news_tool"
            )
    
    def _get_news_data(self, category: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """获取新闻数据"""
        news_list = []
        
        if category:
            filtered = [n for n in self._mock_news if n["category"] == category]
            news_list = filtered if filtered else self._mock_news.copy()
        else:
            news_list = self._mock_news.copy()
        
        random.shuffle(news_list)
        news_list = news_list[:limit]
        
        result = []
        for news in news_list:
            result.append({
                "id": f"news_{hash(news['title']) % 10000}",
                "title": news["title"],
                "category": news["category"],
                "source": news["source"],
                "summary": news["summary"],
                "description": news.get("description", news["summary"]),
                "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "新闻类别（科技、国际、财经、健康、教育等）",
                        "enum": ["科技", "国际", "财经", "健康", "教育", None]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回新闻数量",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": []
            }
        }
