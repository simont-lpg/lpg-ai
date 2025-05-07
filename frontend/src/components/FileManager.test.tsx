import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileManager } from './FileManager';
import { uploadFiles, watchIngestProgress } from '../api';
import { vi } from 'vitest';

// Mock the API functions
vi.mock('../api', () => ({
  uploadFiles: vi.fn(),
  watchIngestProgress: vi.fn(),
  listFiles: vi.fn().mockResolvedValue([]),
  deleteDocument: vi.fn(),
}));

describe('FileManager', () => {
  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows upload and processing progress in sequence', async () => {
    // Mock uploadFiles to simulate upload progress
    (uploadFiles as any).mockImplementation((
      files: File[],
      namespace: string,
      onProgress: (phase: "upload", pct: number) => void
    ) => {
      onProgress("upload", 0);
      onProgress("upload", 100);
      return Promise.resolve("test-upload-id");
    });

    // Mock watchIngestProgress to simulate processing progress
    (watchIngestProgress as any).mockImplementation((
      uploadId: string,
      onProgress: (phase: "processing", pct: number) => void
    ) => {
      onProgress("processing", 0);
      onProgress("processing", 100);
      return () => {}; // Return cleanup function
    });

    render(<FileManager onFileSelect={mockOnFileSelect} />);

    // Upload a file
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
    const input = screen.getByLabelText(/upload files/i);
    fireEvent.change(input, { target: { files: [file] } });

    // Check upload progress
    await waitFor(() => {
      const progressText = screen.getByTestId('upload-progress-text');
      expect(progressText.textContent?.replace(/\s+/g, ' ').trim()).toBe('Uploading… 100%');
    });

    // Check processing progress
    await waitFor(() => {
      const progressText = screen.getByTestId('upload-progress-text');
      expect(progressText.textContent?.replace(/\s+/g, ' ').trim()).toBe('Processing… 100%');
    });

    // Verify progress bar values
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });
}); 