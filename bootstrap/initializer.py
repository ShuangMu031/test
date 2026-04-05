"""
V9 初始化器

V9 改版：bootstrap 层

职责：
- 初始化世界运行时
- 初始化三层记忆
- 初始化记忆固化服务
- 初始化六脑
- 初始化世界知识服务
- 初始化现实素材采集器
- 构建完整 Agent

V9 第五批新增：
- ToolRegistry
- NewsTool / WeatherTool
- RealitySourceCollector
- WorldKnowledgeService

V9 修复：
- 返回完整的 AgentCoordinator
- CLI 只需调用 coordinator.handle_user_input()
"""

from typing import Dict, Any, Optional
import logging

from domain.memory import CoreMemoryService, EpisodicMemoryService, WorkingMemoryService
from domain.memory import ConsolidationService
from domain.world_state import LocalWorldAdapter, WorldRuntimePort
from domain.world_knowledge import (
    WorldKnowledgeService,
    WorldKnowledgeRepository,
    RealityToWorldTranslator
)
from domain.emotion.service import EmotionService
from domain.proactivity.service import ProactiveInteractionService
from application.orchestration.proactive_message_composer import ProactiveMessageComposer
from infrastructure.reality_sources import RealitySourceCollector
from infrastructure.tools.news.tool import NewsTool
from infrastructure.tools.weather.tool import WeatherTool
from infrastructure.tools.registry import ToolRegistry
from infrastructure.llm.mock_llm import MockLLM
from infrastructure.llm.factory import LLMFactory
from application.orchestration.coordinator import AgentCoordinator

logger = logging.getLogger(__name__)


