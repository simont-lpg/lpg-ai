export interface Document {
  id: string;
  content: string;
  meta: {
    namespace?: string;
    [key: string]: any;
  };
  embedding?: number[];
}

export interface IngestResponse {
  files_ingested: number;
  total_chunks: number;
}

export interface QueryResponse {
  answer: string;
  sources: Document[];
}

export interface ErrorResponse {
  error: string;
  details?: string;
} 