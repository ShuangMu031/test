"""
响应模型

V6 核心组件：Agent 响应数据结构 - 接口层最终契约。

第二次整改：
- AgentResponse 从"拼装物"改成"冻结的接口契约"
- 只保留用户真正需要的字段
- 所有字段类型明确
- 所有可选字段明确
- 不再临时兼容旧字段

V7 改进：
- 添加 _turn_context 属性用于展示层
- 支持可观测层直接读取上下文

字段分类：

【用户可见字段】（必须）
- text: str - 最终回复文本
- delivery_required: bool - 是否需要投递
- response_message_id: str - 回复消息 ID

【状态摘要字段】（可选）
- world_state: Any - 世界状态摘要
- recent_messages_count: int - 最近消息数量
- relevant_memories_count: int - 相关记忆数量
- world_changes: List[Dict] - 世界变更列表

【调试字段】（可选，用于问题排查）
- emotion_insight: Dict - 情绪脑输出
- memory_decision: Dict - 记忆脑输出
- world_update_proposal: Dict - 世界更新提案
- npc_interaction_hint: Dict - NPC 提示
- behavior_plan_v2: Dict - 行为脑计划
- supervisor_decision: Dict - 总控脑决策
- execution_result: Dict - 执行结果
- debug: Dict - 调试信息（phase, model_tier, trace, warnings）

【内部字段】（不对外暴露）
- _turn_context: TurnContext - 用于展示层

已删除旧字段：
- decision: 被 behavior_plan_v2/supervisor_decision 替代
- action_plan: 被 behavior_plan_v2 替代
- emotional_state: 不应在 response 中暴露内部状态

原则：
- AgentResponse 不应该成为内部所有结构的镜像
- AgentResponse 不应该是主链临时数据的大杂烩
- AgentResponse 不应该是调试内容垃圾桶
- AgentResponse 应该只是"接口层最终契约"
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class AgentResponse:
    """
    Agent 响应 - 接口层最终契约
    
    第二次整改：冻结为接口契约
    
    V7 改进：添加 _turn_context 用于展示层
    
    用户可见字段：
        text: 最终回复文本（必须）
        delivery_required: 是否需要投递
        response_message_id: 回复消息 ID
    
    状态摘要字段：
        world_state: 世界状态摘要
        recent_messages_count: 最近消息数量
        relevant_memories_count: 相关记忆数量
        world_changes: 世界变更列表
    
    调试字段：
        emotion_insight: 情绪脑输出
        memory_decision: 记忆脑输出
        world_update_proposal: 世界更新提案
        npc_interaction_hint: NPC 提示
        behavior_plan_v2: 行为脑计划
        supervisor_decision: 总控脑决策
        execution_result: 执行结果
        debug: 调试信息
    
    内部字段：
        _turn_context: 用于展示层（不序列化）
    """
    
    text: str
    delivery_required: bool = True
    response_message_id: str = ""
    
    world_state: Any = None
    recent_messages_count: int = 0
    relevant_memories_count: int = 0
    world_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    emotion_insight: Optional[Dict[str, Any]] = None
    memory_decision: Optional[Dict[str, Any]] = None
    world_update_proposal: Optional[Dict[str, Any]] = None
    npc_interaction_hint: Optional[Dict[str, Any]] = None
    behavior_plan_v2: Optional[Dict[str, Any]] = None
    supervisor_decision: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    
    debug: Dict[str, Any] = field(default_factory=dict)
    
    _turn_context: Any = field(default=None, repr=False, compare=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        第二次整改：统一序列化协议
        """
        return {
            "text": self.text,
            "delivery_required": self.delivery_required,
            "response_message_id": self.response_message_id,
            "world_state": str(self.world_state) if self.world_state else None,
            "recent_messages_count": self.recent_messages_count,
            "relevant_memories_count": self.relevant_memories_count,
            "world_changes": self.world_changes,
            "emotion_insight": self.emotion_insight,
            "memory_decision": self.memory_decision,
            "world_update_proposal": self.world_update_proposal,
            "npc_interaction_hint": self.npc_interaction_hint,
            "behavior_plan_v2": self.behavior_plan_v2,
            "supervisor_decision": self.supervisor_decision,
            "execution_result": self.execution_result,
            "debug": self.debug
        }
