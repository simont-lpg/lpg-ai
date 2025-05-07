import { deleteDocument, listFiles, uploadFiles, queryRAG } from './api';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the config module
vi.mock('./config', () => ({
  getConfig: vi.fn().mockReturnValue({ apiBaseUrl: 'http://test-api' })
}));

// Mock fetch globally
global.fetch = vi.fn();

// Mock DataTransfer
class MockDataTransfer {
  private fileList: File[] = [];

  get files() {
    return Object.assign(this.fileList, {
      item: (index: number) => this.fileList[index],
      length: this.fileList.length
    });
  }

  get items() {
    return {
      add: (file: File) => {
        this.fileList.push(file);
      }
    };
  }
}

// @ts-ignore
global.DataTransfer = MockDataTransfer;

describe('API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listFiles', () => {
    it('fetches files successfully', async () => {
      const mockFiles = [
        { filename: 'test.pdf', id: '1', namespace: 'default', document_count: 1, file_size: 1024 }
      ];

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ files: mockFiles })
      });

      const result = await listFiles();
      expect(result).toEqual(mockFiles);
      expect(fetch).toHaveBeenCalledWith('http://test-api/files');
    });

    it('handles errors', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false
      });

      await expect(listFiles()).rejects.toThrow('Failed to fetch files');
    });
  });

  describe('deleteDocument', () => {
    it('deletes document successfully', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true
      });

      await deleteDocument('test.pdf');
      expect(fetch).toHaveBeenCalledWith('http://test-api/documents/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_name: 'test.pdf' }),
      });
    });

    it('handles errors', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: { error: 'Delete failed' } })
      });

      await expect(deleteDocument('test.pdf')).rejects.toThrow('Delete failed');
    });
  });

  describe('queryRAG', () => {
    it('queries successfully', async () => {
      const mockResponse = {
        answers: ['test answer'],
        documents: [{ content: 'test', meta: {}, id: '1' }]
      };

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await queryRAG('test query', 3);
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith('http://test-api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: 'test query',
          top_k: 3,
          file_id: undefined,
        }),
      });
    });

    it('handles errors', async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false
      });

      await expect(queryRAG('test query')).rejects.toThrow('Failed to query RAG');
    });
  });
}); 