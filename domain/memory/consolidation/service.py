"""
记忆固化与遗忘

V9 三层记忆 - 固化层

职责：
- 记忆固化（工作记忆 -> 事件记忆）
- 遗忘机制
- 衰减计算
- 重要性评估
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import math


@dataclass
class ConsolidationRule:
    """固化规则"""
    name: str
    condition: str
    action: str
    threshold: float = 0.5
    enabled: bool = True


class ConsolidationService:
    """
    记忆固化服务
    
    管理记忆的固化、遗忘和衰减
    """
    
    def __init__(self):
        self._rules: List[ConsolidationRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """设置默认规则"""
        self._rules = [
            ConsolidationRule(
                name="emotional_peak",
                condition="emotional_impact > threshold",
                action="consolidate_to_episodic",
                threshold=0.7
            ),
            ConsolidationRule(
                name="repeated_interaction",
                condition="interaction_count > threshold",
                action="consolidate_to_core",
                threshold=3
            ),
            ConsolidationRule(
                name="time_decay",
                condition="days_passed > threshold",
                action="forget",
                threshold=30
            )
        ]
    
    def should_consolidate(
        self,
        memory_entry: Dict[str, Any],
        stats: Dict[str, Any]
    ) -> Optional[str]:
        """判断是否需要固化"""
        for rule in self._rules:
            if not rule.enabled:
                continue
            
            if rule.condition == "emotional_impact > threshold":
                if memory_entry.get("emotional_impact", 0) > rule.threshold:
                    return rule.action
            
            elif rule.condition == "interaction_count > threshold":
                if stats.get("interaction_count", 0) > rule.threshold:
                    return rule.action
            
            elif rule.condition == "days_passed > threshold":
                timestamp = memory_entry.get("timestamp")
                if timestamp:
                    days = (datetime.now() - timestamp).days
                    if days > rule.threshold:
                        return rule.action
        
        return None
    
    def calculate_decay(
        self,
        initial_importance: float,
        days_passed: int,
        decay_rate: float = 0.01
    ) -> float:
        """计算衰减后的重要性"""
        return initial_importance * math.exp(-decay_rate * days_passed)
    
    def evaluate_importance(
        self,
        entry: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """评估记忆重要性"""
        base_importance = entry.get("importance", 0.5)
        emotional_factor = entry.get("emotional_impact", 0) * 0.3
        recency_factor = self._calculate_recency_factor(entry.get("timestamp"))
        relevance_factor = context.get("relevance", 0) * 0.2
        
        return min(1.0, base_importance + emotional_factor + recency_factor + relevance_factor)
    
    def _calculate_recency_factor(self, timestamp: Optional[datetime]) -> float:
        """计算新近度因子"""
        if not timestamp:
            return 0.0
        
        days_passed = (datetime.now() - timestamp).days
        return max(0, 0.1 * (1 - days_passed / 30))
    
    def add_rule(self, rule: ConsolidationRule) -> None:
        """添加规则"""
        self._rules.append(rule)
    
    def get_rules(self) -> List[ConsolidationRule]:
        """获取所有规则"""
        return self._rules
    
    def run_consolidation(
        self,
        working_memory: List[Dict[str, Any]],
        episodic_memory: List[Dict[str, Any]],
        core_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        运行记忆固化（V9 主链接口）
        
        Args:
            working_memory: 工作记忆条目列表
            episodic_memory: 事件记忆条目列表
            core_memory: 核心记忆字典
            
        Returns:
            固化结果，包含：
            - to_episodic: 需要固化到事件记忆的条目
            - to_core: 需要固化到核心记忆的条目
            - to_forget: 需要遗忘的条目
            - stats: 统计信息
        """
        to_episodic = []
        to_core = []
        to_forget = []
        
        for entry in working_memory:
            action = self.should_consolidate(entry, {})
            if action == "consolidate_to_episodic":
                to_episodic.append(entry)
            elif action == "consolidate_to_core":
                to_core.append(entry)
            elif action == "forget":
                to_forget.append(entry)
        
        for entry in episodic_memory:
            action = self.should_consolidate(entry, {})
            if action == "forget":
                to_forget.append(entry)
        
        return {
            "to_episodic": to_episodic,
            "to_core": to_core,
            "to_forget": to_forget,
            "stats": {
                "working_entries": len(working_memory),
                "episodic_entries": len(episodic_memory),
                "core_entries": len(core_memory),
                "consolidated_to_episodic": len(to_episodic),
                "consolidated_to_core": len(to_core),
                "forgotten": len(to_forget)
            }
        }
    
    def process_memory_decision(
        self,
        memory_decision: Dict[str, Any],
        working_memory_service: Any,
        episodic_memory_service: Any,
        core_memory_service: Any
    ) -> Dict[str, Any]:
        """
        处理记忆决策（V9 主链接口）
        
        根据 MemoryDecision 执行实际的记忆写入
        """
        results = {
            "working_written": False,
            "episodic_written": False,
            "core_written": False,
            "consolidation_run": False
        }
        
        if memory_decision.get("write_working", False):
            payload = memory_decision.get("working_payload", {})
            if payload.get("content"):
                working_memory_service.push_user_input(payload["content"])
                results["working_written"] = True
        
        if memory_decision.get("write_episodic", False):
            payload = memory_decision.get("episodic_payload", {})
            if payload.get("description"):
                episodic_memory_service.add_memory_event(
                    description=payload["description"],
                    importance=payload.get("importance", 0.5),
                    emotional_impact=payload.get("emotional_impact", 0.0)
                )
                results["episodic_written"] = True
        
        if memory_decision.get("write_core", False):
            payload = memory_decision.get("core_payload", {})
            if payload:
                if payload.get("identity"):
                    core_memory_service.update_identity(payload["identity"])
                if payload.get("preference"):
                    for key, value in payload["preference"].items():
                        core_memory_service.update_preference(key, value)
                if payload.get("relationship"):
                    for key, value in payload["relationship"].items():
                        core_memory_service.update_relationship(key, value)
                results["core_written"] = True
        
        if memory_decision.get("should_consolidate", False):
            results["consolidation_run"] = True
        
        return results
