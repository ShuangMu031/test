# AI Emotion Framework V10 修改内容

## 版本概述

V10 主要修复主动回复（Proactive Interaction）的相关问题，遵循"最小侵入、先稳住再变聪明"的原则。

## 修改目标

改完后，主动回复链路变成：

**启动**
- 默认 `enable_proactivity = false`
- 后台不启动 proactive task

**手动开启**
- `/proactive_on` 或配置打开
- 后台开始定时检查

**检查时**
- 先判断 trigger
- 再判断 cooldown
- 再判断情绪触发是否达到最小空闲时长
- 通过后生成 candidate
- candidate 不直接发固定模板句，而是交给 LLM 重写成自然一句话
- 最后 enqueue 到 `outbound_queue`

---

## 第一优先级：把 `enable_proactivity` 真正接上

### 1. bootstrap/initializer.py
- 增加从配置读取 `enable_proactivity` 和 `proactive_check_interval`
- 传递给 `AgentCoordinator`

### 2. application/orchestration/coordinator.py
- 增加 `enable_proactivity` 和 `proactive_check_interval` 参数
- 所有主动回复相关调用加 guard
- 增加运行时开关方法：`pause_proactivity()`, `resume_proactivity()`, `get_proactivity_status()`

### 3. application/orchestration/background_runtime.py
- 增加 `pause_proactivity()` 和 `resume_proactivity()` 方法

### 4. apps/cli/main.py
- 增加命令：`/proactive_on`, `/proactive_off`, `/proactive_status`

---

## 第二优先级：修冷却机制

### 问题
1. key 前后不一致：判断时看 `idle`，注册时写 `proactive_idle`
2. 语义混乱：`cooldowns[key]` 有时是剩余秒数，有时是时间戳

### 解决方案
- `_cooldown_registry` 内部统一存 `expires_at`（过期时间戳）
- `build_context()` 时转成 `remaining_seconds`
- trigger 判断只用 `remaining_seconds > 0`

### 修改文件
1. domain/proactivity/models.py - `ProactiveCandidate` 增加 `cooldown_seconds` 字段
2. domain/proactivity/service.py - 统一冷却机制语义

---

## 第三优先级：给情绪触发加"最小空闲时长"

### 修改前
```python
if self.trigger_type == TriggerType.EMOTION:
    return context.last_support_need in ["high", "medium"]
```

### 修改后
```python
if self.trigger_type == TriggerType.EMOTION:
    if context.last_support_need == "high":
        return context.idle_seconds >= 600  # 10分钟
    if context.last_support_need == "medium":
        return context.idle_seconds >= 1200  # 20分钟
    return False
```

### 修改文件
- domain/proactivity/models.py - `TriggerCondition.should_trigger()`

---

## 第四优先级：把固定模板句改成"候选触发 + LLM 重写"

### 新增文件
- application/orchestration/proactive_message_composer.py

### 职责
把 candidate 重写成一条自然、简短、贴上下文的主动消息

### 修改文件
- application/orchestration/background_runtime.py - 集成 LLM 重写
- bootstrap/initializer.py - 实例化 `ProactiveMessageComposer`

---

## 默认参数配置

```python
enable_proactivity = False
proactive_check_interval = 300  # 5分钟

# 触发条件冷却时间
IDLE cooldown = 3600           # 1小时
EMOTION cooldown = 1800        # 30分钟
WORLD_EVENT cooldown = 7200    # 2小时
PROMISE_FOLLOWUP cooldown = 3600   # 1小时
RELATIONSHIP_PUSH cooldown = 14400 # 4小时

# 触发门槛
IDLE: 1800 秒 (30分钟)
EMOTION high: 600 秒 (10分钟)
EMOTION medium: 1200 秒 (20分钟)
```

---

## 改进效果

### 改前
- 定时器味很重
- 该停不停
- 模板句机械
- 情绪打扰感强

### 改后
- 默认安静
- 只有手动开才运行
- 一次触发后能真正冷却
- 情绪触发不会太急
- 文案更像真人，不像系统通知

---

## V10 第二轮修复（Bug 修复）

### Bug 1: 环境变量兜底失效
**问题**：`config.get("enable_proactivity", False)` 会直接返回 False，永远不会进入 None 分支检查环境变量。

**修复**：
```python
# 修改前
enable_proactivity = config.get("enable_proactivity", False)
if enable_proactivity is None:
    enable_proactivity = os.environ.get("V9_ENABLE_PROACTIVITY", "false").lower() == "true"

# 修改后
if "enable_proactivity" in config:
    enable_proactivity = config["enable_proactivity"]
else:
    enable_proactivity = os.environ.get("V9_ENABLE_PROACTIVITY", "false").lower() == "true"
```

**文件**：`bootstrap/initializer.py`

---

### Bug 2: 关闭时不更新 last_interaction/context
**问题**：只有 `enable_proactivity=True` 时才更新互动时间和上下文，导致恢复后误触发。

**修复**：移除 guard，始终更新 `last_interaction` 和 `proactive_context`。

**文件**：`application/orchestration/coordinator.py`
- `_on_message_received()`
- `handle_user_input()`
- `_update_proactive_context()`

