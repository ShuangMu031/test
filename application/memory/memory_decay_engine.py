"""
记忆衰减引擎

V9 三层记忆系统：
定时衰减事件记忆，清理低价值事件，可压缩为摘要。

衰减规则：
- retention_score = 0.45 * importance + 0.45 * emotional_weight + 0.10 * revisit_bonus
- current_score = retention_score - decay_rate * days_passed
- 情绪越重，删得越慢

删除阈值：
- current_score < 0.20: 可删除
- 0.20 <= score < 0.35: 转为摘要
- >= 0.35: 继续保留

衰减率：
- 普通事件: 0.05
- 中等情绪事件: 0.03
- 高情绪事件: 0.015
- 高情绪 + 高关系影响事件: 0.01
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from .memory_document_store import (
    MemoryDocumentStore,
    EpisodicEvent
)

logger = logging.getLogger(__name__)


class MemoryDecayEngine:
    """
    记忆衰减引擎
    
    职责：
    1. 定时扫描事件记忆
    2. 应用衰减公式计算当前分数
    3. 执行删除/压缩/保留决策
    4. 记录衰减日志
    """
    
    DELETE_THRESHOLD = 0.20
    COMPRESS_THRESHOLD = 0.35
    
    DECAY_RATES = {
        "normal": 0.05,
        "medium_emotion": 0.03,
        "high_emotion": 0.015,
        "high_emotion_relation": 0.01
    }
    
    def __init__(
        self,
        document_store: MemoryDocumentStore,
        check_interval_minutes: int = 60
    ):
        self.document_store = document_store
        self.check_interval_minutes = check_interval_minutes
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        self._decay_log: List[Dict[str, Any]] = []
    
    async def start(self) -> None:
        """启动衰减引擎"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._decay_loop())
        logger.info(f"记忆衰减引擎启动，检查间隔: {self.check_interval_minutes}分钟")
    
    async def stop(self) -> None:
        """停止衰减引擎"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("记忆衰减引擎停止")
    
    async def _decay_loop(self) -> None:
        """衰减循环"""
        while self._running:
            try:
                await self.run_decay_cycle()
            except Exception as e:
                logger.error(f"衰减周期执行失败: {e}")
            
            await asyncio.sleep(self.check_interval_minutes * 60)
    
    async def run_decay_cycle(self) -> Dict[str, Any]:
        """
        执行一次衰减周期
        
        Returns:
            衰减报告
        """
        logger.info("开始记忆衰减周期")
        
        report = {
            "started_at": datetime.now().isoformat(),
            "deleted": [],
            "compressed": [],
            "retained": [],
            "errors": []
        }
        
        events = list(self.document_store._episodic_events.values())
        
        for event in events:
            if event.status != "active":
                continue
            
            try:
                result = self._process_event_decay(event)
                
                if result["action"] == "deleted":
                    report["deleted"].append(result)
                elif result["action"] == "compressed":
                    report["compressed"].append(result)
                else:
                    report["retained"].append(result)
                    
            except Exception as e:
                report["errors"].append({
                    "event_id": event.event_id,
                    "error": str(e)
                })
                logger.error(f"处理事件衰减失败: {event.event_id}, {e}")
        
        report["completed_at"] = datetime.now().isoformat()
        report["summary"] = {
            "total_events": len(events),
            "deleted_count": len(report["deleted"]),
            "compressed_count": len(report["compressed"]),
            "retained_count": len(report["retained"])
        }
        
        self._decay_log.append(report)
        
        if len(self._decay_log) > 100:
            self._decay_log = self._decay_log[-100:]
        
        logger.info(
            f"衰减周期完成: 删除={len(report['deleted'])}, "
            f"压缩={len(report['compressed'])}, 保留={len(report['retained'])}"
        )
        
        return report
    
    def _process_event_decay(self, event: EpisodicEvent) -> Dict[str, Any]:
        """
        处理单个事件的衰减
        
        Args:
            event: 事件记忆
            
        Returns:
            处理结果
        """
        days_passed = (datetime.now() - event.created_at).days
        
        event.calculate_retention_score()
        current_score = event.apply_decay(days_passed)
        
        result = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "summary": event.summary[:50] + "..." if len(event.summary) > 50 else event.summary,
            "retention_score": event.retention_score,
            "current_score": current_score,
            "days_passed": days_passed,
            "action": "retained"
        }
        
        if current_score < self.DELETE_THRESHOLD:
            self._delete_event(event)
            result["action"] = "deleted"
            logger.debug(f"删除事件: {event.event_id}, score={current_score:.3f}")
            
        elif current_score < self.COMPRESS_THRESHOLD:
            self._compress_event(event)
            result["action"] = "compressed"
            logger.debug(f"压缩事件: {event.event_id}, score={current_score:.3f}")
        
        return result
    
    def _delete_event(self, event: EpisodicEvent) -> None:
        """删除事件"""
        event.status = "deleted"
        
        if event.event_id in self.document_store._episodic_events:
            del self.document_store._episodic_events[event.event_id]
    
    def _compress_event(self, event: EpisodicEvent) -> None:
        """压缩事件为摘要"""
        event.status = "compressed"
        
        compressed_summary = self._generate_compressed_summary(event)
        event.summary = compressed_summary
        event.metadata["compressed_at"] = datetime.now().isoformat()
        event.metadata["original_importance"] = event.importance
    
    def _generate_compressed_summary(self, event: EpisodicEvent) -> str:
        """生成压缩摘要"""
        emotion_str = ""
        if event.emotion:
            primary = event.emotion.get("primary", "")
            intensity = event.emotion.get("intensity", 0)
            emotion_str = f"[{primary}({intensity:.1f})]"
        
        participants_str = ""
        if event.participants:
            participants_str = f"涉及:{'/'.join(event.participants[:3])}"
        
        summary = event.summary
        if len(summary) > 100:
            summary = summary[:100] + "..."
        
        return f"{emotion_str} {summary} {participants_str}".strip()
    
    def get_event_decay_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        获取事件衰减状态
        
        Args:
            event_id: 事件ID
            
        Returns:
            衰减状态信息
        """
        event = self.document_store.get_event(event_id)
        if not event:
            return None
        
        days_passed = (datetime.now() - event.created_at).days
        current_score = event.apply_decay(days_passed)
        
        return {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "status": event.status,
            "retention_score": event.retention_score,
            "current_score": current_score,
            "decay_rate": event.decay_rate,
            "days_passed": days_passed,
            "will_delete_in_days": self._estimate_delete_days(current_score, event.decay_rate),
            "will_compress_in_days": self._estimate_compress_days(current_score, event.decay_rate)
        }
    
    def _estimate_delete_days(self, current_score: float, decay_rate: float) -> Optional[int]:
        """估算删除天数"""
        if decay_rate <= 0:
            return None
        
        score_to_delete = current_score - self.DELETE_THRESHOLD
        if score_to_delete <= 0:
            return 0
        
        return int(score_to_delete / decay_rate)
    
    def _estimate_compress_days(self, current_score: float, decay_rate: float) -> Optional[int]:
        """估算压缩天数"""
        if decay_rate <= 0:
            return None
        
        score_to_compress = current_score - self.COMPRESS_THRESHOLD
        if score_to_compress <= 0:
            return 0
        
        return int(score_to_compress / decay_rate)
    
    def get_decay_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取衰减日志"""
        return self._decay_log[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        events = list(self.document_store._episodic_events.values())
        
        active_events = [e for e in events if e.status == "active"]
        compressed_events = [e for e in events if e.status == "compressed"]
        
        avg_score = 0
        if active_events:
            total_score = sum(e.retention_score for e in active_events)
            avg_score = total_score / len(active_events)
        
        return {
            "running": self._running,
            "check_interval_minutes": self.check_interval_minutes,
            "total_events": len(events),
            "active_events": len(active_events),
            "compressed_events": len(compressed_events),
            "average_retention_score": round(avg_score, 3),
            "decay_cycles_run": len(self._decay_log)
        }
    
    def force_decay_check(self) -> Dict[str, Any]:
        """
        强制执行衰减检查
        
        同步方法，用于测试或手动触发
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(self.run_decay_cycle())
                return {"status": "scheduled"}
            else:
                return loop.run_until_complete(self.run_decay_cycle())
        except RuntimeError:
            return asyncio.run(self.run_decay_cycle())
    
    def predict_decay(
        self,
        importance: float,
        emotional_weight: float,
        relationship_impact: float = 0.0
    ) -> Dict[str, Any]:
        """
        预测衰减情况
        
        Args:
            importance: 重要性
            emotional_weight: 情绪权重
            relationship_impact: 关系影响
            
        Returns:
            预测结果
        """
        retention_score = 0.45 * importance + 0.45 * emotional_weight + 0.10
        
        if emotional_weight >= 0.8 and relationship_impact >= 0.5:
            decay_rate = self.DECAY_RATES["high_emotion_relation"]
        elif emotional_weight >= 0.7:
            decay_rate = self.DECAY_RATES["high_emotion"]
        elif emotional_weight >= 0.5:
            decay_rate = self.DECAY_RATES["medium_emotion"]
        else:
            decay_rate = self.DECAY_RATES["normal"]
        
        days_to_compress = int((retention_score - self.COMPRESS_THRESHOLD) / decay_rate) if decay_rate > 0 else -1
        days_to_delete = int((retention_score - self.DELETE_THRESHOLD) / decay_rate) if decay_rate > 0 else -1
        
        return {
            "retention_score": round(retention_score, 3),
            "decay_rate": decay_rate,
            "predicted_days_to_compress": max(0, days_to_compress),
            "predicted_days_to_delete": max(0, days_to_delete),
            "category": self._categorize_event(emotional_weight, relationship_impact)
        }
    
    def _categorize_event(
        self,
        emotional_weight: float,
        relationship_impact: float
    ) -> str:
        """分类事件"""
        if emotional_weight >= 0.8 and relationship_impact >= 0.5:
            return "高情绪+高关系影响"
        elif emotional_weight >= 0.7:
            return "高情绪事件"
        elif emotional_weight >= 0.5:
            return "中等情绪事件"
        else:
            return "普通事件"
