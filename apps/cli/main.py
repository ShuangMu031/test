"""
CLI 主入口

V9 改版：apps/cli/

这个版本新增：
- /trace         显示本轮六脑协作过程
- /trace_summary 显示本轮摘要
- 记录 last_response，读取 AgentResponse._turn_context 做可视化展示
"""

import asyncio
import logging
import os
import sys
from typing import Any, Optional

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from bootstrap import create_v9_application
from application.observability import TraceBuilder, CLIExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CLIInterface:
    """
    CLI 交互界面

    V9：
    - 只调用 AgentCoordinator.handle_user_input()
    - 不在 CLI 层自行拼逻辑
    - 增加 trace 展示

    V10：
    - 后台任务检查主动消息，实现真正的异步展示
    """

    def __init__(self, components: dict):
        self.components = components
        self.coordinator = components["agent_coordinator"]
        self.initializer = components["initializer"]
        self.running = False

        self.last_response: Optional[Any] = None

        self.trace_builder = TraceBuilder()
        self.cli_exporter = CLIExporter(use_color=True, verbose=True)
        
        self._proactive_task: Optional[asyncio.Task] = None
        self._input_lock = asyncio.Lock()

    async def start(self) -> None:
        """启动 CLI"""
        self.running = True

        await self.coordinator.start()
        
        self._proactive_task = asyncio.create_task(self._proactive_message_loop())

        print("\n" + "=" * 50)
        print("AI Emotion Framework V10")
        print("=" * 50)
        print("输入消息与 Agent 对话")
        print("输入 /help 查看帮助")
        print("输入 /quit 退出")
        print("=" * 50 + "\n")

        await self._main_loop()

    async def stop(self) -> None:
        """停止 CLI"""
        self.running = False
        
        if self._proactive_task:
            self._proactive_task.cancel()
            try:
                await self._proactive_task
            except asyncio.CancelledError:
                pass
        
        await self.coordinator.stop()
        await self.initializer.shutdown()
        print("\n再见！")

    async def _main_loop(self) -> None:
        """主循环"""
        while self.running:
            try:
                user_input = await self._get_input()

                if not user_input.strip():
                    continue

                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                await self._handle_message(user_input)

            except KeyboardInterrupt:
                await self.stop()
                break
            except EOFError:
                await self.stop()
                break
    
    async def _proactive_message_loop(self) -> None:
        """后台任务：定期检查并展示主动消息"""
        while self.running:
            try:
                await asyncio.sleep(2)
                if self.running:
                    await self._check_proactive_messages()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("检查主动消息失败")
    
    async def _check_proactive_messages(self) -> None:
        """检查并展示主动消息"""
        async with self._input_lock:
            pending = self.coordinator.get_pending_messages(limit=5)
            for msg in pending:
                if msg.get("message_type") == "proactive":
                    print(f"\n[主动消息] 小雨: {msg.get('content', '')}\n")
                    await self.coordinator.mark_message_delivered(msg.get("id"))

    async def _get_input(self) -> str:
        """获取用户输入"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: input("你: "))

    async def _handle_message(self, user_input: str) -> None:
        """
        处理用户消息
        """
        try:
            response = await self.coordinator.handle_user_input(user_input)

            # 保存最后一轮响应，供 /trace /trace_summary 使用
            self.last_response = response

            print(f"\n小雨: {response.text}\n")

            if response.debug:
                phase = response.debug.get("phase", "unknown")
                warnings = response.debug.get("warnings", [])
                if warnings:
                    print(f"[调试] 阶段: {phase}, 警告: {warnings}")

        except Exception as e:
            logger.exception("处理消息失败")
            print(f"\n[错误] 处理消息失败: {e}\n")

    async def _handle_command(self, command: str) -> None:
        """处理命令"""
        cmd = command.lower().strip()

        if cmd in ["/quit", "/exit", "/q"]:
            await self.stop()
        elif cmd == "/help":
            self._print_help()
        elif cmd == "/status":
            self._print_status()
        elif cmd == "/memory":
            self._print_memory()
        elif cmd == "/world":
            await self._print_world()
        elif cmd == "/debug":
            await self._print_debug()
        elif cmd == "/trace":
            self._print_trace()
        elif cmd == "/trace_summary":
            self._print_trace_summary()
        elif cmd == "/proactive_on":
            await self.coordinator.resume_proactivity()
            print("主动回复已开启\n")
        elif cmd == "/proactive_off":
            await self.coordinator.pause_proactivity()
            print("主动回复已暂停\n")
        elif cmd == "/proactive_status":
            status = self.coordinator.get_proactivity_status()
            print(f"主动回复启用: {status['enabled']}")
            print(f"后台任务运行: {status['task_active']}")
            print(f"检查间隔: {status['check_interval']}")
            print(f"上下文: {status['context']}\n")
        else:
            print(f"未知命令: {command}")
            print("输入 /help 查看帮助\n")

    def _print_help(self) -> None:
        """打印帮助"""
        print("\n可用命令:")
        print("  /help           - 显示帮助")
        print("  /status         - 显示系统状态")
        print("  /memory         - 显示记忆状态")
        print("  /world          - 显示世界状态")
        print("  /debug          - 显示调试信息")
        print("  /trace          - 显示本轮六脑协作过程")
        print("  /trace_summary  - 显示本轮摘要")
        print("  /proactive_on   - 开启主动回复")
        print("  /proactive_off  - 关闭主动回复")
        print("  /proactive_status - 显示主动回复状态")
        print("  /quit           - 退出程序\n")

    def _print_status(self) -> None:
        """打印状态"""
        state = self.coordinator.get_agent_state()
        print("\n系统状态:")
        print(f"  运行中: {state.get('is_running', False)}")
        print(f"  会话ID: {state.get('conversation_id', 'N/A')}")
        print(f"  可用工具: {state.get('tools_available', [])}")
        print(f"  NPC管理器: {'启用' if state.get('npc_manager_enabled') else '禁用'}")
        print(f"  世界内容: {'启用' if state.get('world_content_enabled') else '禁用'}\n")

    def _print_memory(self) -> None:
        """打印记忆"""
        core_memory = self.components.get("core_memory")
        episodic_memory = self.components.get("episodic_memory")
        working_memory = self.components.get("working_memory")

        print("\n记忆状态:")
        if core_memory:
            print(f"\n核心记忆:\n{core_memory.to_prompt_context()}")
        if episodic_memory:
            print(f"\n事件记忆:\n{episodic_memory.to_prompt_context()}")
        if working_memory:
            print(f"\n工作记忆:\n{working_memory.to_prompt_context()}\n")

    async def _print_world(self) -> None:
        """打印世界状态"""
        world_runtime = self.components.get("world_runtime")
        if world_runtime:
            snapshot = await world_runtime.get_world_snapshot()
            print("\n世界状态:")
            print(f"  时间: {snapshot.world_time}")
            print(f"  天气: {snapshot.weather}")
            print(f"  位置: {snapshot.location}")
            print(f"  NPC 数量: {len(snapshot.npcs)}\n")
        else:
            print("\n世界状态模块不可用\n")

    async def _print_debug(self) -> None:
        """打印调试信息"""
        print("\n" + "=" * 50)
        print("调试信息")
        print("=" * 50)

        world_runtime = self.components.get("world_runtime")
        if world_runtime:
            snapshot = await world_runtime.get_world_snapshot()
            print("\n[世界状态]")
            print(f"  版本: {snapshot.version}")
            print(f"  时间: {snapshot.world_time}")
            print(f"  时间段: {snapshot.time_period}")
            print(f"  天气: {snapshot.weather}")
            print(f"  位置: {snapshot.location}")
            print(f"  能量: {snapshot.energy:.2f}")
            print(f"  饥饿: {snapshot.hunger:.2f}")
            print(f"  事件数: {len(snapshot.recent_events)}")

            save_info = world_runtime.get_save_info() if hasattr(world_runtime, "get_save_info") else {}
            if save_info.get("exists"):
                print(f"  持久化: 已保存 ({save_info.get('modified', 'N/A')})")
            else:
                print("  持久化: 未保存")

        llm = self.components.get("llm")
        if llm:
            llm_type = type(llm).__name__
            print("\n[LLM]")
            print(f"  类型: {llm_type}")
            if hasattr(llm, "model_name"):
                print(f"  模型: {llm.model_name}")
            elif hasattr(llm, "model"):
                print(f"  模型: {llm.model}")

        core_memory = self.components.get("core_memory")
        episodic_memory = self.components.get("episodic_memory")
        working_memory = self.components.get("working_memory")

        print("\n[记忆计数]")
        if core_memory:
            entries = core_memory.get_all_entries() if hasattr(core_memory, "get_all_entries") else []
            print(f"  核心记忆: {len(entries)} 条")
        if episodic_memory:
            events = episodic_memory.get_all_events() if hasattr(episodic_memory, "get_all_events") else []
            print(f"  事件记忆: {len(events)} 条")
        if working_memory:
            entries = working_memory._entries if hasattr(working_memory, "_entries") else []
            print(f"  工作记忆: {len(entries)} 条")

        state = self.coordinator.get_agent_state()
        print("\n[运行状态]")
        print(f"  运行中: {state.get('is_running', False)}")
        print(f"  会话ID: {state.get('conversation_id', 'N/A')}")
        print(f"  NPC管理器: {'启用' if state.get('npc_manager_enabled') else '禁用'}")
        print(f"  世界内容: {'启用' if state.get('world_content_enabled') else '禁用'}")

        if self.last_response and getattr(self.last_response, "debug", None):
            print("\n[上一轮响应调试]")
            print(f"  phase: {self.last_response.debug.get('phase', 'unknown')}")
            print(f"  warnings: {self.last_response.debug.get('warnings', [])}")

        print("\n" + "=" * 50 + "\n")

    def _print_trace(self) -> None:
        """显示完整 trace"""
        if not self.last_response:
            print("\n暂无可追踪内容，请先进行一轮对话。\n")
            return

        turn_context = getattr(self.last_response, "_turn_context", None)
        if not turn_context:
            print("\n当前响应没有附带 turn_context，无法展示 trace。\n")
            return

        try:
            view = self.trace_builder.build(turn_context)
            output = self.cli_exporter.export(view)
            print("\n" + output + "\n")
        except Exception as e:
            logger.exception("构建 trace 失败")
            print(f"\n[错误] 构建 trace 失败: {e}\n")

    def _print_trace_summary(self) -> None:
        """显示 trace 摘要"""
        if not self.last_response:
            print("\n暂无可追踪内容，请先进行一轮对话。\n")
            return

        turn_context = getattr(self.last_response, "_turn_context", None)
        if not turn_context:
            print("\n当前响应没有附带 turn_context，无法展示 trace。\n")
            return

        try:
            view = self.trace_builder.build(turn_context)
            output = self.cli_exporter.export_summary(view)
            print("\n" + output + "\n")
        except Exception as e:
            logger.exception("构建 trace 摘要失败")
            print(f"\n[错误] 构建 trace 摘要失败: {e}\n")


async def main_async() -> None:
    """异步主函数"""
    logger.info("启动 V9...")

    persona = {
        "identity": "小雨，一个温柔善良的 AI 助手",
        "personality": {"value": "温柔、善良、有同理心", "category": "preference"},
        "user_relation": {"value": "用户是好朋友", "category": "relationship"}
    }

    components = await create_v9_application({"persona": persona})

    cli = CLIInterface(components)
    await cli.start()


def main() -> None:
    """主入口"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()