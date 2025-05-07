import { getConfig } from './config';
import axios from 'axios';

export interface File {
  filename: string;
  namespace: string;
  document_count: number;
  id: string;
  file_size: number;  // Size in bytes
}

interface FileListResponse {
  files: File[];
}

export interface QueryResponse {
  answers: string[];
  documents: Array<{
    content: string;
    meta: Record<string, any>;
    id: string;
    score?: number;
  }>;
  error?: string;
}

export const listFiles = async (): Promise<File[]> => {
  const response = await fetch(`${getConfig().apiBaseUrl}/files`);
  if (!response.ok) {
    throw new Error('Failed to fetch files');
  }
  const data: FileListResponse = await response.json();
  return data.files;
};

export const deleteDocument = async (fileName: string): Promise<void> => {
  const response = await fetch(`${getConfig().apiBaseUrl}/documents/delete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ file_name: fileName }),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail?.error || 'Failed to delete document');
  }
};

export async function uploadFiles(
  files: globalThis.File[],
  namespace: string,
  onProgress: (phase: "upload", pct: number) => void
): Promise<string> {
  const form = new FormData();
  files.forEach(f => form.append("files", f));
  form.append("namespace", namespace);

  const response = await axios.post<{ upload_id: string }>(
    `${getConfig().apiBaseUrl}/ingest`,
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: e => {
        if (e.total) {
          const pct = Math.round((e.loaded * 100) / e.total);
          onProgress("upload", pct);
        }
      }
    }
  );
  return response.data.upload_id;
}

export function watchIngestProgress(
  uploadId: string,
  onProgress: (phase: "processing", pct: number) => void
) {
  const es = new EventSource(`${getConfig().apiBaseUrl}/ingest/progress/${uploadId}`);
  es.onmessage = evt => {
    const pct = parseInt(evt.data, 10);
    onProgress("processing", pct);
    if (pct >= 100) es.close();
  };
  es.onerror = () => { es.close(); };
  return () => es.close();
}

export const queryRAG = async (
  text: string,
  topK: number = 3,
  fileId?: string
): Promise<QueryResponse> => {
  const response = await fetch(`${getConfig().apiBaseUrl}/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      top_k: topK,
      file_id: fileId,
    }),
  });
  if (!response.ok) {
    throw new Error('Failed to query RAG');
  }
  return response.json();
}; 