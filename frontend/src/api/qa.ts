import http from "./http";

export interface QAReference {
  document_id: number;
  file_name: string;
  chunk_index: number;
  snippet: string;
}

export interface AskPayload {
  knowledge_base_id: number;
  question: string;
  session_id?: number;
}

export interface AskResponse {
  session_id: number;
  answer: string;
  references: QAReference[];
}

export interface QAMessage {
  role: string;
  content: string;
  references_json: QAReference[] | null;
}

export interface QASessionItem {
  id: number;
  knowledge_base_id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface QASessionDetail {
  id: number;
  knowledge_base_id: number;
  title: string | null;
  messages: QAMessage[];
}

export async function askQuestion(payload: AskPayload) {
  const { data } = await http.post<AskResponse>("/qa/ask", payload, {
    timeout: 120000
  });
  return data;
}

export async function getQASessions() {
  const { data } = await http.get<QASessionItem[]>("/qa/sessions");
  return data;
}

export async function getQASessionDetail(sessionId: number) {
  const { data } = await http.get<QASessionDetail>(`/qa/sessions/${sessionId}`);
  return data;
}

export async function deleteQASession(sessionId: number) {
  await http.delete(`/qa/sessions/${sessionId}`);
}
