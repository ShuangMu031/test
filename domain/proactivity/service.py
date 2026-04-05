"""
主动交互服务

V9 改版：从随机提醒改成条件触发

不再靠随机，而是只看明确条件：
- 长时间沉默
- 高情绪残留
- 世界事件待提醒
- 上轮承诺待跟进
- NPC 关系待推进
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from domain.proactivity.models import (
    ProactiveMessage,
    ProactiveContext,
    ProactiveDecision,
    ProactiveCandidate,
    TriggerType,
    TriggerCondition
)

logger = logging.getLogger(__name__)


class ProactiveInteractionService:
    """
    主动交互服务
    
    V9 改版：主动交互候选生成器
    
    不再直接发送消息，而是生成候选，由门控层决定是否发送。
    """
    
    def __init__(self, memory_service=None, npc_manager=None, world_runtime=None):
        self.memory_service = memory_service
        self.npc_manager = npc_manager
        self.world_runtime = world_runtime
        
        self.last_interaction_time = datetime.now().timestamp()
        self._candidate_counter = 0
        self._cooldown_registry: Dict[str, float] = {}
        
        self._trigger_conditions: List[TriggerCondition] = [
            TriggerCondition(
                trigger_type=TriggerType.IDLE,
                priority=5,
                cooldown=3600
            ),
            TriggerCondition(
                trigger_type=TriggerType.EMOTION,
                priority=8,
                cooldown=1800
            ),
            TriggerCondition(
                trigger_type=TriggerType.WORLD_EVENT,
                priority=6,
                cooldown=7200
            ),
            TriggerCondition(
                trigger_type=TriggerType.PROMISE_FOLLOWUP,
                priority=7,
                cooldown=3600
            ),
            TriggerCondition(
                trigger_type=TriggerType.RELATIONSHIP_PUSH,
                priority=4,
                cooldown=14400
            )
        ]
    
    def _export_cooldowns_remaining(self) -> Dict[str, float]:
        """导出剩余冷却时间"""
        now = datetime.now().timestamp()
        remaining = {}
        expired = []
        
        for key, expires_at in self._cooldown_registry.items():
            left = max(0.0, expires_at - now)
            if left > 0:
                remaining[key] = left
            else:
                expired.append(key)
        
        for key in expired:
            self._cooldown_registry.pop(key, None)
        
        return remaining
    
    def update_last_interaction(self) -> None:
        """更新最后交互时间"""
        self.last_interaction_time = datetime.now().timestamp()
    
    def build_context(
        self,
        last_emotion: str = None,
        last_emotion_valence: float = 0.0,
        last_support_need: str = "none",
        last_world_event: str = None,
        pending_promises: List[str] = None,
        cooldowns: Dict[str, float] = None,
        recent_npc_interactions: List[str] = None
    ) -> ProactiveContext:
        """
        构建主动交互上下文
        
        Args:
            last_emotion: 最后情绪
            last_emotion_valence: 情绪愉悦度
            last_support_need: 支持需求
            last_world_event: 最后世界事件
            pending_promises: 待跟进承诺
            cooldowns: 冷却状态
            recent_npc_interactions: 最近 NPC 交互
            
        Returns:
            ProactiveContext
        """
        current_time = datetime.now().timestamp()
        idle_seconds = current_time - self.last_interaction_time
        
        return ProactiveContext(
            idle_seconds=idle_seconds,
            last_emotion=last_emotion,
            last_emotion_valence=last_emotion_valence,
            last_support_need=last_support_need,
            last_world_event=last_world_event,
            pending_promises=pending_promises or [],
            cooldowns=cooldowns or self._export_cooldowns_remaining(),
            recent_npc_interactions=recent_npc_interactions or [],
            world_snapshot_available=self.world_runtime is not None
        )
    
    async def check_and_generate_candidate(
        self,
        context: ProactiveContext = None,
        **kwargs
    ) -> Optional[ProactiveCandidate]:
        """
        检查并生成主动交互候选
        
        Args:
            context: 主动交互上下文（可选，如果不提供则自动构建）
            **kwargs: 用于构建上下文的参数
            
        Returns:
            ProactiveCandidate 或 None
        """
        if context is None:
            context = self.build_context(**kwargs)
        
        candidates = []
        
        for condition in self._trigger_conditions:
            if condition.should_trigger(context):
                candidate = self._create_candidate(condition, context)
                if candidate:
                    candidate.cooldown_seconds = condition.cooldown
                    candidates.append(candidate)
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda c: c.priority, reverse=True)
        best_candidate = candidates[0]
        
        self._candidate_counter += 1
        
        return best_candidate
    
    def _create_candidate(
        self,
        condition: TriggerCondition,
        context: ProactiveContext
    ) -> Optional[ProactiveCandidate]:
        """根据触发条件创建候选"""
        
        if condition.trigger_type == TriggerType.IDLE:
            return self._create_idle_candidate(context)
        
        if condition.trigger_type == TriggerType.EMOTION:
            return self._create_emotion_candidate(context)
        
        if condition.trigger_type == TriggerType.WORLD_EVENT:
            return self._create_world_event_candidate(context)
        
        if condition.trigger_type == TriggerType.PROMISE_FOLLOWUP:
            return self._create_promise_candidate(context)
        
        if condition.trigger_type == TriggerType.RELATIONSHIP_PUSH:
            return self._create_relationship_candidate(context)
        
        return None
    
    def _create_idle_candidate(self, context: ProactiveContext) -> ProactiveCandidate:
        """创建空闲触发候选"""
        idle_minutes = int(context.idle_seconds / 60)
        
        if idle_minutes > 60:
            suggested = "好久没聊了，最近还好吗？有什么想分享的吗？"
            priority = 6.0
        elif idle_minutes > 30:
            suggested = "有一段时间没说话了，你还在吗？"
            priority = 5.0
        else:
            suggested = "最近怎么样？有什么想聊的吗？"
            priority = 4.0
        
        return ProactiveCandidate(
            trigger_type=TriggerType.IDLE,
            priority=priority,
            reason=f"用户已沉默 {idle_minutes} 分钟",
            suggested_content=suggested,
            needs_emotional_style=True
        )
    
    def _create_emotion_candidate(self, context: ProactiveContext) -> ProactiveCandidate:
        """创建情绪触发候选"""
        emotion = context.last_emotion or "neutral"
        support_need = context.last_support_need
        
        if support_need == "high":
            suggested = "我感觉你可能需要一些支持，有什么我可以帮你的吗？"
            priority = 8.5
        else:
            suggested = "你看起来有些心事，愿意聊聊吗？"
            priority = 7.5
        
        return ProactiveCandidate(
            trigger_type=TriggerType.EMOTION,
            priority=priority,
            reason=f"检测到情绪残留: {emotion}, 支持需求: {support_need}",
            suggested_content=suggested,
            needs_emotional_style=True
        )
    
    def _create_world_event_candidate(self, context: ProactiveContext) -> ProactiveCandidate:
        """创建世界事件触发候选"""
        event = context.last_world_event or "一些事情"
        
        return ProactiveCandidate(
            trigger_type=TriggerType.WORLD_EVENT,
            priority=6.0,
            reason=f"有新的世界事件待提醒: {event}",
            suggested_content=f"对了，{event}，你听说了吗？",
            needs_world_context=True
        )
    
    def _create_promise_candidate(self, context: ProactiveContext) -> ProactiveCandidate:
        """创建承诺跟进候选"""
        promises = context.pending_promises
        
        if not promises:
            return None
        
        first_promise = promises[0]
        
        return ProactiveCandidate(
            trigger_type=TriggerType.PROMISE_FOLLOWUP,
            priority=7.0,
            reason=f"有待跟进的承诺: {first_promise}",
            suggested_content=f"之前你提到的{first_promise}，现在进展怎么样了？",
            needs_emotional_style=True
        )
    
    def _create_relationship_candidate(self, context: ProactiveContext) -> ProactiveCandidate:
        """创建关系推进候选"""
        npc_interactions = context.recent_npc_interactions
        
        if not npc_interactions:
            return None
        
        last_npc = npc_interactions[-1] if npc_interactions else None
        
        return ProactiveCandidate(
            trigger_type=TriggerType.RELATIONSHIP_PUSH,
            priority=4.0,
            reason=f"NPC 关系待推进: {last_npc}",
            suggested_content=f"上次和{last_npc}聊得挺开心的，要不要再聊聊？",
            needs_world_context=True,
            target_npc_id=last_npc
        )
    
    async def check_and_generate(self) -> Optional[ProactiveMessage]:
        """
        兼容旧后台运行时接口
        
        返回旧版 ProactiveMessage
        """
        context = self.build_context()
        candidate = await self.check_and_generate_candidate(context)
        
        if not candidate:
            return None
        
        decision = candidate.to_decision(should_send=True)
        
        return ProactiveMessage(
            content=candidate.suggested_content,
            trigger_type=candidate.trigger_type,
            priority=int(candidate.priority),
            timestamp=datetime.now().timestamp(),
            decision=decision
        )
    
    def is_in_cooldown(self, cooldown_key: str) -> bool:
        """检查是否在冷却中"""
        expires_at = self._cooldown_registry.get(cooldown_key)
        if expires_at is None:
            return False
        return datetime.now().timestamp() < expires_at
    
    def register_cooldown(self, cooldown_key: str, cooldown_seconds: int = 300) -> None:
        """注册冷却"""
        self._cooldown_registry[cooldown_key] = datetime.now().timestamp() + cooldown_seconds
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "last_interaction": self.last_interaction_time,
            "candidate_counter": self._candidate_counter,
            "active_cooldowns": len(self._cooldown_registry),
            "cooldowns": dict(self._cooldown_registry)
        }
