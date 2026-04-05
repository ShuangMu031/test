"""
主动消息重写器

V10 新增：把 candidate 重写成一条自然、简短、贴上下文的主动消息

职责：
- 接收 ProactiveCandidate
- 使用 LLM 重写成自然的一句话
- 输出 should_send 和 message
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ProactiveMessageComposer:
    """
    主动消息重写器
    
    V10 新增：
    - 把 candidate 重写成自然的一句话
    - 使用 LLM 进行重写
    - 输出 should_send 和 message
    """
    
    def __init__(self, llm=None, working_memory=None):
        self.llm = llm
        self.working_memory = working_memory
    
    async def compose(self, candidate, context) -> str:
        """
        重写主动消息
        
        Args:
            candidate: ProactiveCandidate
            context: ProactiveContext
            
        Returns:
            重写后的消息内容，如果 should_send 为 False 则返回空字符串
        """
        if not self.llm:
            return candidate.suggested_content
        
        recent_dialogue = []
        if self.working_memory and hasattr(self.working_memory, "get_dialogue_history"):
            history = self.working_memory.get_dialogue_history()
            recent_dialogue = [
                {
                    "role": getattr(x, "role", "unknown"),
                    "content": getattr(x, "content", str(x))
                }
                for x in history[-4:]
            ]
        
        messages = [
            {
                "role": "system",
                "content": (
                    "你要把一条主动消息改写得像真人聊天。"
                    "要求：简短、自然、别像系统提醒、别解释触发机制、别空泛、别连续追问。"
                    "输出 JSON：{\"should_send\": true/false, \"message\": \"...\"}"
                )
            },
            {
                "role": "user",
                "content": f'''触发类型: {candidate.trigger_type.value}
触发原因: {candidate.reason}
候选草稿: {candidate.suggested_content}
最近情绪: {context.last_emotion}
支持需求: {context.last_support_need}
空闲秒数: {int(context.idle_seconds)}
最近对话: {recent_dialogue}

要求：
1. 只写 1 句中文
2. 最好 8-28 个字
3. 能贴上下文就贴，不要编造
4. 不要出现"检测到""系统""提醒""支持需求"等词'''
            }
        ]
        
        try:
            result = await self._call_llm(messages)
            if not result.get("should_send", True):
                return ""
            return (result.get("message") or "").strip()
        except Exception as e:
            logger.warning(f"LLM 重写失败: {e}，使用原始内容")
            return candidate.suggested_content
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        调用 LLM
        
        Args:
            messages: 消息列表
            
        Returns:
            解析后的 JSON 结果
        """
        if hasattr(self.llm, "structured"):
            return await self.llm.structured(
                messages=messages,
                response_format={
                    "type": "object",
                    "properties": {
                        "should_send": {"type": "boolean"},
                        "message": {"type": "string"}
                    },
                    "required": ["should_send", "message"]
                },
                temperature=0.4,
                max_tokens=100
            )
        
        if hasattr(self.llm, "achat"):
            response = await self.llm.achat(messages)
            content = response.content if hasattr(response, "content") else str(response)
        elif hasattr(self.llm, "invoke"):
            response = self.llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)
        else:
            content = str(await self.llm(messages))
        
        import json
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"should_send": True, "message": content}
