import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileManager } from '../FileManager';
import * as api from '../../api';

// Mock the API functions
jest.mock('../../api', () => ({
  listFiles: jest.fn(),
  deleteDocument: jest.fn(),
  uploadFiles: jest.fn(),
}));

// Mock Chakra UI toast
jest.mock('@chakra-ui/react', () => ({
  ...jest.requireActual('@chakra-ui/react'),
  useToast: () => jest.fn(),
}));

describe('FileManager', () => {
  const mockFiles = [
    { id: '1', name: 'test1.pdf' },
    { id: '2', name: 'test2.pdf' },
  ];

  beforeEach(() => {
    (api.listFiles as jest.Mock).mockResolvedValue(mockFiles);
    (api.deleteDocument as jest.Mock).mockResolvedValue(undefined);
    (api.uploadFiles as jest.Mock).mockResolvedValue(undefined);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders and fetches files on mount', async () => {
    render(<FileManager onFileSelect={jest.fn()} />);
    
    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });

    mockFiles.forEach((file) => {
      expect(screen.getByText(file.name)).toBeInTheDocument();
    });
  });

  it('handles file selection', async () => {
    const onFileSelect = jest.fn();
    render(<FileManager onFileSelect={onFileSelect} />);

    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByText('test1.pdf'));
    expect(onFileSelect).toHaveBeenCalledWith('1');
  });

  it('handles file deletion', async () => {
    render(<FileManager onFileSelect={jest.fn()} />);

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

  it('handles file upload', async () => {
    render(<FileManager onFileSelect={jest.fn()} />);

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/upload files/i);
    
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(api.uploadFiles).toHaveBeenCalled();
      expect(api.listFiles).toHaveBeenCalledTimes(2); // Initial load + after upload
    });
  });

  it('handles API errors gracefully', async () => {
    (api.listFiles as jest.Mock).mockRejectedValue(new Error('API Error'));
    render(<FileManager onFileSelect={jest.fn()} />);

    await waitFor(() => {
      expect(api.listFiles).toHaveBeenCalled();
    });
  });
}); 