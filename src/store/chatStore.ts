// 聊天状态管理
import { create } from 'zustand';
import { chatApi } from '../utils/api';
import { SendMessagePayload, TurnTrace, BrainName } from '../types/trace';

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string;
  emotion?: string;
}

interface ChatState {
  messages: Message[];
  inputValue: string;
  isLoading: boolean;
  error: string | null;
  currentTrace: TurnTrace | null;
  selectedBrain: BrainName | null;
  
  setInputValue: (value: string) => void;
  setSelectedBrain: (brain: BrainName | null) => void;
  sendMessage: (payload: SendMessagePayload) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  inputValue: '',
  isLoading: false,
  error: null,
  currentTrace: null,
  selectedBrain: null,
  
  setInputValue: (value) => set({ inputValue: value }),
  
  setSelectedBrain: (brain) => set({ selectedBrain: brain }),
  
  sendMessage: async (payload) => {
    const { messages } = get();
    const userMessage: Message = {
      id: Date.now().toString(),
      content: payload.message,
      isUser: true,
      timestamp: new Date().toISOString(),
    };
    
    set({ 
      messages: [...messages, userMessage],
      inputValue: '',
      isLoading: true,
      error: null 
    });
    
    try {
      const response = await chatApi.sendMessage(payload);
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.reply.content,
        isUser: false,
        timestamp: response.reply.timestamp,
        emotion: response.reply.emotion,
      };
      
      // 构建 trace 对象
      const trace: TurnTrace = {
        turn_id: response.turn.turn_id,
        phase: response.turn.phase,
        user_input_summary: payload.message,
        primary_intent: 'emotional_support',
        dominant_brain: response.turn.dominant_brain as BrainName,
        final_action: response.turn.final_action,
        has_world_content: response.turn.has_world_content,
        has_npc: response.turn.has_npc,
        has_tool: response.turn.has_tool,
        model_tier: response.turn.model_tier,
        total_duration_ms: response.trace_summary.brain_views.reduce((sum, brain) => sum + brain.duration_ms, 0),
        timeline: response.trace_summary.timeline,
        brain_views: response.trace_summary.brain_views.map(brain => ({
          brain_name: brain.brain_name as BrainName,
          display_name: brain.display_name,
          triggered: brain.triggered,
          conclusion: brain.conclusion,
          key_fields: brain.key_fields,
          influence_target: brain.influence_target,
          telemetry: {},
          monologue: '',
          actions: [],
          interactions: [],
          tool_calls: [],
          llm_thought: '',
          duration_ms: brain.duration_ms,
          has_error: brain.has_error,
          error_msg: ''
        })),
        plan_diff: {},
        execution_view: {},
        reply_gate: {},
        decision_chain: { steps: [] },
        memory_commit: {},
        proactive: {},
        decision_tensions: response.trace_summary.decision_tensions,
        final_response: response.trace_summary.final_response,
        response_source: response.trace_summary.response_source,
        warnings: response.turn.warnings
      };
      
      set({ 
        messages: [...messages, userMessage, aiMessage],
        currentTrace: trace,
        isLoading: false 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '发送消息失败',
        isLoading: false 
      });
    }
  },
  
  clearMessages: () => set({ messages: [], currentTrace: null, selectedBrain: null }),
  
  clearError: () => set({ error: null }),
}));