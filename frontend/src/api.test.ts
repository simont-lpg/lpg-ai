import { deleteDocument, listFiles, uploadFiles, queryRAG } from './api';
import { getConfig } from './config';

// Mock the config module
jest.mock('./config', () => ({
  getConfig: jest.fn()
}));

// Mock fetch globally
global.fetch = jest.fn();

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

describe('API', () => {
  const mockConfig = {
    apiBaseUrl: 'http://localhost:8000'
  };

  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
    (getConfig as jest.Mock).mockReturnValue(mockConfig);
  });

  describe('deleteDocument', () => {
    it('should make a POST request to /documents/delete with the file name', async () => {
      const fileName = 'test.pdf';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'success', deleted: 1 })
      });

      await deleteDocument(fileName);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/documents/delete',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ file_name: fileName }),
        }
      );
    });

    it('should throw an error if the request fails', async () => {
      const fileName = 'test.pdf';
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(deleteDocument(fileName)).rejects.toThrow('Failed to delete document');
    });
  });

  describe('listFiles', () => {
    it('should make a GET request to /files', async () => {
      const mockFiles = [{ filename: 'test.pdf', id: '1' }];
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ files: mockFiles })
      });

      const result = await listFiles();

      expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/files');
      expect(result).toEqual(mockFiles);
    });
  });

  describe('uploadFiles', () => {
    it('should make a POST request to /ingest with FormData', async () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      const fileList = dataTransfer.files;
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true
      });

      await uploadFiles(fileList);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/ingest',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      );
    });
  });

  describe('queryRAG', () => {
    it('should make a POST request to /query with the query parameters', async () => {
      const query = 'test query';
      const mockResponse = { answers: ['answer'], documents: [] };
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await queryRAG(query);

      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/query',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text: query,
            top_k: 3,
            file_id: undefined
          }),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });
}); 