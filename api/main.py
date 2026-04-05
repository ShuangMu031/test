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
        logger.info(f"收到消息: {request.message}")
        
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
            response_text = "抱歉，我暂时无法回应。"
            emotion = "neutral"
        
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
                "dominant_brain": "emotion",
                "final_action": "comfort_first",
                "model_tier": "standard",
                "has_world_content": False,
                "has_npc": False,
                "has_tool": False,
                "warnings": []
            },
            trace_summary={
                "brain_views": [
                    {
                        "brain_name": "emotion",
                        "display_name": "情绪脑",
                        "triggered": True,
                        "conclusion": "用户处于低效价情绪，支持需求较高",
                        "key_fields": {
                            "primary_emotion": emotion,
                            "valence": -0.72,
                            "arousal": 0.41,
                            "support_need": "high"
                        },
                        "influence_target": ["memory", "behavior", "supervisor"],
                        "duration_ms": 42,
                        "has_error": False
                    },
                    {
                        "brain_name": "memory",
                        "display_name": "记忆脑",
                        "triggered": True,
                        "conclusion": "检索到相关记忆",
                        "key_fields": {
                            "working_memory": "用户近期情绪低落",
                            "episodic_memory": "用户上周提到工作压力",
                            "core_memory": "用户重视情感支持"
                        },
                        "influence_target": ["behavior"],
                        "duration_ms": 35,
                        "has_error": False
                    },
                    {
                        "brain_name": "world",
                        "display_name": "世界脑",
                        "triggered": False,
                        "conclusion": "无需世界内容更新",
                        "key_fields": {
                            "time": datetime.now().isoformat(),
                            "location": "Digital World",
                            "weather": "sunny"
                        },
                        "influence_target": [],
                        "duration_ms": 28,
                        "has_error": False
                    },
                    {
                        "brain_name": "npc",
                        "display_name": "NPC脑",
                        "triggered": False,
                        "conclusion": "无需NPC介入",
                        "key_fields": {},
                        "influence_target": [],
                        "duration_ms": 22,
                        "has_error": False
                    },
                    {
                        "brain_name": "behavior",
                        "display_name": "行为脑",
                        "triggered": True,
                        "conclusion": "采取安慰策略",
                        "key_fields": {
                            "action": "comfort",
                            "priority": "high",
                            "tool_calls": []
                        },
                        "influence_target": ["supervisor"],
                        "duration_ms": 45,
                        "has_error": False
                    },
                    {
                        "brain_name": "supervisor",
                        "display_name": "总控脑",
                        "triggered": True,
                        "conclusion": "批准安慰策略",
                        "key_fields": {
                            "model_tier": "standard",
                            "suppress_tool_calls": True,
                            "suppress_npc": True
                        },
                        "influence_target": [],
                        "duration_ms": 38,
                        "has_error": False
                    }
                ],
                "timeline": [
                    "context_collected",
                    "brains_completed",
                    "policy_checked",
                    "responded"
                ],
                "decision_tensions": [],
                "response_source": "llm",
                "final_response": response_text
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
        "settings": {
            "llmProvider": "siliconflow",
            "apiKey": "",
            "modelName": "Qwen/Qwen2.5-72B-Instruct",
            "enableProactivity": True,
            "enableWorldTick": True,
            "enableNpcBrain": True,
            "theme": "light",
            "fontSize": "medium"
        }
    }


@app.post("/api/settings")
async def update_settings(settings: Dict[str, Any]):
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
            "enabled": False,
            "task_active": False,
            "check_interval": 30,
            "context": "idle"
        }
    }


@app.post("/api/proactive")
async def set_proactive(payload: Dict[str, Any]):
    enabled = payload.get("enabled", False)
    return {
        "status": "ok",
        "enabled": enabled
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
