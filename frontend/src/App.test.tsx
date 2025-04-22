import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import App from './App';
import { queryRAG } from './api';
import theme from './theme';

// Mock the API
jest.mock('./api', () => ({
  queryRAG: jest.fn(),
}));

// Mock the toast
const mockToast = jest.fn();
jest.mock('@chakra-ui/react', () => {
  const actual = jest.requireActual('@chakra-ui/react');
  return {
    ...actual,
    useToast: () => mockToast,
  };
});

describe('App Integration', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  it('handles chat interaction and displays response', async () => {
    // Mock the API response
    (queryRAG as jest.Mock).mockResolvedValueOnce({
      answers: ['This is the answer'],
      documents: [
        {
          content: 'Source document 1',
          meta: {},
          id: '1',
          score: 0.8,
        },
      ],
      error: null,
    });

    render(
      <ChakraProvider theme={theme}>
        <App />
      </ChakraProvider>
    );

    // Find and interact with the chat input
    const input = screen.getByPlaceholderText('Type your question...');
    fireEvent.change(input, { target: { value: 'Test question' } });
    
    // Click the Send button instead of pressing Enter
    const sendButton = screen.getByText('Send');
    fireEvent.click(sendButton);

    // Wait for the API call and response
    await waitFor(() => {
      expect(queryRAG).toHaveBeenCalledWith('Test question', 3, undefined);
    });

    // Verify the response is displayed
    expect(await screen.findByText('This is the answer')).toBeInTheDocument();
    expect(screen.getByText('Source document 1')).toBeInTheDocument();
    expect(screen.getByText('Score: 0.800')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    // Mock API error
    (queryRAG as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(
      <ChakraProvider theme={theme}>
        <App />
      </ChakraProvider>
    );

    // Find and interact with the chat input
    const input = screen.getByPlaceholderText('Type your question...');
    fireEvent.change(input, { target: { value: 'Test question' } });
    
    // Click the Send button
    const sendButton = screen.getByText('Send');
    fireEvent.click(sendButton);

    // Wait for the toast to be called
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Error',
          description: 'Failed to get response',
          status: 'error',
        })
      );
    });
  });
}); 