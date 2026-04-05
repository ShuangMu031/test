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
    response: str
    emotion: str
    timestamp: str
    trace: Optional[Dict[str, Any]] = None


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
                trace = result.to_dict() if hasattr(result, 'to_dict') else None
            elif isinstance(result, dict):
                response_text = result.get("text", result.get("response", "抱歉，我暂时无法回应。"))
                emotion = result.get("emotion", "neutral")
                trace = result
            else:
                response_text = str(result)
                emotion = "neutral"
                trace = None
        else:
            response_text = "抱歉，我暂时无法回应。"
            emotion = "neutral"
            trace = None
        
        return ChatResponse(
            response=response_text,
            emotion=emotion,
            timestamp=datetime.now().isoformat(),
            trace=trace
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
        "theme": "light",
        "fontSize": 14,
        "proactiveMessage": True,
        "llmProvider": "siliconflow",
        "modelName": "Qwen/Qwen2.5-72B-Instruct"
    }


@app.post("/api/settings")
async def update_settings(settings: Dict[str, Any]):
    return {"success": True, "message": "设置已更新"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
