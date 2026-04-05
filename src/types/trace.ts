export type BrainName =
  | 'emotion'
  | 'memory'
  | 'world'
  | 'npc'
  | 'behavior'
  | 'supervisor';

export interface BrainTraceView {
  brain_name: BrainName;
  display_name: string;
  triggered: boolean;
  conclusion: string;
  key_fields: Record<string, unknown>;
  influence_target: string[];
  telemetry: Record<string, unknown>;
  monologue: string;
  actions: string[];
  interactions: string[];
  tool_calls: string[];
  llm_thought: string;
  duration_ms: number;
  has_error: boolean;
  error_msg: string;
}

export interface TurnTrace {
  turn_id: string;
  phase: string;
  user_input_summary: string;
  primary_intent: string;
  dominant_brain: BrainName;
  final_action: string;
  has_world_content: boolean;
  has_npc: boolean;
  has_tool: boolean;
  model_tier: string;
  total_duration_ms: number;
  timeline: string[];
  brain_views: BrainTraceView[];
  plan_diff: Record<string, unknown>;
  execution_view: Record<string, unknown>;
  reply_gate: Record<string, unknown>;
  decision_chain: { steps: string[] };
  memory_commit: Record<string, unknown>;
  proactive: Record<string, unknown>;
  decision_tensions: Array<Record<string, unknown>>;
  final_response: string;
  response_source: string;
  warnings: string[];
}

export interface SendMessagePayload {
  message: string;
  scene: 'service' | 'game' | 'companion';
  traceEnabled?: boolean;
  debug?: boolean;
}

export interface ChatTurnState {
  trace?: TurnTrace;
  selectedBrain?: BrainName;
  phase?: string;
}