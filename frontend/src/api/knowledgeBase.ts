import http from "./http";

export interface KnowledgeBaseItem {
  id: number;
  name: string;
  description: string | null;
  job_role: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateKnowledgeBasePayload {
  name: string;
  description?: string;
  job_role?: string;
}

export async function getKnowledgeBases() {
  const { data } = await http.get<KnowledgeBaseItem[]>("/knowledge-bases");
  return data;
}

export async function createKnowledgeBase(payload: CreateKnowledgeBasePayload) {
  const { data } = await http.post<KnowledgeBaseItem>("/knowledge-bases", payload);
  return data;
}
