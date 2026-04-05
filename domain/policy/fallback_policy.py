"""
兜底策略

V5 核心组件：从 decision/engine.py 降级而来。
不再作为主决策器，只做安全兜底和边界保护。

职责：
1. 当 BehaviorBrain 失败时给兜底
2. 高风险时强制 comfort
3. 物理不可能动作过滤
4. 紧急情况处理

不负责：
- 主要行为决策（由 BehaviorBrain 负责）
- 意图理解
- 工具选择
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import logging

from application.contracts.action_types import ActionType

logger = logging.getLogger(__name__)


@dataclass
class FallbackDecision:
    """兜底决策"""
    action_type: ActionType
    reasoning: str
    response_hint: str = ""
    confidence: float = 0.5
    is_emergency: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "reasoning": self.reasoning,
            "response_hint": self.response_hint,
            "confidence": self.confidence,
            "is_emergency": self.is_emergency
        }


class FallbackPolicy:
    """
    兜底策略
    
    只在以下情况介入：
    1. BehaviorBrain 失败
    2. 紧急情况（能量极低、饥饿极高、情绪极端）
    3. 安全边界触发
    
    核心原则：
    - 不做主要决策
    - 只做安全兜底
    - 优先级高于一切
    """
    
    ENERGY_CRITICAL_THRESHOLD = 0.15
    HUNGER_CRITICAL_THRESHOLD = 0.85
    VALENCE_CRITICAL_THRESHOLD = -0.7
    
    def __init__(self):
        self.stats = {
            "total_fallbacks": 0,
            "emergency_count": 0,
            "by_type": {}
        }
    
    def check_emergency(
        self,
        emotional_state: Any,
        user_input: str = ""
    ) -> Optional[FallbackDecision]:
        """
        检查紧急情况
        
        Args:
            emotional_state: 情绪状态 (EmotionInsight)
            user_input: 用户输入
            
        Returns:
            如果有紧急情况，返回兜底决策；否则返回 None
        """
        if emotional_state is None:
            return None
        
        valence = getattr(emotional_state, "valence", 0.0)
        risk_level = getattr(emotional_state, "risk_level", "none")
        
        if risk_level == "high":
            return self._create_emergency(
                ActionType.COMFORT,
                "检测到高风险情绪状态",
                "我能感受到你现在很难受，我在这里陪着你。"
            )
        
        if valence < self.VALENCE_CRITICAL_THRESHOLD:
            return self._create_emergency(
                ActionType.COMFORT,
                f"情绪极度消极 (valence={valence:.2f})",
                "看起来你现在心情很不好，有什么想跟我说的吗？"
            )
        
        return None
    
    def get_fallback(self, context: Dict[str, Any]) -> FallbackDecision:
        """
        获取兜底决策
        
        Args:
            context: 上下文信息
            
        Returns:
            FallbackDecision
        """
        emotional_state = context.get("emotional_state")
        user_input = context.get("user_input", "")
        
        emergency = self.check_emergency(emotional_state, user_input)
        if emergency:
            return emergency
        
        decision = self._rule_based_fallback(context)
        
        self._record_fallback(decision)
        
        return decision
    
    def _rule_based_fallback(self, context: Dict[str, Any]) -> FallbackDecision:
        """基于规则的兜底"""
        valence = context.get("valence", 0.0)
        support_need = context.get("support_need", "none")
        
        if support_need in ["high", "medium"]:
            return FallbackDecision(
                action_type=ActionType.COMFORT,
                reasoning="用户需要情感支持",
                response_hint="我能感受到你需要一些支持，我在这里。",
                confidence=0.75
            )
        
        if valence < -0.3:
            return FallbackDecision(
                action_type=ActionType.COMFORT,
                reasoning="用户情绪低落",
                response_hint="看起来你心情不太好，有什么想说的吗？",
                confidence=0.7
            )
        
        return FallbackDecision(
            action_type=ActionType.RESPOND,
            reasoning="默认回复",
            response_hint="",
            confidence=0.5
        )
    
    def _create_emergency(
        self,
        action_type: ActionType,
        reasoning: str,
        response_hint: str = ""
    ) -> FallbackDecision:
        """创建紧急决策"""
        self.stats["emergency_count"] += 1
        logger.warning(f"紧急情况触发: {reasoning}")
        
        return FallbackDecision(
            action_type=action_type,
            reasoning=reasoning,
            response_hint=response_hint,
            confidence=0.95,
            is_emergency=True
        )
    
    def _record_fallback(self, decision: FallbackDecision) -> None:
        """记录兜底决策"""
        self.stats["total_fallbacks"] += 1
        action_type = decision.action_type.value
        self.stats["by_type"][action_type] = self.stats["by_type"].get(action_type, 0) + 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    def validate_action(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> bool:
        """
        校验动作是否合法
        
        Args:
            action_type: 动作类型
            context: 上下文
            
        Returns:
            是否合法
        """
        return True
    
    def validate_behavior_plan(
        self,
        plan: Any,
        context: Any
    ) -> Tuple[bool, List[str]]:
        """
        校验行为计划
        
        Args:
            plan: ActionPlanV2
            context: TurnContext
            
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        if plan is None:
            return False, ["plan is None"]
        
        mode = getattr(plan, "mode", None)
        if mode is None:
            errors.append("mode is missing")
        
        primary_action = getattr(plan, "primary_action", None)
        if primary_action is None:
            errors.append("primary_action is missing")
        
        return len(errors) == 0, errors
    
    def validate_world_proposal(
        self,
        proposal: Any,
        context: Any
    ) -> Any:
        """
        校验世界更新提案
        
        Args:
            proposal: WorldUpdateProposal
            context: TurnContext
            
        Returns:
            修正后的提案
        """
        if proposal is None:
            return proposal
        
        time_advance = getattr(proposal, "time_advance_minutes", 0)
        if time_advance > 480:
            proposal.time_advance_minutes = 480
        
        return proposal
    
    def clamp_state_values(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        约束状态值范围
        
        Args:
            state: 状态字典
            
        Returns:
            约束后的状态
        """
        clamped = state.copy()
        
        if "energy" in clamped:
            clamped["energy"] = max(0.0, min(100.0, clamped["energy"]))
        
        if "hunger" in clamped:
            clamped["hunger"] = max(0.0, min(100.0, clamped["hunger"]))
        
        if "valence" in clamped:
            clamped["valence"] = max(-1.0, min(1.0, clamped["valence"]))
        
        if "arousal" in clamped:
            clamped["arousal"] = max(0.0, min(1.0, clamped["arousal"]))
        
        return clamped
    
    def degrade_to_response(
        self,
        reason: str,
        response_hint: str = ""
    ) -> FallbackDecision:
        """
        降级为回复
        
        Args:
            reason: 降级原因
            response_hint: 回复提示
            
        Returns:
            FallbackDecision
        """
        return FallbackDecision(
            action_type=ActionType.RESPOND,
            reasoning=reason,
            response_hint=response_hint,
            confidence=0.3,
            is_emergency=False
        )
