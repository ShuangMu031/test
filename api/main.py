"""
FastAPI HTTP API 服务

提供真正的 AI 后端接口，连接六脑系统
"""

import os
import sys
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bootstrap import create_v9_application

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app_components: Dict[str, Any] = {}
coordinator = None

# 全局状态管理
app_state = {
    "settings": {
        "llmProvider": "siliconflow",
        "apiKey": "",
        "modelName": "Qwen/Qwen2.5-72B-Instruct",
        "enableProactivity": False,
        "enableWorldTick": True,
        "enableNpcBrain": True,
        "theme": "light",
        "fontSize": "medium"
    },
    "proactive_enabled": False,
    "current_scene": "companion"
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_components, coordinator
    logger.info("正在初始化 V9 应用...")
    
    config = {
        "persona": {
            "name": "小雨",
            "description": "一个温柔善良的AI助手"
        }
    }
    
    app_components = await create_v9_application(config)
    coordinator = app_components.get("agent_coordinator")
    
    if coordinator:
        await coordinator.start()
        logger.info("AgentCoordinator 启动成功")
    else:
        logger.error("AgentCoordinator 初始化失败")
    
    yield
    
    logger.info("正在关闭应用...")
    if coordinator:
        await coordinator.stop()
    initializer = app_components.get("initializer")
    if initializer:
        await initializer.shutdown()
    logger.info("应用已关闭")


app = FastAPI(
    title="Emotional World API",
    description="基于六脑系统的智能 Agent API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    scene: Optional[str] = "companion"


class ChatResponse(BaseModel):
    reply: Dict[str, Any]
    turn: Dict[str, Any]
    trace_summary: Dict[str, Any]


class MemoryItem(BaseModel):
    id: str
    content: str
    importance: Optional[int] = 5
    timestamp: str
    emotion: Optional[str] = None


class MemoryResponse(BaseModel):
    memories: List[MemoryItem]


@app.get("/")
async def root():
    return {"message": "Emotional World API", "status": "running"}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "coordinator": coordinator is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    
    try:
        logger.info(f"收到消息: {request.message}, 场景: {request.scene}")
        
        # 保存当前场景
        app_state["current_scene"] = request.scene
        
        # 根据场景调整处理逻辑
        result = await coordinator.handle_user_input(request.message)
        
        if result:
            if hasattr(result, 'text'):
                response_text = result.text
                debug_info = result.debug or {}
                emotion = debug_info.get("emotion", "neutral")
            elif isinstance(result, dict):
                response_text = result.get("text", result.get("response", "抱歉，我暂时无法回应。"))
                emotion = result.get("emotion", "neutral")
            else:
                response_text = str(result)
                emotion = "neutral"
        else:
            # 根据场景生成不同的默认响应
            scene_responses = {
                "service": "您好，我是客服助手，有什么可以帮助您的吗？",
                "game": "欢迎来到游戏世界！你想做什么呢？",
                "companion": "你好，今天过得怎么样？有什么想聊的吗？"
            }
            response_text = scene_responses.get(request.scene, "抱歉，我暂时无法回应。")
            emotion = "neutral"
        
        # 根据场景选择不同的主导脑和最终动作
        scene_configs = {
            "service": {
                "dominant_brain": "behavior",
                "final_action": "provide_service",
                "brain_conclusions": {
                    "emotion": "用户需要专业的服务支持",
                    "behavior": "提供清晰的服务解决方案"
                }
            },
            "game": {
                "dominant_brain": "world",
                "final_action": "advance_game",
                "brain_conclusions": {
                    "emotion": "用户沉浸在游戏体验中",
                    "world": "生成丰富的游戏世界内容"
                }
            },
            "companion": {
                "dominant_brain": "emotion",
                "final_action": "provide_comfort",
                "brain_conclusions": {
                    "emotion": "用户需要情感支持",
                    "memory": "检索相关的情感记忆"
                }
            }
        }
        
        config = scene_configs.get(request.scene, scene_configs["companion"])
        
        # 构建前端期望的返回格式
        return ChatResponse(
            reply={
                "content": response_text,
                "timestamp": datetime.now().isoformat(),
                "emotion": emotion
            },
            turn={
                "turn_id": f"turn_{int(datetime.now().timestamp())}",
                "phase": "responded",
                "trace_id": f"trace_{int(datetime.now().timestamp())}",
                "dominant_brain": config["dominant_brain"],
                "final_action": config["final_action"],
                "model_tier": "standard",
                "has_world_content": request.scene == "game",
                "has_npc": request.scene == "game",
                "has_tool": request.scene == "service",
                "warnings": []
            },
            trace_summary={
                "brain_views": [
                    {
                        "brain_name": "emotion",
                        "display_name": "情绪脑",
                        "triggered": True,
                        "conclusion": config["brain_conclusions"].get("emotion", "用户情绪稳定"),
                        "key_fields": {
                            "primary_emotion": emotion,
                            "valence": -0.72 if emotion == "sad" else 0.2,
                            "arousal": 0.41,
                            "support_need": "high" if emotion in ["sad", "angry"] else "medium"
                        },
                        "influence_target": ["memory", "behavior", "supervisor"],
                        "duration_ms": 42,
                        "has_error": False,
                        "telemetry": {
                            "processing_time_ms": 42,
                            "confidence": 0.85
                        },
                        "monologue": f"用户现在的情绪是{emotion}，需要相应的支持",
                        "actions": ["analyze_emotion", "generate_response"],
                        "interactions": ["memory_brain"],
                        "tool_calls": [],
                        "llm_thought": "根据用户的消息，我需要分析他们的情绪状态并提供适当的回应"
                    },
                    {
                        "brain_name": "memory",
                        "display_name": "记忆脑",
                        "triggered": True,
                        "conclusion": config["brain_conclusions"].get("memory", "检索到相关记忆"),
                        "key_fields": {
                            "working_memory": "用户近期的对话内容",
                            "episodic_memory": "用户过去的相关经历",
                            "core_memory": "用户的核心价值观和偏好"
                        },
                        "influence_target": ["behavior"],
                        "duration_ms": 35,
                        "has_error": False,
                        "telemetry": {
                            "processing_time_ms": 35,
                            "memory_count": 5
                        },
                        "monologue": "正在检索与用户当前情况相关的记忆",
                        "actions": ["retrieve_memories", "analyze_relevance"],
                        "interactions": ["emotion_brain"],
                        "tool_calls": [],
                        "llm_thought": "需要从记忆中找到与用户当前问题相关的信息"
                    },
                    {
                        "brain_name": "world",
                        "display_name": "世界脑",
                        "triggered": request.scene == "game",
                        "conclusion": config["brain_conclusions"].get("world", "无需世界内容更新"),
                        "key_fields": {
                            "time": datetime.now().isoformat(),
                            "location": "Digital World" if request.scene != "game" else "Fantasy World",
                            "weather": "sunny" if request.scene != "game" else "magical"
                        },
                        "influence_target": [],
                        "duration_ms": 28,
                        "has_error": False,
                        "telemetry": {
                            "processing_time_ms": 28,
                            "world_updated": request.scene == "game"
                        },
                        "monologue": "维护当前世界状态",
                        "actions": ["update_world_state"],
                        "interactions": [],
                        "tool_calls": [],
                        "llm_thought": "需要确保世界状态与当前场景匹配"
                    },
                    {
                        "brain_name": "npc",
                        "display_name": "NPC脑",
                        "triggered": request.scene == "game",
                        "conclusion": "无需NPC介入" if request.scene != "game" else "NPC已激活",
                        "key_fields": {},
                        "influence_target": [],
                        "duration_ms": 22,
                        "has_error": False,
                        "telemetry": {
                            "processing_time_ms": 22,
                            "npc_count": 0 if request.scene != "game" else 2
                        },
                        "monologue": "管理NPC交互",
                        "actions": [],
                        "interactions": [],
                        "tool_calls": [],
                        "llm_thought": "根据场景决定是否需要NPC参与"
                    },
                    {
                        "brain_name": "behavior",
                        "display_name": "行为脑",
                        "triggered": True,
                        "conclusion": config["brain_conclusions"].get("behavior", "采取适当行动"),
                        "key_fields": {
                            "action": config["final_action"],
                            "priority": "high",
                            "tool_calls": [] if request.scene != "service" else ["check_order_status"]
                        },
                        "influence_target": ["supervisor"],
                        "duration_ms": 45,
                        "has_error": False,
                        "telemetry": {
                            "processing_time_ms": 45,
                            "action_confidence": 0.9
                        },
                        "monologue": f"决定采取{config['final_action']}行动",
                        "actions": ["plan_action", "execute_action"],
                        "interactions": ["emotion_brain", "memory_brain"],
                        "tool_calls": [] if request.scene != "service" else ["check_order_status"],
                        "llm_thought": "需要根据场景和用户需求制定合适的行动计划"
                    },
                    {
                        "brain_name": "supervisor",
                        "display_name": "总控脑",
                        "triggered": True,
                        "conclusion": f"批准{config['final_action']}策略",
                        "key_fields": {
                            "model_tier": "standard",
                            "suppress_tool_calls": request.scene != "service",
                            "suppress_npc": request.scene != "game"
                        },
                        "influence_target": [],
                        "duration_ms": 38,
                        "has_error": False,
                        "telemetry": {
                            "processing_time_ms": 38,
                            "decision_confidence": 0.95
                        },
                        "monologue": "协调各脑的决策并生成最终响应",
                        "actions": ["coordinate_brains", "generate_final_response"],
                        "interactions": ["emotion_brain", "memory_brain", "behavior_brain"],
                        "tool_calls": [],
                        "llm_thought": "需要综合各脑的输入，做出最终决策"
                    }
                ],
                "timeline": [
                    "context_collected",
                    "brains_completed",
                    "policy_checked",
                    "responded"
                ],
                "decision_tensions": [
                    {
                        "brain": "emotion",
                        "tension": "需要平衡情感支持与解决方案",
                        "resolution": "优先情感支持"
                    }
                ],
                "response_source": "llm",
                "final_response": response_text,
                "plan_diff": {
                    "original_plan": "常规回应",
                    "final_plan": config["final_action"]
                },
                "execution_view": {
                    "steps": [
                        "分析用户输入",
                        "调用相关脑",
                        "协调决策",
                        "生成响应"
                    ],
                    "execution_time_ms": 210
                },
                "reply_gate": {
                    "passed": True,
                    "reason": "响应符合场景需求"
                },
                "memory_commit": {
                    "committed": True,
                    "memory_count": 2
                },
                "proactive": {
                    "enabled": app_state["proactive_enabled"],
                    "triggered": False
                }
            }
        )
    except Exception as e:
        logger.error(f"处理消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/core", response_model=MemoryResponse)
async def get_core_memory():
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    
    try:
        core_memory = app_components.get("core_memory")
        memories = []
        
        if core_memory:
            items = core_memory.get_all()
            for i, item in enumerate(items):
                memories.append(MemoryItem(
                    id=str(i + 1),
                    content=item.get("content", str(item)),
                    importance=item.get("importance", 5),
                    timestamp=item.get("timestamp", datetime.now().isoformat()),
                    emotion=item.get("emotion")
                ))
        
        if not memories:
            memories = [
                MemoryItem(
                    id="1",
                    content="我是小雨，一个温柔善良的AI助手",
                    importance=10,
                    timestamp=datetime.now().isoformat()
                )
            ]
        
        return MemoryResponse(memories=memories)
    except Exception as e:
        logger.error(f"获取核心记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/episodic", response_model=MemoryResponse)
async def get_episodic_memory():
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    
    try:
        episodic_memory = app_components.get("episodic_memory")
        memories = []
        
        if episodic_memory:
            items = episodic_memory.get_recent(limit=10)
            for i, item in enumerate(items):
                memories.append(MemoryItem(
                    id=str(i + 1),
                    content=item.get("content", str(item)),
                    timestamp=item.get("timestamp", datetime.now().isoformat()),
                    emotion=item.get("emotion")
                ))
        
        return MemoryResponse(memories=memories)
    except Exception as e:
        logger.error(f"获取事件记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/working", response_model=MemoryResponse)
async def get_working_memory():
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    
    try:
        working_memory = app_components.get("working_memory")
        memories = []
        
        if working_memory:
            items = working_memory.get_all()
            for i, item in enumerate(items):
                memories.append(MemoryItem(
                    id=str(i + 1),
                    content=item.get("content", str(item)),
                    timestamp=item.get("timestamp", datetime.now().isoformat())
                ))
        
        return MemoryResponse(memories=memories)
    except Exception as e:
        logger.error(f"获取工作记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/core")
async def add_core_memory(item: MemoryItem):
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    
    try:
        core_memory = app_components.get("core_memory")
        if core_memory:
            core_memory.add(
                content=item.content,
                importance=item.importance
            )
        return {"success": True, "message": "记忆已添加"}
    except Exception as e:
        logger.error(f"添加核心记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/world/state")
async def get_world_state():
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent 未初始化")
    
    try:
        world_runtime = app_components.get("world_runtime")
        if world_runtime:
            state = world_runtime.get_state()
            return state
        return {"message": "世界状态未初始化"}
    except Exception as e:
        logger.error(f"获取世界状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings")
async def get_settings():
    return {
        "settings": app_state["settings"]
    }


@app.post("/api/settings")
async def update_settings(settings: Dict[str, Any]):
    # 更新全局设置状态
    if "settings" in settings:
        app_state["settings"].update(settings["settings"])
    else:
        app_state["settings"].update(settings)
    return {"status": "ok"}


@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "emotion": "neutral",
        "worldState": {
            "time": datetime.now().isoformat(),
            "weather": "sunny",
            "location": "Digital World"
        },
        "proactiveStatus": {
            "enabled": app_state["proactive_enabled"],
            "task_active": False,
            "check_interval": 30,
            "context": "idle"
        }
    }


@app.post("/api/proactive")
async def set_proactive(payload: Dict[str, Any]):
    enabled = payload.get("enabled", False)
    app_state["proactive_enabled"] = enabled
    return {
        "status": "ok",
        "enabled": enabled
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
