export type RoleType = "user" | "spouse" | "child" | "friend" | "elder" | "unknown";
export type GroupType = "family" | "friends" | "couple" | "solo" | "unknown";
export type ConflictType =
  | "energy_mismatch"
  | "diet_conflict"
  | "budget_conflict"
  | "pace_conflict"
  | "photo_vs_practical"
  | "indoor_outdoor"
  | "unknown";
export type DecisionType = "activity" | "dining" | "route" | "timeline" | "budget";
export type StrategyType =
  | "rotate_priority"
  | "soften_conflict"
  | "compensate_loser"
  | "min_regret"
  | "constraint_first";
export type PlanType = "plan_a" | "plan_b" | "recommended";
export type PlanState =
  | "pending"
  | "confirmed"
  | "executing"
  | "completed"
  | "replanning"
  | "failed"
  | "feedback";
export type StageType = "energy_release" | "explore" | "dine" | "relax" | "transport" | "buffer";
export type TimelineItemType = "activity" | "transport" | "dining" | "buffer";
export type ExecutionAction =
  | "book_restaurant"
  | "book_activity"
  | "call_taxi"
  | "share_plan"
  | "order_gift";
export type ExecutionStatus = "pending" | "running" | "confirmed" | "failed" | "cancelled";
export type EventType =
  | "queue_overflow"
  | "weather_change"
  | "user_feedback"
  | "booking_failed"
  | "time_overrun";

export interface Location {
  lat: number;
  lon: number;
}

export interface PlanPreviewRequest {
  user_id: string;
  query: string;
  city: string;
  start_time: string;
  duration_minutes: number;
  location?: Location | null;
}

export interface RoleProfile {
  role_id: string;
  role_type: RoleType;
  display_name: string;
  age: number | null;
  hard_constraints: string[];
  soft_preferences: string[];
  hidden_needs: string[];
  risk_points: string[];
  priority_weight: number;
  confidence: number;
}

export interface GroupContext {
  group_type: GroupType;
  roles: RoleProfile[];
  group_size: number;
  scene_label: string;
  inferred_constraints: string[];
  clarification_questions: string[];
  confidence_summary: Record<string, number>;
}

export interface Conflict {
  conflict_id: string;
  conflict_type: ConflictType;
  involved_roles: string[];
  description: string;
  severity: number;
  affected_decisions: DecisionType[];
  evidence: string[];
  resolution_hint: string;
}

export interface NegotiationStrategy {
  strategy_id: string;
  strategy_type: StrategyType;
  target_conflicts: string[];
  explanation: string;
  stage_policy: Record<string, unknown>;
  compensation_policy: Record<string, unknown>;
}

export interface ExperienceScores {
  photo_score: number;
  conversation_score: number;
  novelty_score: number;
  relax_score: number;
}

export interface POI {
  id: string;
  name: string;
  category: string;
  city: string;
  area: string | null;
  address: string | null;
  lon: number;
  lat: number;
  avg_price: number | null;
  open_hours: string | null;
  avg_stay_minutes: number | null;
  indoor: boolean;
  weather_fit: string[];
  energy_level: number;
  crowd_risk: string;
  queue_risk: string;
  suitable_for: string[];
  activity_tags: string[];
  mood_tags: string[];
  experience_scores: ExperienceScores;
  facilities: Record<string, unknown>;
  business_rules: Record<string, unknown>;
  persona_fit: Record<string, number>;
  conflict_relief_tags: string[];
}

export interface Stage {
  stage_id: string;
  stage_type: StageType;
  name: string;
  experience_goal: string;
  priority_role_id: string | null;
  duration_minutes: number;
  energy_level: number;
  constraints: Record<string, unknown>;
  selected_poi: POI | null;
  fallback_pois: POI[];
  reasoning: string;
}

export interface TimelineItem {
  time: string;
  type: TimelineItemType;
  poi_id: string | null;
  poi_name: string | null;
  mode: string | null;
  duration_minutes: number;
  estimated_cost: number;
  notes: string;
}

export interface SatisfactionScore {
  role_id: string;
  score: number;
  reasons: string[];
  sacrificed_points: string[];
  compensation: string | null;
}

