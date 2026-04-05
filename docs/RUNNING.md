# 运行指南

## 环境准备

### 1. Python 版本

确保 Python 版本 >= 3.10：

```bash
python --version
```

### 2. 创建虚拟环境

```bash
cd AI_Emotion_Framework_v10

# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

最小安装（仅生产环境）：

```bash
pip install httpx openai
```

---

## LLM 配置

### 方式一：OpenAI

```bash
# Windows
set OPENAI_API_KEY=sk-xxxxx

# Linux/Mac
export OPENAI_API_KEY=sk-xxxxx
```

### 方式二：SiliconFlow（推荐国内用户）

```bash
# Windows
set SILICONFLOW_API_KEY=xxxxx

# Linux/Mac
export SILICONFLOW_API_KEY=xxxxx
```

可选配置：

```bash
set SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
set SF_MODEL_STANDARD=Qwen/Qwen2.5-72B-Instruct
```

### 方式三：Ollama（本地）

1. 安装 Ollama：https://ollama.ai
2. 运行服务：

```bash
ollama serve
ollama pull llama3
```

---

## 启动应用

### CLI 模式

```bash
python -m apps.cli.main
```

### 使用 Mock LLM 测试

```bash
# Windows
set V9_ENABLE_MOCK_LLM=true
python -m apps.cli.main

# Linux/Mac
export V9_ENABLE_MOCK_LLM=true
python -m apps.cli.main
```

---

## CLI 命令详解

### 基础命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/quit` | 退出程序 |

### 调试命令

| 命令 | 说明 |
|------|------|
| `/trace` | 显示本轮六脑协作详细过程 |
| `/trace_summary` | 显示本轮摘要 |

### 主动消息控制

| 命令 | 说明 |
|------|------|
| `/proactive_on` | 开启主动消息 |
| `/proactive_off` | 关闭主动消息 |
| `/proactive_status` | 查看主动消息状态 |

---

## 功能开关

通过环境变量控制：

```bash
# 主动消息（默认关闭）
set V10_ENABLE_PROACTIVITY=true

# 世界状态更新（默认开启）
set V9_ENABLE_WORLD_TICK=true

# Mock LLM（默认关闭）
set V9_ENABLE_MOCK_LLM=false

# NPC 脑（默认关闭）
set V9_ENABLE_NPC_BRAIN=false

# 情绪检测（默认关闭）
set V9_ENABLE_EMOTION_DETECTION=false
```

---

## 常见问题

### Q: 启动时报 "未检测到可用的 LLM"

**A:** 需要配置至少一个 LLM Provider：
- 设置 `OPENAI_API_KEY`
- 或设置 `SILICONFLOW_API_KEY`
- 或运行 Ollama 服务

### Q: 主动消息没有触发

**A:** 检查以下配置：
1. 确认已开启：`/proactive_on` 或设置 `V10_ENABLE_PROACTIVITY=true`
2. 确认空闲时间足够（默认需要 30 分钟）
3. 检查是否在冷却期内

### Q: 如何使用自定义模型

**A:** 通过环境变量指定：

```bash
# OpenAI
set OPENAI_MODEL=gpt-4

# SiliconFlow
set SF_MODEL_STANDARD=Qwen/Qwen2.5-72B-Instruct
set SF_MODEL_CHEAP=Qwen/Qwen2.5-7B-Instruct
set SF_MODEL_TOP=deepseek-ai/DeepSeek-V3
```

### Q: 如何查看详细日志

**A:** 修改日志级别：

```python
# 在 apps/cli/main.py 中修改
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

---

## 开发调试

### 运行语法检查

```bash
python -m compileall .
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
ruff check .
ruff format .
```

### 类型检查

```bash
mypy .
```

---

## 架构概览

```
用户输入
    ↓
AgentCoordinator（协调器）
    ↓
TurnOrchestrator（轮次编排）
    ↓
┌─────────────────────────────┐
│         六脑并行执行          │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │情绪脑│ │记忆脑│ │世界脑│   │
│  └─────┘ └─────┘ └─────┘   │
│  ┌─────┐ ┌─────┐ ┌─────┐   │
│  │行为脑│ │NPC脑│ │总控脑│   │
│  └─────┘ └─────┘ └─────┘   │
└─────────────────────────────┘
    ↓
PlanCompiler（计划编译）
    ↓
ActionExecutor（动作执行）
    ↓
ReplyComposer（回复生成）
    ↓
输出给用户
```

---

## 后台任务

框架运行多个后台任务：

| 任务 | 默认间隔 | 说明 |
|------|---------|------|
| World Ticker | 60s | 世界状态更新 |
| Proactive Checker | 300s | 主动消息检查 |
| Memory Consolidation | 600s | 记忆整合 |
| Session Checker | 300s | 会话清理 |
| Memory Decay | 3600s | 记忆衰减 |
