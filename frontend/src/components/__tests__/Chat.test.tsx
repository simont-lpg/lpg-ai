import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Chat } from '../Chat';
import { queryRAG } from '../../api';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the API functions
vi.mock('../../api', () => ({
  queryRAG: vi.fn(),
}));

// Mock Chakra UI toast
const mockToast = vi.fn();
vi.mock('@chakra-ui/react', async () => {
  const actual = await vi.importActual('@chakra-ui/react');
  return {
    ...actual,
    useToast: () => mockToast,
  };
});

describe('Chat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat input and handles submission', async () => {
    const mockQueryResponse = {
      answers: ['Test answer'],
      documents: [
        {
          content: 'Test document',
          meta: {},
          id: '1',
          score: 0.8,
        },
      ],
    };

    (queryRAG as any).mockResolvedValueOnce(mockQueryResponse);

    render(<Chat selectedFileId="1" />);

    const input = screen.getByPlaceholderText('Type your question...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Test answer')).toBeInTheDocument();
      expect(screen.getByText('Test document')).toBeInTheDocument();
    });

    expect(queryRAG).toHaveBeenCalledWith('Test question', 3, '1');
  });

  it('handles API errors', async () => {
    (queryRAG as any).mockRejectedValueOnce(new Error('API Error'));

    render(<Chat selectedFileId="1" />);

    const input = screen.getByPlaceholderText('Type your question...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'Failed to get response',
          status: 'error',
          duration: 3000,
          isClosable: true
        })
      );
    });
  });

  it('handles file context', async () => {
    const selectedFileId = 'test-file-id';
    const mockQueryResponse = {
      answers: ['Test answer'],
      documents: [],
    };

    (queryRAG as any).mockResolvedValueOnce(mockQueryResponse);

    render(<Chat selectedFileId={selectedFileId} />);

    const input = screen.getByPlaceholderText('Type your question...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(queryRAG).toHaveBeenCalledWith(
        'test question',
        3,
        selectedFileId
      );
    });
  });

  it('handles empty input', () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText('Type your question...');
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: '   ' } });
    expect(sendButton).toBeDisabled();
  });
}); 