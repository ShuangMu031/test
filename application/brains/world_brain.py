"""
世界脑

V9 改版：世界状态提案和内容判断

改进：
1. LLM 优先输出结构化提案
2. Fallback 简化为最保守输出
3. 不再依赖关键词表驱动
4. 单一结构返回（移除 side-effect）
5. 默认时间推进为 0
6. 接入 world_runtime 而不是 world_service
"""

from typing import Any, Dict, List, Optional
import logging
import json

from .base import BaseBrain
from application.contracts import (
    WorldUpdateProposal,
    WorldContentProposal,
    WorldBrainOutput
)

logger = logging.getLogger(__name__)


WORLD_SCHEMA = {
    "type": "object",
    "properties": {
        "time_advance_minutes": {"type": "integer", "minimum": 0, "maximum": 1440},
        "suggested_location": {"type": "string"},
        "npc_context_hint": {"type": "string"},
        "world_commit_needed": {"type": "boolean"},
        "user_is_asking_world_content": {"type": "boolean"},
        "content_types_needed": {
            "type": "array",
            "items": {"type": "string"}
        },
        "content_category": {"type": "string"},
        "retrieval_query": {"type": "string"},
        "change_trigger": {"type": "string"},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"}
    },
    "required": ["time_advance_minutes", "world_commit_needed"]
}


