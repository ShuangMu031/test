import { TurnTrace } from '../types/trace';

export const traceApi = {
  fetchTrace: async (traceId: string): Promise<TurnTrace> => {
    // 模拟 API 调用，实际项目中替换为真实的 fetch 调用
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          turn_id: `turn_${Date.now()}`,
          phase: "responded",
          user_input_summary: "我今天情绪很差",
          primary_intent: "emotional_support",
          dominant_brain: "emotion",
          final_action: "comfort_first",
          has_world_content: false,
          has_npc: false,
          has_tool: false,
          model_tier: "standard",
          total_duration_ms: 218,
          timeline: [
            "context_collected",
            "brains_completed",
            "policy_checked",
            "responded"
          ],
          brain_views: [
            {
              brain_name: "emotion",
              display_name: "情绪脑",
              triggered: true,
              conclusion: "用户处于低效价情绪，支持需求较高",
              key_fields: {
                primary_emotion: "sad",
                valence: -0.72,
                arousal: 0.41,
                support_need: "high"
              },
              influence_target: ["memory", "behavior", "supervisor"],
              telemetry: {
                processing_time_ms: 42,
                model_calls: 1
              },
              monologue: "用户表达了负面情绪，需要提供情感支持",
              actions: ["analyze_emotion", "assess_support_need"],
              interactions: [],
              tool_calls: [],
              llm_thought: "用户情绪低落，需要优先安慰",
              duration_ms: 42,
              has_error: false,
              error_msg: ""
            },
            {
              brain_name: "memory",
              display_name: "记忆脑",
              triggered: true,
              conclusion: "检索到相关记忆",
              key_fields: {
                working_memory: "用户近期情绪低落",
                episodic_memory: "用户上周提到工作压力",
                core_memory: "用户重视情感支持"
              },
              influence_target: ["behavior"],
              telemetry: {
                processing_time_ms: 35,
                memory_retrieved: 3
              },
              monologue: "找到了与用户情绪相关的记忆",
              actions: ["retrieve_working_memory", "retrieve_episodic_memory"],
              interactions: [],
              tool_calls: [],
              llm_thought: "用户近期有工作压力，这可能是情绪低落的原因",
              duration_ms: 35,
              has_error: false,
              error_msg: ""
            },
            {
              brain_name: "world",
              display_name: "世界脑",
              triggered: false,
              conclusion: "无需世界内容更新",
              key_fields: {
                time: "2026-04-05T13:20:00Z",
                location: "Digital World",
                weather: "sunny"
              },
              influence_target: [],
              telemetry: {
                processing_time_ms: 28
              },
              monologue: "当前世界状态稳定，无需更新",
              actions: ["check_time", "check_location"],
              interactions: [],
              tool_calls: [],
              llm_thought: "世界状态与当前情绪支持任务无关",
              duration_ms: 28,
              has_error: false,
              error_msg: ""
            },
            {
              brain_name: "npc",
              display_name: "NPC脑",
              triggered: false,
              conclusion: "无需NPC介入",
              key_fields: {},
              influence_target: [],
              telemetry: {
                processing_time_ms: 22
              },
              monologue: "当前场景不需要NPC参与",
              actions: ["check_npc_availability"],
              interactions: [],
              tool_calls: [],
              llm_thought: "情感支持任务由系统直接处理即可",
              duration_ms: 22,
              has_error: false,
              error_msg: ""
            },
            {
              brain_name: "behavior",
              display_name: "行为脑",
              triggered: true,
              conclusion: "采取安慰策略",
              key_fields: {
                action: "comfort",
                priority: "high",
                tool_calls: []
              },
              influence_target: ["supervisor"],
              telemetry: {
                processing_time_ms: 45
              },
              monologue: "基于情绪和记忆分析，决定采取安慰策略",
              actions: ["plan_comfort_strategy"],
              interactions: [],
              tool_calls: [],
              llm_thought: "用户需要情感支持，应优先安慰",
              duration_ms: 45,
              has_error: false,
              error_msg: ""
            },
            {
              brain_name: "supervisor",
              display_name: "总控脑",
              triggered: true,
              conclusion: "批准安慰策略",
              key_fields: {
                model_tier: "standard",
                suppress_tool_calls: true,
                suppress_npc: true
              },
              influence_target: [],
              telemetry: {
                processing_time_ms: 38
              },
              monologue: "策略符合当前场景需求，批准执行",
              actions: ["approve_strategy", "set_model_tier"],
              interactions: [],
              tool_calls: [],
              llm_thought: "安慰策略是当前最佳选择，无需工具或NPC介入",
              duration_ms: 38,
              has_error: false,
              error_msg: ""
            }
          ],
          plan_diff: {
            original: "general_response",
            modified: "comfort_first"
          },
          execution_view: {
            tools_executed: [],
            tools_failed: [],
            npc_interacted: false,
            npc_name: "",
            npc_mode: ""
          },
          reply_gate: {
            passed: true,
            overridden_by: "",
            response_source: "llm",
            model_tier: "standard"
          },
          decision_chain: {
            steps: [
              "context_collection",
              "emotion_analysis",
              "memory_retrieval",
              "world_check",
              "npc_check",
              "behavior_planning",
              "supervisor_approval",
              "response_generation"
            ]
          },
          memory_commit: {
            working_memory: "用户今天情绪很差",
            episodic_memory: "2026-04-05: 用户表达情绪低落",
            core_memory: "用户重视情感支持"
          },
          proactive: {
            triggered: false,
            reason: "用户当前需要情感支持，不适合主动话题"
          },
          decision_tensions: [],
          final_response: "我听出来你现在真的有点难受，我们先慢一点。",
          response_source: "llm",
          warnings: []
        });
      }, 500);
    });
  }
};