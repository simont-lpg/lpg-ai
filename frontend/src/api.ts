const API_BASE_URL = 'http://localhost:8000';

export interface File {
  name: string;
  id: string;
}

export interface QueryResponse {
  answer: string;
  sources: Array<{
    content: string;
    metadata: Record<string, any>;
  }>;
}

export const listFiles = async (): Promise<File[]> => {
  const response = await fetch(`${API_BASE_URL}/files`);
  if (!response.ok) {
    throw new Error('Failed to fetch files');
  }
  return response.json();
};

export const deleteDocument = async (fileName: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: 'DELETE',
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

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    throw new Error('Failed to upload files');
  }
};

export const queryRAG = async (
  text: string,
  topK: number = 3,
  fileId?: string
): Promise<QueryResponse> => {
  const response = await fetch(`${API_BASE_URL}/query`, {
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