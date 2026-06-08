import http from "./http";

export interface QAReference {
  document_id: number;
  file_name: string;
  chunk_index: number;
  snippet: string;
  section_title?: string | null;
  content_type_hint?: string | null;
  document_kind?: string | null;
  starts_with_question?: boolean | null;
  context_role?: string | null;
}

export interface QARetrievalCandidate {
  file_name: string;
  chunk_index: number;
  section_title?: string | null;
  content_type_hint?: string | null;
  document_kind?: string | null;
  context_role?: string | null;
  distance?: number | null;
  retrieval_rank?: number | null;
  rerank_score?: number | null;
  matched_filters?: Record<string, unknown> | null;
}

export interface QARetrievalStep {
  filters: Record<string, unknown>;
  returned_count: number;
  candidates: QARetrievalCandidate[];
}

export interface QAContextBlock {
  role: string;
  title: string;
  references: QAReference[];
}

export interface QADebugTrace {
  route_intent: string;
  rerank_enabled: boolean;
  query_plan: Record<string, unknown>[];
  retrieval_steps: QARetrievalStep[];
  reranked_results: QARetrievalCandidate[];
  context_blocks: QAContextBlock[];
  structured_context: string;
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
  debug_trace?: QADebugTrace | null;
}

export interface QAStreamMetaEvent {
  session_id: number;
}

export interface QAStreamDeltaEvent {
  content: string;
}

export interface QAStreamFinalEvent {
  session_id: number;
  references: QAReference[];
  debug_trace?: QADebugTrace | null;
}

export interface QAMessage {
  role: string;
  content: string;
  references_json: QAReference[] | null;
  debug_trace?: QADebugTrace | null;
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

export async function askQuestionStream(
  payload: AskPayload,
  handlers: {
    onMeta?: (event: QAStreamMetaEvent) => void;
    onDelta?: (event: QAStreamDeltaEvent) => void;
    onFinal?: (event: QAStreamFinalEvent) => void;
  }
) {
  const token = localStorage.getItem("access_token");
  const response = await fetch("http://localhost:8000/api/v1/qa/ask/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    let detail = "问答失败，请稍后重试。";
    try {
      const data = await response.json();
      if (data?.detail) {
        detail = String(data.detail);
      }
    } catch {
      // Ignore JSON parse failure.
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });

    while (buffer.includes("\n\n")) {
      const boundary = buffer.indexOf("\n\n");
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const parsed = parseSSEEvent(rawEvent);
      if (!parsed) {
        continue;
      }
      if (parsed.event === "meta" && handlers.onMeta) {
        handlers.onMeta(parsed.data as QAStreamMetaEvent);
      }
      if (parsed.event === "delta" && handlers.onDelta) {
        handlers.onDelta(parsed.data as QAStreamDeltaEvent);
      }
      if (parsed.event === "final" && handlers.onFinal) {
        handlers.onFinal(parsed.data as QAStreamFinalEvent);
      }
    }
  }
}

function parseSSEEvent(rawEvent: string): { event: string; data: unknown } | null {
  const lines = rawEvent.split("\n");
  let eventName = "message";
  let dataLine = "";
  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    }
    if (line.startsWith("data:")) {
      dataLine += line.slice(5).trim();
    }
  }
  if (!dataLine) {
    return null;
  }
  return {
    event: eventName,
    data: JSON.parse(dataLine),
  };
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
