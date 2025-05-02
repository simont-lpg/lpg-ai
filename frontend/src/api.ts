import { getConfig } from './config';

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
    throw new Error('Failed to delete document');
  }
};

export const uploadFiles = async (files: FileList): Promise<void> => {
  const formData = new FormData();
  Array.from(files).forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${getConfig().apiBaseUrl}/ingest`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail?.error || 'Failed to upload files');
  }
};

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