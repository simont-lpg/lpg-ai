import axios from 'axios';
import { Document, IngestResponse, QueryResponse, ErrorResponse } from '../types/api';

export type { Document };

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ingestDocument = async (file: File, namespace?: string): Promise<IngestResponse> => {
  const formData = new FormData();
  formData.append('files', file);
  if (namespace) {
    formData.append('namespace', namespace);
  }

  const response = await api.post<IngestResponse>('/ingest', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDocuments = async (namespace?: string): Promise<Document[]> => {
  const params = namespace ? { namespace } : undefined;
  const response = await api.get<Document[]>('/documents', { params });
  return response.data;
};

export const query = async (question: string, namespace?: string): Promise<QueryResponse> => {
  const response = await api.post<QueryResponse>('/query', {
    question,
    namespace,
  });
  return response.data;
};

export const deleteDocument = async (id: string): Promise<void> => {
  await api.delete(`/documents/${id}`);
}; 