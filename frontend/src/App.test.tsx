import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import App from './App';
import { queryRAG } from './api';
import theme from './theme';
import { vi, describe, it, expect } from 'vitest';

// Mock the API
vi.mock('./api', () => ({
  queryRAG: vi.fn(),
}));

// Mock the config
vi.mock('./config', () => ({
  getConfig: () => ({ apiBaseUrl: "http://test-server" }),
}));

// Mock Chakra UI
const mockToast = vi.fn();
vi.mock('@chakra-ui/react', async () => {
  const actual = await vi.importActual('@chakra-ui/react');
  return {
    ...actual,
    ChakraProvider: ({ children }: { children: React.ReactNode }) => children,
    useColorModeValue: vi.fn().mockImplementation((light, dark) => light),
    useToast: () => mockToast
  };
});

// Mock fetch globally
global.fetch = vi.fn().mockImplementation(() => 
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      environment: "development",
      embedding_model: "MiniLM",
      generator_model: "tinyllama:latest",
    })
  })
);

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />);
    expect(screen.getByAltText('LPG Logo')).toBeInTheDocument();
  });
});

describe('App Integration', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    
    // Mock the settings response
    (global.fetch as any).mockResolvedValueOnce({
      json: async () => ({
        environment: "development",
        embedding_model: "MiniLM",
        generator_model: "tinyllama:latest",
      }),
    });
  });

  it('handles chat interaction and displays response', async () => {
    // Mock the API response
    (queryRAG as any).mockResolvedValueOnce({
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
    (queryRAG as any).mockRejectedValueOnce(new Error('API Error'));

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