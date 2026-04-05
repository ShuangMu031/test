import { SendMessagePayload } from '../types/trace';

interface ChatResponse {
  reply: {
    content: string;
    timestamp: string;
    emotion: string;
  };
  turn: {
    turn_id: string;
    phase: string;
    trace_id: string;
    dominant_brain: string;
    final_action: string;
    model_tier: string;
    has_world_content: boolean;
    has_npc: boolean;
    has_tool: boolean;
    warnings: string[];
  };
  trace_summary: {
    brain_views: Array<{
      brain_name: string;
      display_name: string;
      triggered: boolean;
      conclusion: string;
      key_fields: Record<string, unknown>;
      influence_target: string[];
      duration_ms: number;
      has_error: boolean;
    }>;
    timeline: string[];
    decision_tensions: Array<Record<string, unknown>>;
    response_source: string;
    final_response: string;
  };
}

export const chatApi = {
  sendMessage: async (payload: SendMessagePayload): Promise<ChatResponse> => {
    // 模拟 API 调用，实际项目中替换为真实的 fetch 调用
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          reply: {
            content: "我听出来你现在真的有点难受，我们先慢一点。",
            timestamp: new Date().toISOString(),
            emotion: "sad"
          },
          turn: {
            turn_id: `turn_${Date.now()}`,
            phase: "responded",
            trace_id: `trace_${Date.now()}`,
            dominant_brain: "emotion",
            final_action: "comfort_first",
            model_tier: "standard",
            has_world_content: false,
            has_npc: false,
            has_tool: false,
            warnings: []
          },
          trace_summary: {
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
                duration_ms: 42,
                has_error: false
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
                duration_ms: 35,
                has_error: false
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
                duration_ms: 28,
                has_error: false
              },
              {
                brain_name: "npc",
                display_name: "NPC脑",
                triggered: false,
                conclusion: "无需NPC介入",
                key_fields: {},
                influence_target: [],
                duration_ms: 22,
                has_error: false
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
                duration_ms: 45,
                has_error: false
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
                duration_ms: 38,
                has_error: false
              }
            ],
            timeline: [
              "context_collected",
              "brains_completed",
              "policy_checked",
              "responded"
            ],
            decision_tensions: [],
            response_source: "llm",
            final_response: "我听出来你现在真的有点难受，我们先慢一点。"
          }
        });
      }, 1000);
    });
  }
};