"""
总控脑

V7 核心组件：战略裁决器。

V7 改进（基于修改意见第2次整改）：
1. 纳入世界脑输出进行裁决
2. 检测行为脑是否忽略世界提案
3. 世界脑强烈要求读内容时可覆盖动作
4. 输出改强结构化
5. override_action_type 使用 ActionType 枚举
6. 增加 suppress_tool_execution, suppress_npc 标志
"""

from typing import Any, Optional
import logging

from .base import BaseBrain
from application.contracts import SupervisorDecision
from application.contracts.action_types import ActionType

logger = logging.getLogger(__name__)


class SupervisorBrain(BaseBrain):
    """
    总控脑
    
    V7 唯一战略裁决器。
    
    V7 改进：
    - 纳入世界脑输出进行裁决
    - 检测行为脑是否忽略世界提案
    - 世界脑强烈要求读内容时可覆盖动作
    
    职责：
    1. 检测冲突（含世界冲突）
    2. 解决冲突
    3. 选择模型档位
    4. 最终裁决
    5. 覆盖动作类型
    6. 抑制特定行为
    
    输出字段（统一）：
    - conflict_detected: 是否检测到冲突
    - conflict_resolution: 冲突解决策略
    - override_action_type: 覆盖动作类型（ActionType）
    - suppress_tool_execution: 是否抑制工具执行
    - suppress_npc: 是否抑制 NPC 交互
    - final_model_tier: 最终模型档位
    - should_run_final_review: 是否需要最终审查
    - reasoning: 推理说明
    - confidence: 置信度
    """
    
    def __init__(self, llm=None, character_config=None):
        self.llm = llm
        self.character_config = character_config or {}
    
    @property
    def name(self) -> str:
        return "supervisor"
    
    async def process(self, context: Any) -> SupervisorDecision:
        """处理总控"""
        emotion_insight = context.emotion_insight
        behavior_plan = context.behavior_plan_v2
        npc_hint = context.npc_interaction_hint
        world_output = getattr(context, "world_brain_output", None)
        
        conflict_detected = self._detect_conflicts(
            emotion_insight, 
            behavior_plan, 
            npc_hint,
            world_output
        )
        
        conflict_resolution = self._resolve_conflicts(conflict_detected, emotion_insight, behavior_plan)
        
        final_model_tier = self._select_model_tier(emotion_insight, behavior_plan)
        
        override_action_type = self._check_override(
            emotion_insight,
            behavior_plan,
            world_output
        )
        
        suppress_tool_execution = self._should_suppress_tool(conflict_detected, behavior_plan)
        suppress_npc = self._should_suppress_npc(conflict_detected, npc_hint)
        
        override_world_expression_mode = self._check_world_expression_override(
            emotion_insight,
            behavior_plan,
            context
        )
        
        should_run_final_review = conflict_detected or (override_action_type is not None)
        
        confidence = 0.8 if emotion_insight and behavior_plan else 0.5
        
        context.record_telemetry(
            "supervisor",
            conflict_detected=conflict_detected,
            conflict_resolution=conflict_resolution,
            override_action=override_action_type.value if override_action_type else "",
            suppress_tool_execution=suppress_tool_execution,
            suppress_npc=suppress_npc,
            final_model_tier=final_model_tier,
            confidence=confidence
        )
        
        actions = []
        interactions = []
        
        if conflict_detected:
            actions.append(f"检测到冲突: {conflict_resolution}")
            
            involved_brains = []
            if emotion_insight:
                involved_brains.append("emotion")
            if behavior_plan:
                involved_brains.append("behavior")
            if world_output:
                involved_brains.append("world")
            if npc_hint:
                involved_brains.append("npc")
            
            context.add_decision_tension(
                conflict_desc=f"决策冲突: {conflict_resolution}",
                resolution=f"总控裁决: {override_action_type.value if override_action_type else '维持原计划'}",
                involved_brains=involved_brains
            )
        
        if override_action_type:
            actions.append(f"覆盖动作: {override_action_type.value}")
        
        if suppress_tool_execution:
            actions.append("抑制工具执行")
        
        if suppress_npc:
            actions.append("抑制 NPC 交互")
        
        if emotion_insight:
            interactions.append("← emotion_insight")
        if behavior_plan:
            interactions.append("← behavior_plan_v2")
        if world_output:
            interactions.append("← world_brain_output")
        if npc_hint:
            interactions.append("← npc_interaction_hint")
        
        context.record_monologue(
            "supervisor",
            monologue=f"总控裁决: 冲突={conflict_detected}, 模型档位={final_model_tier}, 覆盖动作={override_action_type.value if override_action_type else '无'}",
            actions=actions,
            interactions=interactions
        )
        
        return SupervisorDecision(
            conflict_detected=conflict_detected,
            conflict_resolution=conflict_resolution,
            override_action_type=override_action_type,
            suppress_tool_execution=suppress_tool_execution,
            suppress_npc=suppress_npc,
            final_model_tier=final_model_tier,
            should_run_final_review=should_run_final_review,
            override_world_expression_mode=override_world_expression_mode,
            reasoning="基于综合分析做出裁决",
            confidence=confidence
        )
    
    def _detect_conflicts(
        self,
        emotion_insight: Any,
        behavior_plan: Any,
        npc_hint: Any,
        world_output: Any
    ) -> bool:
        """
        检测冲突
        
        V7 改进：
        - 增加世界冲突检测
        - 检测行为脑是否忽略世界提案
        """
        if not emotion_insight or not behavior_plan:
            return False
        
        support_need = getattr(emotion_insight, "support_need", "none")
        mode = getattr(behavior_plan, "mode", "chat")
        should_involve_npc = getattr(npc_hint, "should_involve_npc", False) if npc_hint else False
        
        if support_need in ["high", "medium"] and mode == "tool":
            return True
        
        if support_need == "high" and should_involve_npc:
            return True
        
        if world_output and behavior_plan:
            should_read_world = getattr(world_output, "should_read_world_content", False)
            should_apply_world = getattr(world_output, "should_apply_update", False)

            primary_action = getattr(behavior_plan, "primary_action", None)
            primary_action_value = getattr(primary_action, "value", str(primary_action)).lower() if primary_action else ""

            world_commit_needed = getattr(behavior_plan, "world_commit_needed", False)

            if should_read_world and primary_action_value not in ["world_content_read", "respond"]:
                logger.debug(f"世界冲突检测: should_read_world={should_read_world}, action={primary_action_value}")
                return True

            if should_apply_world and not world_commit_needed:
                logger.debug(f"世界冲突检测: should_apply_world={should_apply_world}, world_commit_needed={world_commit_needed}")
                return True
        
        return False
    
    def _resolve_conflicts(
        self,
        conflict_detected: bool,
        emotion_insight: Any,
        behavior_plan: Any
    ) -> str:
        """解决冲突"""
        if not conflict_detected:
            return "none"
        
        support_need = getattr(emotion_insight, "support_need", "none") if emotion_insight else "none"
        
        if support_need == "high":
            return "prioritize_comfort"
        elif support_need == "medium":
            return "balance_comfort_and_task"
        else:
            return "follow_behavior_plan"
    
    def _select_model_tier(
        self,
        emotion_insight: Any,
        behavior_plan: Any
    ) -> str:
        """选择模型档位（统一命名：cheap/standard/top）"""
        if not emotion_insight:
            return "standard"
        
        support_need = getattr(emotion_insight, "support_need", "none")
        mode = getattr(behavior_plan, "mode", "chat") if behavior_plan else "chat"
        
        if support_need == "high":
            return "top"
        elif mode == "tool":
            return "cheap"
        else:
            return "standard"
    
    def _check_override(
        self,
        emotion_insight: Any,
        behavior_plan: Any,
        world_output: Any
    ) -> Optional[ActionType]:
        """
        检查是否需要覆盖，返回 override_action_type
        
        V7 改进：
        - 情感安慰优先级高于世界展开
        - 世界脑明确要求读取世界内容时可覆盖
        """
        if not emotion_insight:
            support_need = "none"
        else:
            support_need = getattr(emotion_insight, "support_need", "none")
        
        mode = getattr(behavior_plan, "mode", "chat") if behavior_plan else ""
        
        if support_need == "high":
            return ActionType.COMFORT
        
        if world_output and getattr(world_output, "should_read_world_content", False):
            logger.debug("世界脑要求读取世界内容，覆盖动作")
            return ActionType.WORLD_CONTENT_READ
        
        if support_need == "high" and mode == "tool":
            return ActionType.COMFORT
        
        if support_need == "high" and mode == "npc":
            return ActionType.COMFORT
        
        return None
    
    def _should_suppress_tool(
        self,
        conflict_detected: bool,
        behavior_plan: Any
    ) -> bool:
        """是否抑制工具执行"""
        if not conflict_detected:
            return False
        
        if behavior_plan:
            mode = getattr(behavior_plan, "mode", "chat")
            if mode == "tool":
                return True
        
        return False
    
    def _should_suppress_npc(
        self,
        conflict_detected: bool,
        npc_hint: Any
    ) -> bool:
        """是否抑制 NPC 交互"""
        if not conflict_detected:
            return False
        
        if npc_hint:
            should_involve = getattr(npc_hint, "should_involve_npc", False)
            if should_involve:
                return True
        
        return False
    
    def _check_world_expression_override(
        self,
        emotion_insight: Any,
        behavior_plan: Any,
        context: Any
    ) -> Optional[str]:
        """
        V10: 检查是否需要覆盖世界表达级别
        
        规则：
        - 高支持需求时，强制 suppressed
        - comfort 动作时，强制 suppressed
        - 现实求助类输入时，强制 suppressed
        """
        support_need = getattr(emotion_insight, "support_need", "none") if emotion_insight else "none"
        
        primary_action = getattr(behavior_plan, "primary_action", None) if behavior_plan else None
        primary_action_value = getattr(primary_action, "value", str(primary_action)).lower() if primary_action else ""
        
        if support_need == "high":
            logger.debug("总控: 高支持需求，压制世界表达")
            return "suppressed"
        
        if primary_action_value == "comfort":
            logger.debug("总控: comfort动作，压制世界表达")
            return "suppressed"
        
        user_text = (getattr(context, "user_input", "") or "").strip()
        reality_help_keywords = ["怎么办", "怎么做", "该不该", "我该", "现实", "工作", "家里", "朋友", "父母", "医院"]
        
        if any(k in user_text for k in reality_help_keywords):
            logger.debug("总控: 现实求助类输入，压制世界表达")
            return "suppressed"
        
        return None
