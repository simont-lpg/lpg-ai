import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Chat } from '../Chat';
import * as api from '../../api';

// Mock the API functions
jest.mock('../../api', () => ({
  queryRAG: jest.fn(),
}));

// Mock Chakra UI toast
jest.mock('@chakra-ui/react', () => ({
  ...jest.requireActual('@chakra-ui/react'),
  useToast: () => jest.fn(),
}));

describe('Chat', () => {
  const mockResponse = {
    answers: ['Test answer'],
    documents: [
      {
        content: 'Source content',
        meta: { source: 'test.pdf' },
        id: '1',
        score: 0.8
      },
    ],
  };

  beforeEach(() => {
    (api.queryRAG as jest.Mock).mockResolvedValue(mockResponse);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders and handles user input', async () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText(/type your question/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    // Test input validation
    expect(sendButton).toBeDisabled();
    fireEvent.change(input, { target: { value: 'test question' } });
    expect(sendButton).not.toBeDisabled();

    // Test sending message
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.queryRAG).toHaveBeenCalledWith('test question', 3, undefined);
    });

    // Verify messages are displayed
    expect(screen.getByText('test question')).toBeInTheDocument();
    expect(screen.getByText('Test answer')).toBeInTheDocument();
    expect(screen.getByText('Source content')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (api.queryRAG as jest.Mock).mockRejectedValue(new Error('API Error'));
    render(<Chat />);

    const input = screen.getByPlaceholderText(/type your question/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.queryRAG).toHaveBeenCalled();
    });
  });

  it('handles file context', async () => {
    const selectedFileId = 'test-file-id';
    render(<Chat selectedFileId={selectedFileId} />);

    const input = screen.getByPlaceholderText(/type your question/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: 'test question' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(api.queryRAG).toHaveBeenCalledWith(
        'test question',
        3,
        selectedFileId
      );
    });
  });

  it('handles empty input', () => {
    render(<Chat />);

    const input = screen.getByPlaceholderText(/type your question/i);
    const sendButton = screen.getByRole('button', { name: /send/i });

    fireEvent.change(input, { target: { value: '   ' } });
    expect(sendButton).toBeDisabled();
  });
}); 