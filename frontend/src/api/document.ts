import http from "./http";

export interface DocumentItem {
  id: number;
  knowledge_base_id: number;
  file_name: string;
  file_type: string;
  file_path: string;
  file_size: number | null;
  status: string;
  parse_error: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  document_id: number;
  task_id: number;
  status: string;
}

export interface DocumentChunkItem {
  chunk_index: number;
  section_title: string | null;
  page_no: number | null;
  content: string;
}

export async function getDocuments(knowledgeBaseId?: number) {
  const { data } = await http.get<DocumentItem[]>("/documents", {
    params: knowledgeBaseId ? { knowledge_base_id: knowledgeBaseId } : undefined
  });
  return data;
}

export async function uploadDocument(knowledgeBaseId: number, file: File) {
  const formData = new FormData();
  formData.append("knowledge_base_id", String(knowledgeBaseId));
  formData.append("file", file);

  const { data } = await http.post<DocumentUploadResponse>("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  return data;
}

export async function deleteDocument(documentId: number) {
  await http.delete(`/documents/${documentId}`);
}

export async function getDocumentChunks(documentId: number) {
  const { data } = await http.get<DocumentChunkItem[]>(`/documents/${documentId}/chunks`);
  return data;
}
