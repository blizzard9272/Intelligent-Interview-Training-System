import http from "./http";

export interface InterviewStartPayload {
  knowledge_base_id: number;
  question_id?: number;
  difficulty?: string;
  question_type?: string;
}

export interface InterviewStartResponse {
  session_id: string;
  knowledge_base_id: number;
  question_id: number;
  question: string;
  difficulty: string | null;
  question_tags: string[];
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
  current_round: number;
  max_rounds: number;
  can_continue: boolean;
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
  difficulty: string | null;
  question_tags: string[];
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
  difficulty: string | null;
  question_tags: string[];
  reference_answer: string | null;
  answer: string | null;
  feedback: string | null;
  overall_score: number | null;
  strengths: string[];
  improvements: string[];
  suggested_followup: string | null;
  next_question: string | null;
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