class V9Initializer:
    """
    V9 初始化器
    
    负责构建完整的 Agent 系统
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self._core_memory: Optional[CoreMemoryService] = None
        self._episodic_memory: Optional[EpisodicMemoryService] = None
        self._working_memory: Optional[WorkingMemoryService] = None
        self._consolidation_service: Optional[ConsolidationService] = None
        self._world_runtime: Optional[WorldRuntimePort] = None
        
        self._tool_registry: Optional[ToolRegistry] = None
        self._news_tool: Optional[NewsTool] = None
        self._weather_tool: Optional[WeatherTool] = None
        self._reality_collector: Optional[RealitySourceCollector] = None
        self._world_knowledge_service: Optional[WorldKnowledgeService] = None
        
        self._initialized = False
    
    async def initialize(self) -> Dict[str, Any]:
        """初始化所有组件"""
        if self._initialized:
            return self._get_components()
        
        logger.info("V9 初始化开始...")
        
        self._core_memory = CoreMemoryService()
        self._episodic_memory = EpisodicMemoryService()
        self._working_memory = WorkingMemoryService()
        
        self._consolidation_service = ConsolidationService()
        
        persona = self.config.get("persona", {})
        self._core_memory.initialize_persona(persona)
        
        self._world_runtime = LocalWorldAdapter()
        
        self._init_tools()
        
        self._init_reality_sources()
        
        self._init_world_knowledge()
        
        self._initialized = True
        logger.info("V9 初始化完成")
        
        return self._get_components()
    
    def _init_tools(self) -> None:
        """初始化工具"""
        self._tool_registry = ToolRegistry()
        
        self._news_tool = NewsTool(api_key=self.config.get("news_api_key"))
        self._weather_tool = WeatherTool(api_key=self.config.get("weather_api_key"))
        
        self._tool_registry.register(self._news_tool)
        self._tool_registry.register(self._weather_tool)
        
        logger.debug("工具初始化完成")
    
    def _init_reality_sources(self) -> None:
        """初始化现实素材采集器"""
        self._reality_collector = RealitySourceCollector(
            news_tool=self._news_tool,
            weather_tool=self._weather_tool,
            config=self.config.get("reality_collector", {})
        )
        
        logger.debug("现实素材采集器初始化完成")
    
    def _init_world_knowledge(self) -> None:
        """初始化世界知识服务"""
        translator = RealityToWorldTranslator(
            config=self.config.get("world_translator", {})
        )
        
        repository = WorldKnowledgeRepository(
            config=self.config.get("world_repository", {})
        )
        
        self._world_knowledge_service = WorldKnowledgeService(
            translator=translator,
            repository=repository,
            config=self.config.get("world_knowledge", {})
        )
        
        logger.debug("世界知识服务初始化完成")
    
    def _get_components(self) -> Dict[str, Any]:
        """获取所有组件"""
        memory_services = {
            "core": self._core_memory,
            "episodic": self._episodic_memory,
            "working": self._working_memory,
            "consolidation": self._consolidation_service,
        }
        
        return {
            "core_memory": self._core_memory,
            "episodic_memory": self._episodic_memory,
            "working_memory": self._working_memory,
            "consolidation_service": self._consolidation_service,
            "memory_services": memory_services,
            "world_runtime": self._world_runtime,
            "tool_registry": self._tool_registry,
            "news_tool": self._news_tool,
            "weather_tool": self._weather_tool,
            "reality_source_collector": self._reality_collector,
            "world_knowledge_service": self._world_knowledge_service,
        }
    
    async def shutdown(self) -> None:
        """关闭所有组件"""
        logger.info("V9 关闭中...")
        self._initialized = False
        logger.info("V9 已关闭")


async def create_v9_application(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    创建 V9 应用
    
    V9 修复：返回完整的 AgentCoordinator
    
    返回：
    - agent_coordinator: 完整的 Agent 协调器
    - initializer: 初始化器
    - 其他组件...
    """
    config = config or {}
    
    initializer = V9Initializer(config)
    components = await initializer.initialize()
    components["initializer"] = initializer
    
    llm = _create_llm(config)
    
    emotion_service = EmotionService()
    
    from application.memory.facade import MemoryFacade
    memory_facade = MemoryFacade(
        core_memory=components.get("core_memory"),
        episodic_memory=components.get("episodic_memory"),
        working_memory=components.get("working_memory")
    )
    
    proactive_service = ProactiveInteractionService(
        memory_service=memory_facade,
        npc_manager=None,
        world_runtime=components["world_runtime"]
    )
    
    import os
    if "enable_proactivity" in config:
        enable_proactivity = config["enable_proactivity"]
    else:
        enable_proactivity = os.environ.get("V10_ENABLE_PROACTIVITY", "false").lower() == "true"
    
    proactive_check_interval = float(config.get("proactive_check_interval", 300.0))
    
    proactive_message_composer = ProactiveMessageComposer(
        llm=llm,
        working_memory=components.get("working_memory")
    )
    
    tools = {}
    if components.get("news_tool"):
        tools["news"] = components["news_tool"]
    if components.get("weather_tool"):
        tools["weather"] = components["weather_tool"]
    
    coordinator = AgentCoordinator(
        llm=llm,
        emotion_service=emotion_service,
        memory_services=components["memory_services"],
        world_runtime=components["world_runtime"],
        proactive_service=proactive_service,
        enable_proactivity=enable_proactivity,
        proactive_check_interval=proactive_check_interval,
        proactive_message_composer=proactive_message_composer,
        character_context=config.get("persona", {}),
        tools=tools,
        npc_manager=None,
        world_content_service=components.get("world_knowledge_service"),
        reality_feed_service=components.get("reality_source_collector"),
        memory_consolidation_service=components["memory_services"].get("consolidation")
    )
    
    components["agent_coordinator"] = coordinator
    components["emotion_service"] = emotion_service
    components["proactive_service"] = proactive_service
    components["llm"] = llm
    
    logger.info("V9 应用创建完成，AgentCoordinator 已就绪")
    
    return components


def _create_llm(config: Optional[Dict[str, Any]] = None) -> Any:
    """
    创建 LLM 实例
    
    优先使用 LLMFactory，失败时回退到 MockLLM
    
    Args:
        config: 配置字典
        
    Returns:
        LLM 实例
    """
    config = config or {}
    llm_config = config.get("llm", {})
    
    use_mock = llm_config.get("use_mock", False)
    
    if use_mock:
        logger.info("使用 MockLLM (配置指定)")
        return MockLLM(model_name=llm_config.get("model_name", "v9-mock-llm"))
    
    try:
        factory = LLMFactory(config=llm_config)
        llm = factory.create_default_llm()
        provider = factory.get_provider_name()
        logger.info(f"使用 LLMFactory 创建 LLM: provider={provider}")
        return llm
    except Exception as e:
        logger.warning(f"LLMFactory 创建失败: {e}，回退到 MockLLM")
        return MockLLM(model_name="v9-fallback-mock")
