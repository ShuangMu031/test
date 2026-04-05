"""
后台运行时

V9 三层记忆系统：
后台任务调度器，支持：
1. 世界状态定时推进
2. 主动消息定时检查
3. 记忆巩固定时检查
4. 会话清算定时检查（5-10分钟空闲会话）
5. 记忆衰减定时执行
"""

from typing import Optional, Callable, Any, Dict
import logging
import asyncio
from datetime import datetime

from domain.proactivity.models import ProactiveMessage, ProactiveContext, ProactiveDecision

logger = logging.getLogger(__name__)


class BackgroundRuntime:
    """
    后台运行时
    
    V9 三层记忆系统：
    - 接入新的主动交互服务
    - 支持新的 ProactiveContext 和 ProactiveDecision
    - 增加记忆巩固检查
    - 增加会话清算检查（5-10分钟空闲会话）
    - 增加记忆衰减引擎
    
    V9 第二批修复：
    - 世界推进使用新接口 enqueue_world_action
    - 记忆巩固传入 memory_services
    """
    
    def __init__(
        self,
        world_service=None,
        proactive_service=None,
        proactive_message_composer=None,
        memory_consolidation_service=None,
        memory_services: Optional[Dict[str, Any]] = None,
        session_finalizer=None,
        memory_decay_engine=None,
        world_tick_interval: float = 60.0,
        proactive_check_interval: float = 300.0,
        consolidation_check_interval: float = 300.0,
        session_check_interval: float = 120.0,
        decay_check_interval: float = 3600.0
    ):
        self.world_service = world_service
        self.proactive_service = proactive_service
        self.proactive_message_composer = proactive_message_composer
        self.memory_consolidation_service = memory_consolidation_service
        self.memory_services = memory_services
        self.session_finalizer = session_finalizer
        self.memory_decay_engine = memory_decay_engine
        
        self.world_tick_interval = world_tick_interval
        self.proactive_check_interval = proactive_check_interval
        self.consolidation_check_interval = consolidation_check_interval
        self.session_check_interval = session_check_interval
        self.decay_check_interval = decay_check_interval
        
        self._world_task: Optional[asyncio.Task] = None
        self._proactive_task: Optional[asyncio.Task] = None
        self._consolidation_task: Optional[asyncio.Task] = None
        self._session_task: Optional[asyncio.Task] = None
        self._decay_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._world_lock = asyncio.Lock()
        
        self._on_proactive_message: Optional[Callable] = None
        
        self._last_emotion: Optional[str] = None
        self._last_support_need: str = "none"
        self._last_world_event: Optional[str] = None
        self._pending_promises: list = []
        self._recent_npc_interactions: list = []
    
    def set_proactive_callback(self, callback: Callable) -> None:
        """设置主动消息回调"""
        self._on_proactive_message = callback
    
    def update_proactive_context(
        self,
        last_emotion: str = None,
        last_support_need: str = None,
        last_world_event: str = None,
        pending_promises: list = None,
        recent_npc_interactions: list = None
    ) -> None:
        """
        更新主动交互上下文
        
        Args:
            last_emotion: 最后情绪
            last_support_need: 支持需求
            last_world_event: 最后世界事件
            pending_promises: 待跟进承诺
            recent_npc_interactions: 最近 NPC 交互
        """
        if last_emotion is not None:
            self._last_emotion = last_emotion
        if last_support_need is not None:
            self._last_support_need = last_support_need
        if last_world_event is not None:
            self._last_world_event = last_world_event
        if pending_promises is not None:
            self._pending_promises = pending_promises
        if recent_npc_interactions is not None:
            self._recent_npc_interactions = recent_npc_interactions
    
    def _build_proactive_context(self) -> ProactiveContext:
        """构建主动交互上下文"""
        if self.proactive_service:
            return self.proactive_service.build_context(
                last_emotion=self._last_emotion,
                last_support_need=self._last_support_need,
                last_world_event=self._last_world_event,
                pending_promises=self._pending_promises,
                recent_npc_interactions=self._recent_npc_interactions
            )
        
        return ProactiveContext(
            last_emotion=self._last_emotion,
            last_support_need=self._last_support_need,
            last_world_event=self._last_world_event,
            pending_promises=self._pending_promises,
            recent_npc_interactions=self._recent_npc_interactions
        )
    
    async def start(self) -> None:
        """启动后台任务"""
        if self._is_running:
            return
        
        self._is_running = True
        logger.info("BackgroundRuntime 启动")
        
        if self.world_service:
            self._world_task = asyncio.create_task(self._world_ticker())
        
        if self.proactive_service:
            self._proactive_task = asyncio.create_task(self._proactive_checker())
        
        if self.memory_consolidation_service:
            self._consolidation_task = asyncio.create_task(self._consolidation_checker())
        
        if self.session_finalizer:
            self._session_task = asyncio.create_task(self._session_checker())
        
        if self.memory_decay_engine:
            self._decay_task = asyncio.create_task(self._decay_checker())
    
    async def stop(self) -> None:
        """停止后台任务"""
        if not self._is_running:
            return
        
        self._is_running = False
        logger.info("BackgroundRuntime 停止")
        
        tasks = [
            self._world_task, 
            self._proactive_task, 
            self._consolidation_task,
            self._session_task,
            self._decay_task
        ]
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._world_task = None
        self._proactive_task = None
        self._consolidation_task = None
        self._session_task = None
        self._decay_task = None
    
    async def _world_ticker(self) -> None:
        """世界状态定时推进"""
        while self._is_running:
            try:
                await asyncio.sleep(self.world_tick_interval)
                
                if self.world_service:
                    async with self._world_lock:
                        await self.world_service.enqueue_world_action({
                            "type": "tick",
                            "minutes": 5
                        })
                        logger.debug("世界状态已推进")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"世界推进失败: {e}")
    
    async def _proactive_checker(self) -> None:
        """主动消息定时检查"""
        while self._is_running:
            try:
                await asyncio.sleep(self.proactive_check_interval)
                
                if self.proactive_service:
                    context = self._build_proactive_context()
                    
                    candidate = await self.proactive_service.check_and_generate_candidate(context)
                    
                    if candidate:
                        content = candidate.suggested_content
                        
                        if self.proactive_message_composer:
                            rewritten = await self.proactive_message_composer.compose(candidate, context)
                            if not rewritten:
                                continue
                            content = rewritten
                        
                        decision = candidate.to_decision(should_send=True)
                        
                        message = ProactiveMessage(
                            content=content,
                            trigger_type=candidate.trigger_type,
                            priority=int(candidate.priority),
                            timestamp=datetime.now().timestamp(),
                            decision=decision
                        )
                        
                        if self._on_proactive_message:
                            await self._on_proactive_message(message)
                            logger.info(f"主动消息触发: {candidate.trigger_type.value}")
                        
                        cooldown_seconds = getattr(candidate, 'cooldown_seconds', 300)
                        self.proactive_service.register_cooldown(
                            candidate.trigger_type.value,
                            cooldown_seconds
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"主动消息检查失败: {e}")
    
    async def _consolidation_checker(self) -> None:
        """记忆巩固定时检查"""
        while self._is_running:
            try:
                await asyncio.sleep(self.consolidation_check_interval)
                
                if self.memory_consolidation_service and self.memory_services:
                    working_entries = [
                        e.to_dict() for e in self.memory_services.get("working", []).get_all_entries() 
                        if hasattr(e, 'to_dict')
                    ] if hasattr(self.memory_services.get("working"), 'get_all_entries') else []
                    
                    episodic_entries = [
                        e.to_dict() for e in self.memory_services.get("episodic", []).get_recent_events(1000)
                        if hasattr(e, 'to_dict')
                    ] if hasattr(self.memory_services.get("episodic"), 'get_recent_events') else []
                    
                    core_entries = self.memory_services.get("core", {}).get_all() if hasattr(self.memory_services.get("core"), 'get_all') else []
                    
                    result = self.memory_consolidation_service.run_consolidation(
                        working_memory=working_entries,
                        episodic_memory=episodic_entries,
                        core_memory=core_entries
                    )
                    if result:
                        logger.debug(f"记忆巩固完成: {result}")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"记忆巩固检查失败: {e}")
    
    async def _session_checker(self) -> None:
        """
        会话清算定时检查
        
        V9 三层记忆系统：
        - 检测过期会话（5-10分钟无活动）
        - 执行清算（升级事件/长期记忆）
        - 删除短期记忆会话
        """
        while self._is_running:
            try:
                await asyncio.sleep(self.session_check_interval)
                
                if self.session_finalizer:
                    reports = self.session_finalizer.finalize_expired_sessions()
                    
                    if reports:
                        for report in reports:
                            logger.info(
                                f"会话清算完成: session={report.get('session_id')}, "
                                f"episodic_upgrades={len(report.get('episodic_upgrades', []))}, "
                                f"long_term_upgrades={len(report.get('long_term_upgrades', []))}"
                            )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"会话清算检查失败: {e}")
    
    async def _decay_checker(self) -> None:
        """
        记忆衰减定时检查
        
        V9 三层记忆系统：
        - 执行事件记忆衰减
        - 删除低价值事件
        - 压缩中等价值事件
        """
        while self._is_running:
            try:
                await asyncio.sleep(self.decay_check_interval)
                
                if self.memory_decay_engine:
                    report = await self.memory_decay_engine.run_decay_cycle()
                    
                    summary = report.get("summary", {})
                    if summary.get("deleted_count", 0) > 0 or summary.get("compressed_count", 0) > 0:
                        logger.info(
                            f"记忆衰减完成: 删除={summary.get('deleted_count', 0)}, "
                            f"压缩={summary.get('compressed_count', 0)}, "
                            f"保留={summary.get('retained_count', 0)}"
                        )
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"记忆衰减检查失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取运行状态"""
        return {
            "is_running": self._is_running,
            "world_task_active": self._world_task is not None and not self._world_task.done(),
            "proactive_task_active": self._proactive_task is not None and not self._proactive_task.done(),
            "consolidation_task_active": self._consolidation_task is not None and not self._consolidation_task.done(),
            "session_task_active": self._session_task is not None and not self._session_task.done(),
            "decay_task_active": self._decay_task is not None and not self._decay_task.done(),
            "world_tick_interval": self.world_tick_interval,
            "proactive_check_interval": self.proactive_check_interval,
            "consolidation_check_interval": self.consolidation_check_interval,
            "session_check_interval": self.session_check_interval,
            "decay_check_interval": self.decay_check_interval,
            "proactive_context": {
                "last_emotion": self._last_emotion,
                "last_support_need": self._last_support_need,
                "last_world_event": self._last_world_event,
                "pending_promises_count": len(self._pending_promises)
            }
        }
    
    async def pause_proactivity(self) -> None:
        """暂停主动回复任务"""
        if self._proactive_task and not self._proactive_task.done():
            self._proactive_task.cancel()
            try:
                await self._proactive_task
            except asyncio.CancelledError:
                pass
        self._proactive_task = None
        logger.info("主动回复任务已暂停")
    
    async def resume_proactivity(self) -> None:
        """恢复主动回复任务"""
        if self._is_running and self.proactive_service and self._proactive_task is None:
            self._proactive_task = asyncio.create_task(self._proactive_checker())
            logger.info("主动回复任务已恢复")
