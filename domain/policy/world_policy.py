"""
世界策略

V9 改版：世界更新校验和约束

改进：
1. 不再硬编码 VALID_LOCATIONS
2. 从 world_state 或 world_registry 读取合法位置
3. Policy 只做校验，不拥有世界知识本体
4. 提供 sanitize_world_output() 统一入口
5. 增强世界内容判断
6. 接入 world_runtime
"""

from typing import Dict, Any, Optional, Set, List
import logging

from application.contracts import WorldBrainOutput, WorldUpdateProposal, WorldContentProposal

logger = logging.getLogger(__name__)


class WorldPolicy:
    """
    世界策略
    
    V9 职责：
    1. 校验世界更新提案
    2. 约束时间推进
    3. 校验位置合法性（从 registry 读取）
    4. 清理世界内容提案
    5. 统一 sanitize_world_output() 入口
    6. 增强世界内容判断
    
    不负责：
    - 维护合法位置集合
    - 世界知识本体
    """
    
    MAX_TIME_ADVANCE = 480
    
    DEFAULT_LOCATIONS = {"宿舍", "食堂", "图书馆", "操场", "教室", "超市"}
    
    VALID_CONTENT_TYPES = {"bulletin", "rumor", "brief", "weather_feed", "news", "event"}
    
    def __init__(self, world_registry: Optional[Any] = None, world_runtime: Optional[Any] = None):
        self.world_registry = world_registry
        self.world_runtime = world_runtime
        self.stats = {
            "total_validations": 0,
            "clamped_time": 0,
            "invalid_locations": 0,
            "sanitized_outputs": 0,
            "content_proposals_cleaned": 0,
            "world_updates_suppressed": 0
        }
    
    def _get_valid_locations(self, world_state: Optional[Any] = None) -> Set[str]:
        """
        获取合法位置集合
        
        优先级：
        1. world_registry.get_valid_locations()
        2. world_state.valid_locations
        3. DEFAULT_LOCATIONS
        
        Args:
            world_state: 当前世界状态
            
        Returns:
            合法位置集合
        """
        if self.world_registry and hasattr(self.world_registry, "get_valid_locations"):
            return self.world_registry.get_valid_locations()
        
        if self.world_runtime and hasattr(self.world_runtime, "get_valid_locations"):
            return self.world_runtime.get_valid_locations()
        
        if world_state and hasattr(world_state, "valid_locations"):
            locations = world_state.valid_locations
            if isinstance(locations, (set, list, tuple)):
                return set(locations)
        
        return self.DEFAULT_LOCATIONS
    
    def sanitize_world_output(
        self,
        world_output: WorldBrainOutput,
        world_state: Optional[Any] = None
    ) -> WorldBrainOutput:
        """
        统一清理世界脑输出
        
        处理：
        1. time clamp
        2. location validate
        3. should_apply 与 proposal 一致性修正
        4. should_read 与 content proposal 一致性修正
        5. content types 校验
        
        Args:
            world_output: WorldBrainOutput
            world_state: 当前世界状态
            
        Returns:
            清理后的 WorldBrainOutput
        """
        if world_output is None:
            return self._create_empty_output()
        
        self.stats["total_validations"] += 1
        self.stats["sanitized_outputs"] += 1
        
        world_update = self.sanitize_world_update(
            world_output.world_update_proposal,
            world_state
        )
        
        world_content = self.sanitize_world_content_proposal(
            world_output.world_content_proposal
        )
        
        should_apply = self._determine_should_apply(world_update, world_output.should_apply_update)
        should_read = self._determine_should_read(world_content, world_output.should_read_world_content)
        
        return WorldBrainOutput(
            world_update_proposal=world_update,
            world_content_proposal=world_content,
            should_apply_update=should_apply,
            should_read_world_content=should_read
        )
    
    def _determine_should_apply(
        self,
        world_update: Optional[WorldUpdateProposal],
        original_should_apply: bool
    ) -> bool:
        """确定是否应该应用更新"""
        if world_update is None:
            return False
        
        if not world_update.world_commit_needed:
            return False
        
        if self.should_suppress_world_update(world_update):
            self.stats["world_updates_suppressed"] += 1
            return False
        
        return original_should_apply
    
    def _determine_should_read(
        self,
        world_content: Optional[WorldContentProposal],
        original_should_read: bool
    ) -> bool:
        """确定是否应该读取世界内容"""
        if world_content is None:
            return False
        
        if not world_content.user_is_asking_world_content:
            return False
        
        return original_should_read
    
    def _create_empty_output(self) -> WorldBrainOutput:
        """创建空输出"""
        return WorldBrainOutput(
            world_update_proposal=WorldUpdateProposal(
                time_advance_minutes=0,
                suggested_location=None,
                npc_context_hint="",
                world_commit_needed=False,
                reasoning="policy: empty output"
            ),
            world_content_proposal=None,
            should_apply_update=False,
            should_read_world_content=False
        )
    
    def sanitize_world_update(
        self,
        proposal: Any,
        world_state: Optional[Any] = None
    ) -> Any:
        """
        清理世界更新提案
        
        Args:
            proposal: WorldUpdateProposal
            world_state: 当前世界状态
            
        Returns:
            清理后的提案
        """
        if proposal is None:
            return proposal
        
        self.stats["total_validations"] += 1
        
        proposal.time_advance_minutes = self.clamp_time_advance(
            getattr(proposal, "time_advance_minutes", 0)
        )
        
        proposal.suggested_location = self.validate_location(
            getattr(proposal, "suggested_location", None),
            world_state
        )
        
        return proposal
    
    def sanitize_world_content_proposal(
        self,
        proposal: Any
    ) -> Optional[Any]:
        """
        清理世界内容提案
        
        V9 增强：
        - 校验 content_types
        - 清理空查询
        - 过滤无效类型
        
        Args:
            proposal: WorldContentProposal
            
        Returns:
            清理后的提案
        """
        if proposal is None:
            return None
        
        if not getattr(proposal, "user_is_asking_world_content", False):
            return None
        
        content_types = getattr(proposal, "content_types_needed", [])
        if not content_types:
            return None
        
        valid_types = self._validate_content_types(content_types)
        if not valid_types:
            self.stats["content_proposals_cleaned"] += 1
            return None
        
        proposal.content_types_needed = valid_types
        
        retrieval_query = getattr(proposal, "retrieval_query", "")
        if not retrieval_query or not retrieval_query.strip():
            proposal.retrieval_query = " ".join(valid_types)
        
        return proposal
    
    def _validate_content_types(self, content_types: List[str]) -> List[str]:
        """
        校验内容类型
        
        Args:
            content_types: 内容类型列表
            
        Returns:
            有效的内容类型列表
        """
        valid_types = []
        for ct in content_types:
            if ct in self.VALID_CONTENT_TYPES:
                valid_types.append(ct)
            else:
                logger.debug(f"无效的内容类型: {ct}")
        
        return valid_types
    
    def clamp_time_advance(self, minutes: int) -> int:
        """
        约束时间推进
        
        Args:
            minutes: 推进分钟数
            
        Returns:
            约束后的分钟数
        """
        if minutes < 0:
            self.stats["clamped_time"] += 1
            return 0
        
        if minutes > self.MAX_TIME_ADVANCE:
            self.stats["clamped_time"] += 1
            logger.warning(f"时间推进 {minutes} 分钟超过上限，已约束为 {self.MAX_TIME_ADVANCE}")
            return self.MAX_TIME_ADVANCE
        
        return minutes
    
    def validate_location(
        self,
        location: Optional[str],
        world_state: Optional[Any] = None
    ) -> Optional[str]:
        """
        校验位置合法性
        
        Args:
            location: 建议位置
            world_state: 当前世界状态
            
        Returns:
            合法的位置或 None
        """
        if location is None:
            return None
        
        valid_locations = self._get_valid_locations(world_state)
        
        if location not in valid_locations:
            self.stats["invalid_locations"] += 1
            logger.warning(f"位置 '{location}' 不在合法位置集合中，已忽略")
            return None
        
        return location
    
    def should_suppress_world_update(
        self,
        proposal: Any,
        context: Any = None
    ) -> bool:
        """
        判断是否应该抑制世界更新
        
        Args:
            proposal: WorldUpdateProposal
            context: 上下文
            
        Returns:
            是否抑制
        """
        if proposal is None:
            return True
        
        change_trigger = getattr(proposal, "change_trigger", "none")
        confidence = getattr(proposal, "confidence", 0.0)
        
        if change_trigger == "fallback" and confidence < 0.7:
            return True
        
        if change_trigger == "none":
            return True
        
        return False
    
    def should_allow_world_content(
        self,
        world_content_proposal: Optional[WorldContentProposal],
        context: Any = None
    ) -> bool:
        """
        V10: 判断是否应该允许世界内容读取
        
        Args:
            world_content_proposal: 世界内容提案
            context: 上下文
            
        Returns:
            是否允许
        """
        if world_content_proposal is None:
            return False
        
        if not world_content_proposal.user_is_asking_world_content:
            return False
        
        if not world_content_proposal.content_types_needed:
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
