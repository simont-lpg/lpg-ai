import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { FileManager } from '../FileManager';
import * as api from '../../api';
import { uploadFiles, watchIngestProgress } from '../../api';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import userEvent from '@testing-library/user-event';

// Increase test timeout
vi.setConfig({ testTimeout: 10000 });

// Mock the API functions
vi.mock('../../api', () => ({
  listFiles: vi.fn(),
  deleteDocument: vi.fn(),
  uploadFiles: vi.fn(),
  watchIngestProgress: vi.fn(),
}));

// Mock EventSource
const mockEventSource = {
  onmessage: null as ((event: { data: string }) => void) | null,
  onerror: null as (() => void) | null,
  close: vi.fn(),
};

vi.stubGlobal('EventSource', vi.fn().mockImplementation(() => mockEventSource));

// Mock DataTransfer
class MockDataTransfer {
  items: DataTransferItemList;
  files: FileList;

  constructor() {
    this.items = {
      add: vi.fn(),
      remove: vi.fn(),
      clear: vi.fn(),
      length: 0,
      [Symbol.iterator]: function* () {},
    } as unknown as DataTransferItemList;

    this.files = {
      length: 0,
      item: vi.fn(),
      [Symbol.iterator]: function* () {},
    } as unknown as FileList;
  }
}

vi.stubGlobal('DataTransfer', MockDataTransfer);

// Mock toast function
const mockToast = vi.fn();

// Mock Chakra UI
vi.mock('@chakra-ui/react', async () => {
  const actual = await vi.importActual('@chakra-ui/react');
  return {
    ...actual,
    useColorModeValue: vi.fn().mockImplementation((light, dark) => light),
    useToast: () => mockToast
  };
});

describe('FileManager', () => {
  const mockFiles = [
    { filename: 'test1.pdf', id: '1', namespace: 'default', document_count: 1, file_size: 1024 },
    { filename: 'test2.pdf', id: '2', namespace: 'default', document_count: 1, file_size: 2048 },
  ];

  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (api.listFiles as any).mockResolvedValue(mockFiles);
    (api.deleteDocument as any).mockResolvedValue(undefined);
    (api.uploadFiles as any).mockResolvedValue("test-upload-id");
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders and fetches files on mount', async () => {
    render(<FileManager onFileSelect={mockOnFileSelect} />);
    
    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });

    mockFiles.forEach((file) => {
      expect(screen.getByText(file.filename)).toBeInTheDocument();
      expect(screen.getByText('1 KB')).toBeInTheDocument();
      expect(screen.getByText('2 KB')).toBeInTheDocument();
    });
  });

  it('handles file selection', async () => {
    render(<FileManager onFileSelect={mockOnFileSelect} />);

    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByText('test1.pdf'));
    expect(mockOnFileSelect).toHaveBeenCalledWith('1');
  });

  it('handles file deletion', async () => {
    render(<FileManager onFileSelect={mockOnFileSelect} />);

    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(api.deleteDocument).toHaveBeenCalledWith('test1.pdf');
      expect(api.listFiles).toHaveBeenCalledTimes(2); // Initial load + after delete
    });
  });

  const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

  it('handles file upload with progress tracking', async () => {
    const mockFile = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    // Mock uploadFiles to emit upload progress
    (uploadFiles as jest.Mock).mockImplementation(async (files, _, onProgress) => {
      onProgress('upload', 100);
      return 'test-upload-id';
    });

    // Mock watchIngestProgress to emit processing progress
    (watchIngestProgress as jest.Mock).mockImplementation((_, onProgress) => {
      onProgress('processing', 100);
      return () => {};
    });

    render(<FileManager onFileSelect={mockOnFileSelect} />);

    const fileInput = screen.getByLabelText(/upload files/i);
    
    // Upload the file
    await act(async () => {
      fireEvent.change(fileInput, { target: { files: [mockFile] } });
      // Wait for all state updates
      await Promise.resolve();
    });

    // Wait for processing phase to complete
    await waitFor(() => {
      const progressText = screen.getByTestId('upload-progress-text');
      expect(progressText).toHaveTextContent('Processing… 100%');
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');
    });

    // Verify API calls
    expect(uploadFiles).toHaveBeenCalledWith(expect.any(Array), 'default', expect.any(Function));
    expect(watchIngestProgress).toHaveBeenCalledWith('test-upload-id', expect.any(Function));
  });

  it('handles API errors gracefully', async () => {
    (api.listFiles as any).mockRejectedValue(new Error('API Error'));
    render(<FileManager onFileSelect={mockOnFileSelect} />);

    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });
  });

  it('handles upload errors gracefully', async () => {
    // Mock uploadFiles to simulate an error
    (uploadFiles as any).mockRejectedValue(new Error('Upload failed'));

    render(<FileManager onFileSelect={mockOnFileSelect} />);

    // Create a file and trigger upload
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const fileList = {
      length: 1,
      item: (index: number) => file,
      [Symbol.iterator]: function* () {
        yield file;
      }
    } as unknown as FileList;

    const input = screen.getByLabelText('Upload Files');
    fireEvent.change(input, { target: { files: fileList } });

    // Wait for error toast
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'Upload failed',
          status: 'error'
        })
      );
    });

    // Verify progress bar is hidden
    expect(screen.queryByTestId('progress-container')).not.toBeInTheDocument();
  });

  it('validates file types', async () => {
    const mockInvalidFile = new File(['test content'], 'test.exe', { type: 'application/exe' });
    
    render(<FileManager onFileSelect={mockOnFileSelect} />);

    const fileInput = screen.getByLabelText('Upload Files');
    Object.defineProperty(fileInput, 'files', {
      value: [mockInvalidFile],
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Invalid file type',
          description: expect.stringContaining('test.exe'),
          status: 'error'
        })
      );
    });
  });
}); 