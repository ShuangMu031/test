"""
会话清算器

V9 三层记忆系统：
会话结束时执行清算、升级、删除短期记忆。

清算流程：
1. 读取整个短期会话文档
2. 提炼候选（事件、长期事实、未完成跟进点）
3. 升级写入事件记忆/长期记忆
4. 删除短期记忆会话文档

关键思想：
> 短期记忆不是保留本身，而是等待被清算。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .memory_document_store import (
    MemoryDocumentStore,
    ShortTermSession,
    EpisodicEvent,
    LongTermMemory
)
from .memory_router import EventType, LongTermCategory

logger = logging.getLogger(__name__)


class SessionFinalizer:
    """
    会话清算器
    
    职责：
    1. 检测过期/结束的会话
    2. 分析短期记忆内容
    3. 提炼候选事件和长期事实
    4. 执行升级写入
    5. 清理短期记忆
    """
    
    def __init__(
        self,
        document_store: MemoryDocumentStore,
        core_memory=None,
        episodic_memory=None
    ):
        self.document_store = document_store
        self.core_memory = core_memory
        self.episodic_memory = episodic_memory
    
    def finalize_session(self, session_id: str) -> Dict[str, Any]:
        """
        清算指定会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            清算结果报告
        """
        session = self.document_store.get_session(session_id)
        if not session:
            logger.warning(f"会话不存在: {session_id}")
            return {"status": "not_found", "session_id": session_id}
        
        logger.info(f"开始清算会话: {session_id}")
        
        report = {
            "session_id": session_id,
            "status": "completed",
            "started_at": datetime.now().isoformat(),
            "episodic_upgrades": [],
            "long_term_upgrades": [],
            "discarded": [],
            "errors": []
        }
        
        try:
            episodic_candidates = self._extract_episodic_candidates(session)
            for candidate in episodic_candidates:
                try:
                    event = self._upgrade_to_episodic(candidate, session_id)
                    report["episodic_upgrades"].append({
                        "event_id": event.event_id,
                        "summary": event.summary
                    })
                except Exception as e:
                    report["errors"].append(f"升级事件失败: {str(e)}")
                    logger.error(f"升级事件失败: {e}")
            
            long_term_candidates = self._extract_long_term_candidates(session)
            for candidate in long_term_candidates:
                try:
                    memory = self._upgrade_to_long_term(candidate, session_id)
                    report["long_term_upgrades"].append({
                        "memory_id": memory.memory_id,
                        "category": memory.category,
                        "value": memory.value
                    })
                except Exception as e:
                    report["errors"].append(f"升级长期记忆失败: {str(e)}")
                    logger.error(f"升级长期记忆失败: {e}")
            
            self.document_store.delete_session(session_id)
            logger.info(f"会话清算完成: {session_id}")
            
        except Exception as e:
            report["status"] = "failed"
            report["errors"].append(str(e))
            logger.error(f"会话清算失败: {e}")
        
        report["completed_at"] = datetime.now().isoformat()
        return report
    
    def finalize_expired_sessions(self) -> List[Dict[str, Any]]:
        """
        清算所有过期会话
        
        Returns:
            所有清算结果报告列表
        """
        expired_sessions = self.document_store.get_expired_sessions()
        reports = []
        
        for session in expired_sessions:
            report = self.finalize_session(session.session_id)
            reports.append(report)
        
        if reports:
            logger.info(f"清算完成: {len(reports)} 个过期会话")
        
        return reports
    
    def _extract_episodic_candidates(
        self,
        session: ShortTermSession
    ) -> List[Dict[str, Any]]:
        """
        从短期记忆提取事件候选
        
        升级条件：
        - 当前会话内反复围绕同一主题
        - 情绪强度较高
        - 出现关系变化
        - 存在后续跟进必要
        - 有明显场景和参与者
        """
        candidates = []
        
        if not session.emotion_trace:
            return candidates
        
        avg_intensity = sum(
            e.get("intensity", 0) for e in session.emotion_trace
        ) / len(session.emotion_trace) if session.emotion_trace else 0
        
        if avg_intensity >= 0.5:
            dominant_emotion = self._get_dominant_emotion(session.emotion_trace)
            
            summary = self._generate_session_summary(session)
            
            candidates.append({
                "event_type": EventType.EMOTIONAL_INTERACTION.value,
                "summary": summary,
                "importance": min(1.0, avg_intensity + 0.2),
                "emotional_weight": avg_intensity,
                "emotion": {
                    "primary": dominant_emotion,
                    "intensity": avg_intensity
                },
                "participants": self._extract_participants(session.dialogue_window)
            })
        
        if session.pending_promises:
            for promise in session.pending_promises:
                candidates.append({
                    "event_type": EventType.PROMISE.value,
                    "summary": f"待跟进: {promise.get('content', '')}",
                    "importance": 0.6,
                    "emotional_weight": 0.3,
                    "followup_needed": True,
                    "followup_hint": promise.get('content', '')
                })
        
        return candidates
    
    def _extract_long_term_candidates(
        self,
        session: ShortTermSession
    ) -> List[Dict[str, Any]]:
        """
        从短期记忆提取长期记忆候选
        
        升级条件：
        - 用户明确表达偏好/厌恶/习惯/边界
        - 信息稳定且明确
        - 对以后回复有持续影响
        """
        candidates = []
        
        for entry in session.dialogue_window:
            if entry.get("role") != "user":
                continue
            
            content = entry.get("content", "")
            
            preference = self._extract_preference(content)
            if preference:
                candidates.append({
                    "category": LongTermCategory.PREFERENCE.value,
                    "entity": "user",
                    "slot": "likes",
                    "value": preference,
                    "confidence": 0.85,
                    "source": "session_analysis"
                })
            
            dislike = self._extract_dislike(content)
            if dislike:
                candidates.append({
                    "category": LongTermCategory.DISLIKE.value,
                    "entity": "user",
                    "slot": "dislikes",
                    "value": dislike,
                    "confidence": 0.85,
                    "source": "session_analysis"
                })
        
        return candidates
    
    def _upgrade_to_episodic(
        self,
        candidate: Dict[str, Any],
        session_id: str
    ) -> EpisodicEvent:
        """升级到事件记忆"""
        event = self.document_store.create_episodic_event(
            event_type=candidate.get("event_type", "user_interaction"),
            summary=candidate.get("summary", ""),
            importance=candidate.get("importance", 0.5),
            emotional_weight=candidate.get("emotional_weight", 0.5),
            relationship_impact=candidate.get("relationship_impact", 0.0),
            participants=candidate.get("participants", []),
            source_session_id=session_id,
            followup_needed=candidate.get("followup_needed", False),
            followup_hint=candidate.get("followup_hint"),
            emotion=candidate.get("emotion", {})
        )
        
        if self.episodic_memory:
            try:
                from domain.memory import EpisodicEventType
                event_type_str = candidate.get("event_type", "user_interaction")
                try:
                    event_type = EpisodicEventType(event_type_str)
                except ValueError:
                    event_type = EpisodicEventType.USER_INTERACTION
                
                self.episodic_memory.add_event(
                    event_type=event_type,
                    description=candidate.get("summary", ""),
                    importance=candidate.get("importance", 0.5),
                    metadata={"source_session": session_id}
                )
            except Exception as e:
                logger.warning(f"同步到episodic_memory失败: {e}")
        
        return event
    
    def _upgrade_to_long_term(
        self,
        candidate: Dict[str, Any],
        session_id: str
    ) -> LongTermMemory:
        """升级到长期记忆"""
        memory = self.document_store.create_long_term_memory(
            category=candidate.get("category", "preference"),
            entity=candidate.get("entity", "user"),
            slot=candidate.get("slot", "general"),
            value=candidate.get("value", ""),
            confidence=candidate.get("confidence", 0.8),
            source=candidate.get("source", "session_analysis"),
            source_session_id=session_id
        )
        
        if self.core_memory:
            try:
                key = f"{candidate.get('category', 'preference')}_{candidate.get('slot', 'general')}"
                self.core_memory.set_entry(
                    key=key,
                    value=candidate.get("value", ""),
                    category=candidate.get("category", "preference")
                )
            except Exception as e:
                logger.warning(f"同步到core_memory失败: {e}")
        
        return memory
    
    def _get_dominant_emotion(
        self,
        emotion_trace: List[Dict[str, Any]]
    ) -> str:
        """获取主导情绪"""
        if not emotion_trace:
            return "neutral"
        
        emotion_counts = {}
        for trace in emotion_trace:
            emotion = trace.get("primary_emotion", "neutral")
            intensity = trace.get("intensity", 0)
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + intensity
        
        if emotion_counts:
            return max(emotion_counts, key=emotion_counts.get)
        return "neutral"
    
    def _generate_session_summary(self, session: ShortTermSession) -> str:
        """生成会话摘要"""
        parts = []
        
        if session.active_topic:
            parts.append(f"主题: {session.active_topic}")
        
        if session.emotion_trace:
            dominant = self._get_dominant_emotion(session.emotion_trace)
            avg_intensity = sum(
                e.get("intensity", 0) for e in session.emotion_trace
            ) / len(session.emotion_trace)
            parts.append(f"情绪: {dominant}(强度{avg_intensity:.2f})")
        
        if session.pending_promises:
            parts.append(f"待跟进: {len(session.pending_promises)}项")
        
        return " | ".join(parts) if parts else "普通对话会话"
    
    def _extract_participants(
        self,
        dialogue_window: List[Dict[str, Any]]
    ) -> List[str]:
        """提取参与者"""
        participants = ["user"]
        
        keywords = ["朋友", "家人", "同事", "兄弟", "姐妹", "他", "她", "他们"]
        
        for entry in dialogue_window:
            content = entry.get("content", "")
            for kw in keywords:
                if kw in content and kw not in participants:
                    participants.append(kw)
        
        return participants
    
    def _extract_preference(self, content: str) -> Optional[str]:
        """提取偏好"""
        import re
        patterns = [
            r"我(喜欢|爱|最爱)(.+?)(?=[，。！？]|$)",
            r"记住[，,]?\s*(.+?)(?=[，。！？]|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                groups = match.groups()
                if len(groups) > 1:
                    return groups[1].strip()
                elif len(groups) == 1:
                    return groups[0].strip()
        
        return None
    
    def _extract_dislike(self, content: str) -> Optional[str]:
        """提取厌恶"""
        import re
        patterns = [
            r"我(讨厌|恨|最讨厌)(.+?)(?=[，。！？]|$)",
            r"以后(别|不要)(.+?)(?=[，。！？]|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                groups = match.groups()
                if len(groups) > 1:
                    return groups[1].strip()
                elif len(groups) == 1:
                    return groups[0].strip()
        
        return None
    
    def get_finalization_preview(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        获取清算预览
        
        不执行清算，只返回将要执行的操作预览
        """
        session = self.document_store.get_session(session_id)
        if not session:
            return {"status": "not_found", "session_id": session_id}
        
        episodic_candidates = self._extract_episodic_candidates(session)
        long_term_candidates = self._extract_long_term_candidates(session)
        
        return {
            "session_id": session_id,
            "status": "preview",
            "session_info": {
                "active_topic": session.active_topic,
                "emotion_count": len(session.emotion_trace),
                "dialogue_count": len(session.dialogue_window),
                "pending_promises": len(session.pending_promises),
                "salience": session.salience
            },
            "episodic_candidates": [
                {
                    "event_type": c.get("event_type"),
                    "summary": c.get("summary"),
                    "importance": c.get("importance")
                }
                for c in episodic_candidates
            ],
            "long_term_candidates": [
                {
                    "category": c.get("category"),
                    "value": c.get("value"),
                    "confidence": c.get("confidence")
                }
                for c in long_term_candidates
            ]
        }