class WorldBrain(BaseBrain):
    """
    世界脑
    
    V9 职责：
    1. 提出世界状态更新建议
    2. 判断用户是否询问世界内容
    3. 提供世界上下文提示
    
    改进：
    - LLM 优先输出结构化提案
    - Fallback 简化为最保守输出
    - 不再依赖关键词表驱动
    - 单一结构返回
    - 默认时间推进为 0
    - 接入 world_runtime
    """
    
    def __init__(self, llm=None, world_runtime=None, world_content_service=None):
        self.llm = llm
        self.world_runtime = world_runtime
        self.world_content_service = world_content_service
    
    @property
    def name(self) -> str:
        return "world"
    
    async def process(self, context: Any) -> WorldBrainOutput:
        """处理世界"""
        if self.llm:
            try:
                proposal = await self._llm_decide(context)
                if proposal:
                    output = self._build_output_from_llm(proposal)
                    
                    context.record_telemetry(
                        "world",
                        time_advance_minutes=output.world_update_proposal.time_advance_minutes,
                        world_commit_needed=output.world_update_proposal.world_commit_needed,
                        should_read_world_content=output.should_read_world_content,
                        confidence=output.world_update_proposal.confidence,
                        change_trigger=output.world_update_proposal.change_trigger
                    )
                    
                    actions = []
                    interactions = []
                    
                    if output.world_update_proposal.time_advance_minutes > 0:
                        actions.append(f"推进时间 {output.world_update_proposal.time_advance_minutes} 分钟")
                        interactions.append("→ world_runtime")
                    
                    if output.world_update_proposal.suggested_location:
                        actions.append(f"建议移动到 {output.world_update_proposal.suggested_location}")
                        interactions.append("→ world_runtime")
                    
                    if output.should_read_world_content:
                        actions.append("读取世界内容")
                        interactions.append("→ world_content_service")
                    
                    context.record_monologue(
                        "world",
                        monologue=f"世界状态分析: 时间推进={output.world_update_proposal.time_advance_minutes}分钟, 需要更新={output.world_update_proposal.world_commit_needed}, 读取内容={output.should_read_world_content}",
                        actions=actions,
                        interactions=interactions
                    )
                    
                    return output
            except Exception as e:
                logger.warning(f"LLM 世界决策失败，使用 fallback: {e}")
        
        fallback_output = self._fallback_decide()
        
        context.record_telemetry(
            "world",
            time_advance_minutes=0,
            world_commit_needed=False,
            should_read_world_content=False,
            confidence=0.3,
            change_trigger="fallback"
        )
        
        context.record_monologue(
            "world",
            monologue="使用 fallback 最保守输出",
            actions=["无世界更新"],
            interactions=[]
        )
        
        return fallback_output
    
    async def _llm_decide(self, context: Any) -> Optional[Dict[str, Any]]:
        """LLM 结构化决策"""
        prompt = self._build_decision_prompt(context)
        
        try:
            response = await self.llm.generate(prompt)
            
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error(f"LLM 世界决策解析失败: {e}")
        
        return None
    
    def _build_decision_prompt(self, context: Any) -> str:
        """
        构建决策提示
        
        V9 改进：
        - 使用 world_snapshot 替代 world_state
        - 使用 recent_world_events 替代 recent_events
        - 更清晰的判断逻辑
        """
        world_summary = ""
        world_snapshot = getattr(context, "world_snapshot", None)
        if world_snapshot:
            world_summary = f"""
当前世界状态：
- 能量: {getattr(world_snapshot, 'energy', 70.0):.0f}%
- 饥饿: {getattr(world_snapshot, 'hunger', 0.0):.0f}%
- 位置: {getattr(world_snapshot, 'location', '宿舍')}
"""
        
        recent_events_summary = "无最近事件"
        recent_world_events = getattr(context, "recent_world_events", None)
        if recent_world_events:
            lines = []
            for evt in recent_world_events[:3]:
                if isinstance(evt, dict):
                    title = evt.get("title", str(evt))
                else:
                    title = getattr(evt, "title", None) or str(evt)
                lines.append(f"- {title}")
            if lines:
                recent_events_summary = "最近事件：\n" + "\n".join(lines)
        
        world_content_summary = "无现有世界内容"
        world_content_items = getattr(context, "world_content_items", None)
        if world_content_items:
            lines = []
            for item in world_content_items[:3]:
                if isinstance(item, dict):
                    title = item.get("title", str(item))
                else:
                    title = getattr(item, "title", None) or str(item)
                lines.append(f"- {title}")
            if lines:
                world_content_summary = "现有世界内容：\n" + "\n".join(lines)
        
        return f"""请分析以下对话并输出世界更新提案。

用户输入: {context.user_input}

{world_summary}

{recent_events_summary}

{world_content_summary}

请特别判断以下几类需求：
1. 用户是否在询问世界新闻、近期动态、最近发生的事
2. 用户是否在询问某个地点/区域的事件进展
3. 用户是否在询问公告、传闻、简报、天气、城市消息
4. 用户是否只是普通聊天或情感倾诉，此时不要错误地判定为需要读取世界内容

重要：如果用户没有主动涉及虚拟世界、地点、NPC、事件、新闻、公告等内容，且主要是在进行现实聊天或情绪表达，请优先避免触发世界内容读取。

请输出 JSON 格式的世界提案，包含以下字段：
- time_advance_minutes: 时间推进分钟数 (0-1440)，默认为 0，只有明确提到时间变化时才推进
- suggested_location: 建议移动到的位置 (可选)
- npc_context_hint: NPC 上下文提示
- world_commit_needed: 是否需要世界更新 (true/false)
- user_is_asking_world_content: 用户是否询问世界内容 (true/false)
- content_types_needed: 需要的内容类型数组 (bulletin/rumor/brief/weather_feed)
- content_category: 内容分类
- retrieval_query: 检索查询
- change_trigger: 变化触发类型 (explicit_user_intent/implicit_context/ambient_progression/fallback/none)
- confidence: 置信度 (0-1)
- reasoning: 决策理由

重要：默认情况下 time_advance_minutes 应为 0，不要随意推进时间。

只输出 JSON，不要其他内容。"""
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析 LLM 响应"""
        try:
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            return None
    
    def _build_output_from_llm(self, proposal: Dict[str, Any]) -> WorldBrainOutput:
        """从 LLM 输出构建 WorldBrainOutput"""
        world_update = WorldUpdateProposal(
            time_advance_minutes=proposal.get("time_advance_minutes", 0),
            suggested_location=proposal.get("suggested_location"),
            npc_context_hint=proposal.get("npc_context_hint", ""),
            world_commit_needed=proposal.get("world_commit_needed", False),
            reasoning=proposal.get("reasoning", ""),
            change_trigger=proposal.get("change_trigger", "none"),
            confidence=proposal.get("confidence", 0.5)
        )
        
        content_proposal = None
        if proposal.get("user_is_asking_world_content"):
            content_proposal = WorldContentProposal(
                user_is_asking_world_content=True,
                content_types_needed=proposal.get("content_types_needed", []),
                content_category=proposal.get("content_category", ""),
                retrieval_query=proposal.get("retrieval_query", "")
            )
        
        should_apply = world_update.world_commit_needed and world_update.confidence >= 0.5
        should_read = content_proposal is not None and content_proposal.user_is_asking_world_content
        
        return WorldBrainOutput(
            world_update_proposal=world_update,
            world_content_proposal=content_proposal,
            should_apply_update=should_apply,
            should_read_world_content=should_read
        )
    
    def _fallback_decide(self) -> WorldBrainOutput:
        """
        Fallback 最保守输出
        
        V9 简化：只返回最保守的世界输出
        - 不推进时间
        - 不更新位置
        - 不读取世界内容
        - confidence=0.3
        """
        world_update = WorldUpdateProposal(
            time_advance_minutes=0,
            suggested_location=None,
            npc_context_hint="",
            world_commit_needed=False,
            reasoning="fallback: 无效 LLM 世界输出的最保守提案",
            change_trigger="fallback",
            confidence=0.3
        )
        
        content_proposal = WorldContentProposal(
            user_is_asking_world_content=False,
            content_types_needed=[],
            content_category="",
            retrieval_query=""
        )
        
        return WorldBrainOutput(
            world_update_proposal=world_update,
            world_content_proposal=content_proposal,
            should_apply_update=False,
            should_read_world_content=False
        )