---

### Bug 3: working_memory.add_entry 参数错位
**问题**：`add_entry("assistant", content)` 把 `"assistant"` 当成 `memory_type` 而不是 `role`。

**修复**：
```python
# 修改前
self.working_memory.add_entry("assistant", content)

# 修改后
self.working_memory.add_dialogue("assistant", content)
```

**文件**：`application/orchestration/coordinator.py`

---

### Bug 4: MockLLM 下主动消息被全部吞掉
**问题**：`MockLLM.structured()` 对 boolean 字段一律返回 `False`，导致 `should_send=False`。

**修复**：对 `should_send` 字段特殊处理，返回 `True`。

**文件**：`infrastructure/llm/mock_llm.py`

---

### Bug 5: pending_promises 仍然是空回灌
**问题**：`_update_proactive_context()` 始终传入 `pending_promises=[]`，导致承诺跟进触发无效。

**修复**：
1. 在 `WorkingMemoryService` 中添加 `_pending_promises` 列表和相关方法
2. 在 `coordinator.py` 中从 `working_memory` 获取实际的 `pending_promises`

**文件**：
- `domain/memory/working/service.py` - 添加 pending_promises 存储
- `application/orchestration/coordinator.py` - 获取并传入实际的 pending_promises

---

### Bug 6: CLI 没有把主动消息真正显示出来
**问题**：主动消息只 enqueue 到 outbound_queue，CLI 没有轮询并展示。

**修复**：添加 `_check_proactive_messages()` 方法，在主循环中检查并展示主动消息。

**文件**：`apps/cli/main.py`

---

## V10 第三轮修复

### Bug 1: pending_promises 链没打通
**问题**：`turn_orchestrator.py` 写 promise 到 `session`，但主动回复读取的是 `working_memory`，两边不是同一条存储链。

**修复**：在写入 `session.add_pending_promise()` 的同时，也写入 `working_memory.add_pending_promise()`。

**文件**：`application/orchestration/turn_orchestrator.py`

---

### Bug 2: CLI 主动消息不是真异步
**问题**：用户停在 `input()` 时，CLI 不会再次调用 `_check_proactive_messages()`，主动消息要等下一次输入才会显示。

**修复**：
1. 添加 `_proactive_message_loop()` 后台任务，每 2 秒检查一次主动消息
2. 使用 `_input_lock` 防止输出混乱
3. 在 `start()` 中启动后台任务，在 `stop()` 中取消

**文件**：`apps/cli/main.py`

---

### 体验优化: 环境变量名更新
**问题**：环境变量名还在用 `V9_ENABLE_PROACTIVITY`，容易误解版本状态。

**修复**：改为 `V10_ENABLE_PROACTIVITY`。

**文件**：
- `bootstrap/initializer.py`
- `config/feature_flags.py`

---

## 文档补充

### 新增 requirements.txt
**内容**：项目依赖清单，包含：
- 核心依赖：`httpx>=0.24.0`、`openai>=1.0.0`
- 可选依赖：`numpy`（深度学习情绪检测）
- 开发依赖：`pytest`、`ruff`、`mypy`
- 环境变量说明

---

## V10 第四轮修复

### Bug 1: RELATIONSHIP_PUSH 是死分支
**问题**：`TriggerType.RELATIONSHIP_PUSH` 在 `should_trigger()` 里没有分支，永远不会被触发。

**修复**：在 `TriggerCondition.should_trigger()` 中添加 RELATIONSHIP_PUSH 分支：
```python
if self.trigger_type == TriggerType.RELATIONSHIP_PUSH:
    return len(context.recent_npc_interactions) > 0
```

**文件**：`domain/proactivity/models.py`

---

### Bug 2: recent_npc_interactions 没有数据来源
**问题**：`ProactiveContext.recent_npc_interactions` 字段定义了，但没有人喂数据。

**修复**：
1. `BackgroundRuntime` 添加 `_recent_npc_interactions` 状态字段
2. `update_proactive_context()` 添加 `recent_npc_interactions` 参数
3. `_build_proactive_context()` 传入 `recent_npc_interactions`
4. `ProactiveService.build_context()` 添加 `recent_npc_interactions` 参数
5. `coordinator._update_proactive_context()` 从 `TurnContext.npc_interaction_hint` 提取 NPC 数据

**文件**：
- `application/orchestration/background_runtime.py`
- `domain/proactivity/service.py`
- `application/orchestration/coordinator.py`

---

## V10 工程卫生清理

### 清理缓存文件
**操作**：删除所有 `__pycache__` 目录和 `.pyc` 文件

**命令**：
```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

---

### 新增文档

#### README.md
**内容**：
- 项目特性介绍
- 快速开始指南
- CLI 命令说明
- 功能开关列表
- 项目结构概览
- 主动交互触发类型说明

#### docs/RUNNING.md
**内容**：
- 环境准备详细步骤
- LLM 配置三种方式（OpenAI/SiliconFlow/Ollama）
- CLI 命令详解
- 功能开关说明
- 常见问题解答
- 开发调试指南
- 架构概览图
- 后台任务说明
