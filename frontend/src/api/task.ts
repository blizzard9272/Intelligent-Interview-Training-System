import http from "./http";

export interface IngestionTaskItem {
  id: number;
  document_id: number;
  status: string;
  progress: number;
  message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export async function getTasks(documentId?: number) {
  const { data } = await http.get<IngestionTaskItem[]>("/tasks", {
    params: documentId ? { document_id: documentId } : undefined
  });
  return data;
}