export interface PlanCandidate {
  plan_id: string;
  plan_type: PlanType;
  title: string;
  theme: string;
  strategy: NegotiationStrategy | null;
  stages: Stage[];
  timeline: TimelineItem[];
  satisfaction_scores: SatisfactionScore[];
  overall_score: number;
  min_role_score: number;
  fairness_score: number;
  tradeoff_summary: string;
  recommendation_reason: string;
  route_segments: Record<string, unknown>[];
}

export interface ExecutionTask {
  task_id: string;
  action: ExecutionAction;
  poi_id: string | null;
  status: ExecutionStatus;
  depends_on: string[];
  params: Record<string, unknown>;
  result: Record<string, unknown>;
  mock_scenario: string;
}

export interface PlanOutput {
  session_id: string;
  user_id: string;
  created_at: string;
  input_query: string;
  inferred_context: GroupContext;
  conflicts: Conflict[];
  negotiation_strategies: NegotiationStrategy[];
  plan_candidates: PlanCandidate[];
  recommended_plan_id: string;
  execution_graph: ExecutionTask[];
  plan_version: number;
  state: PlanState;
  share_message: string;
  replan_reason: string | null;
}

export interface PlanEvent {
  event_id?: string;
  session_id: string;
  event_type: EventType;
  affected_poi_id?: string | null;
  affected_stage_id?: string | null;
  severity: number;
  payload: Record<string, unknown>;
  created_at?: string;
}

export interface ExecutionResponse {
  success: boolean;
  tasks: ExecutionTask[];
  plan: PlanOutput;
}

export interface HealthResponse {
  status: string;
  app: string;
  env: string;
}

export interface FeedbackRequest {
  rating?: number | null;
  raw_feedback: string;
  tags: string[];
  payload: Record<string, unknown>;
}

export interface FeedbackResponse {
  success: boolean;
  session_id: string;
  saved_feedback: Record<string, unknown>;
}

export interface StepStartEvent {
  step: number;
  name: string;
  label: string;
}

export interface StepCompleteEvent {
  step: number;
  name: string;
  label: string;
  result: Record<string, unknown>;
}

export interface ToolCallResult {
  success: boolean;
  data?: unknown;
  error_message?: string;
  latency_ms: number;
  mock_scenario?: string;
  error_code?: string;
  [key: string]: unknown;
}

export interface ToolCallEvent {
  step: number;
  tool: string;
  action: string;
  params: Record<string, unknown>;
  result: ToolCallResult;
}

export interface CandidateStartEvent {
  candidate_index: number;
  plan_type: PlanType | string;
  title: string;
}

export interface CandidateCompleteEvent {
  candidate_index: number;
  plan_type: PlanType | string;
  title: string;
  overall_score: number;
  min_role_score: number;
  fairness_score: number;
}

export interface PlanCompleteEvent {
  session_id: string;
  recommended_plan_id: string;
  candidates_count: number;
}

export interface PlanStreamErrorEvent {
  step: number | null;
  error: string;
}

export type StreamEventName =
  | "step_start"
  | "step_complete"
  | "tool_call"
  | "candidate_start"
  | "candidate_complete"
  | "plan_complete"
  | "error";

export type PlanPreviewStreamEvent =
  | { event: "step_start"; data: StepStartEvent }
  | { event: "step_complete"; data: StepCompleteEvent }
  | { event: "tool_call"; data: ToolCallEvent }
  | { event: "candidate_start"; data: CandidateStartEvent }
  | { event: "candidate_complete"; data: CandidateCompleteEvent }
  | { event: "plan_complete"; data: PlanCompleteEvent }
  | { event: "error"; data: PlanStreamErrorEvent };

export type StepStatus = "pending" | "running" | "completed" | "error";
export type CandidateStatus = "pending" | "running" | "completed";

export interface StepState {
  step: number;
  name: string;
  label: string;
  status: StepStatus;
  result?: Record<string, unknown>;
  toolCalls: ToolCallEvent[];
  startTime?: number;
  endTime?: number;
}

export interface CandidateState {
  candidate_index: number;
  plan_type: string;
  title: string;
  status: CandidateStatus;
  overall_score?: number;
  min_role_score?: number;
  fairness_score?: number;
}
