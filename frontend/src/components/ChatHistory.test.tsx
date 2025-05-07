import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChatHistory } from './ChatHistory';
import { QueryResponse } from '../api';
import { vi, describe, it, expect } from 'vitest';

// Mock Chakra UI
vi.mock('@chakra-ui/react', async () => {
  const actual = await vi.importActual('@chakra-ui/react');
  return {
    ...actual,
    useColorModeValue: vi.fn().mockImplementation((light, dark) => light)
  };
});

describe('ChatHistory', () => {
  it('renders user and assistant messages with answers and documents', () => {
    const messages = [
      {
        type: 'user' as const,
        content: 'What is React?'
      },
      {
        type: 'assistant' as const,
        content: 'React is a JavaScript library.',
        documents: [
          {
            content: 'React makes it painless to create interactive UIs.',
            meta: { source: 'docs' },
            id: '1',
            score: 0.95
          }
        ]
      }
    ];

    render(<ChatHistory messages={messages} />);

    // Check user message
    expect(screen.getByText('You:')).toBeInTheDocument();
    expect(screen.getByText('What is React?')).toBeInTheDocument();

    // Check assistant message
    expect(screen.getByText('Assistant:')).toBeInTheDocument();
    expect(screen.getByText('React is a JavaScript library.')).toBeInTheDocument();

    // Check document
    expect(screen.getByText('React makes it painless to create interactive UIs.')).toBeInTheDocument();
    expect(screen.getByText('Sources:')).toBeInTheDocument();
    expect(screen.getByText('Score: 0.950')).toBeInTheDocument();
  });

  it('renders empty state when no messages', () => {
    render(<ChatHistory messages={[]} />);
    const container = screen.getByTestId('chat-history');
    expect(container).toBeEmptyDOMElement();
  });

  it('shows "No answer available" when answer is empty', () => {
    const messages = [
      {
        type: 'user' as const,
        content: 'What is React?'
      },
      {
        type: 'assistant' as const,
        content: '',
        documents: []
      }
    ];

    render(<ChatHistory messages={messages} />);
    expect(screen.getByText('No answer available')).toBeInTheDocument();
  });

  it('renders answer in a styled bubble', () => {
    const messages = [
      {
        type: 'assistant' as const,
        content: 'Test answer',
        documents: []
      }
    ];

    render(<ChatHistory messages={messages} />);
    const answerBubble = screen.getByTestId('answer-bubble');
    expect(answerBubble).toBeInTheDocument();
    expect(answerBubble).toHaveTextContent('Test answer');
  });
}); 