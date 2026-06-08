import http from "./http";

export interface InterviewStartPayload {
  knowledge_base_id: number;
  question_id?: number;
  source_document_id?: number;
  focus_topic?: string;
  difficulty?: string;
  question_type?: string;
  question_strategy?: string;
  drill_mode?: string;
  question_count?: number;
}

export interface InterviewStartResponse {
  session_id: string;
  knowledge_base_id: number;
  question_id: number;
  question: string;
  source_document_id: number | null;
  source_document_name: string | null;
  focus_topic: string | null;
  difficulty: string | null;
  question_tags: string[];
  question_strategy: string;
  drill_mode: string;
  question_count: number;
  active_question_number: number;
  status: string;
  started_at: string;
}

export interface InterviewAnswerPayload {
  session_id: string;
  answer: string;
}

export interface InterviewFeedbackResponse {
  session_id: string;
  question_id: number;
  question: string;
  difficulty: string | null;
  question_tags: string[];
  answer: string;
  feedback: string;
  overall_score: number;
  strengths: string[];
  improvements: string[];
  suggested_followup: string | null;
  next_question: string | null;
  next_prompt_type: string | null;
  current_round: number;
  max_rounds: number;
  can_continue: boolean;
  drill_mode: string;
  question_count: number;
  active_question_number: number;
  status: string;
  summary: string | null;
  summary_meta: Record<string, any> | null;
  updated_at: string;
}

export interface InterviewTurnItem {
  id: number;
  role: string;
  content: string;
  meta_json: Record<string, any> | any[] | null;
  created_at: string;
}

export interface InterviewSessionListItem {
  session_id: string;
  knowledge_base_id: number;
  question_id: number;
  question: string;
  source_document_id: number | null;
  source_document_name: string | null;
  focus_topic: string | null;
  difficulty: string | null;
  question_tags: string[];
  question_strategy: string;
  drill_mode: string;
  question_count: number;
  active_question_number: number;
  status: string;
  overall_score: number | null;
  started_at: string;
  updated_at: string;
  current_round: number;
}

export interface InterviewSessionDetail {
  session_id: string;
  knowledge_base_id: number;
  question_id: number;
  question: string;
  source_document_id: number | null;
  source_document_name: string | null;
  focus_topic: string | null;
  difficulty: string | null;
  question_tags: string[];
  question_strategy: string;
  drill_mode: string;
  question_count: number;
  active_question_number: number;
  reference_answer: string | null;
  answer: string | null;
  feedback: string | null;
  overall_score: number | null;
  strengths: string[];
  improvements: string[];
  suggested_followup: string | null;
  next_question: string | null;
  next_prompt_type: string | null;
  current_round: number;
  max_rounds: number;
  can_continue: boolean;
  status: string;
  summary: string | null;
  summary_meta: Record<string, any> | null;
  started_at: string;
  updated_at: string;
  turns: InterviewTurnItem[];
}

export interface TrainingAnalysisCountItem {
  label: string;
  count: number;
}

export interface TrainingAnalysisScorePoint {
  session_id: string;
  score: number;
  started_at: string;
}

export interface TrainingDrillRecommendation {
  focus_label: string;
  title: string;
  description: string;
  knowledge_base_id: number | null;
  source_document_id: number | null;
  source_document_name: string | null;
  question_type: string | null;
  drill_mode: string;
  question_count: number;
  question_strategy: string;
}

export interface TrainingFocusEffectItem {
  focus_label: string;
  session_count: number;
  average_score: number;
  latest_score: number;
  best_score: number;
  score_delta: number;
  last_practiced_at: string;
}

export interface TrainingAnalysisResponse {
  knowledge_base_id: number | null;
  total_sessions: number;
  completed_sessions: number;
  average_score: number | null;
  latest_score: number | null;
  common_weak_points: TrainingAnalysisCountItem[];
  common_strengths: TrainingAnalysisCountItem[];
  question_type_breakdown: TrainingAnalysisCountItem[];
  source_document_breakdown: TrainingAnalysisCountItem[];
  recent_scores: TrainingAnalysisScorePoint[];
  recommended_focus: string[];
  focus_drills: TrainingDrillRecommendation[];
  focus_drill_effects: TrainingFocusEffectItem[];
}

export async function startInterview(payload: InterviewStartPayload) {
  const { data } = await http.post<InterviewStartResponse>("/interview/start", payload, {
    timeout: 120000,
  });
  return data;
}

export async function submitInterviewAnswer(payload: InterviewAnswerPayload) {
  const { data } = await http.post<InterviewFeedbackResponse>("/interview/answer", payload, {
    timeout: 120000,
  });
  return data;
}

export async function getInterviewSessions(knowledgeBaseId?: number) {
  const { data } = await http.get<InterviewSessionListItem[]>("/interview/sessions", {
    params: knowledgeBaseId ? { knowledge_base_id: knowledgeBaseId } : undefined,
  });
  return data;
}

export async function getInterviewSessionDetail(sessionId: string) {
  const { data } = await http.get<InterviewSessionDetail>(`/interview/sessions/${sessionId}`);
  return data;
}

export async function deleteInterviewSession(sessionId: string) {
  await http.delete(`/interview/sessions/${sessionId}`);
}

export async function getTrainingAnalysis(knowledgeBaseId?: number) {
  const { data } = await http.get<TrainingAnalysisResponse>("/interview/analysis", {
    params: knowledgeBaseId ? { knowledge_base_id: knowledgeBaseId } : undefined,
  });
  return data;
}
