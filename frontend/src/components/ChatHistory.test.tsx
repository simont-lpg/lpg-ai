import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChatHistory } from './ChatHistory';
import { QueryResponse } from '../api';

describe('ChatHistory', () => {
  it('renders user and assistant messages with answers and documents', () => {
    const messages = [
      {
        type: 'user' as const,
        content: 'Hello',
      },
      {
        type: 'assistant' as const,
        content: 'Hi there!',
        documents: [
          {
            content: 'Document 1',
            meta: {},
            id: '1',
            score: 0.8,
          },
          {
            content: 'Document 2',
            meta: {},
            id: '2',
            score: 0.6,
          },
        ] as QueryResponse['documents'],
      },
    ];

    render(<ChatHistory messages={messages} />);

    // Check user message
    expect(screen.getByText('You:')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();

    // Check assistant message
    expect(screen.getByText('Assistant:')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();

    // Check documents
    expect(screen.getByText('Sources:')).toBeInTheDocument();
    expect(screen.getByText('Document 1')).toBeInTheDocument();
    expect(screen.getByText('Document 2')).toBeInTheDocument();
    expect(screen.getByText('Score: 0.800')).toBeInTheDocument();
    expect(screen.getByText('Score: 0.600')).toBeInTheDocument();
  });

  it('shows "No answer available" when answer is empty', () => {
    const messages = [
      {
        type: 'assistant' as const,
        content: '',
        documents: [],
      },
    ];

    render(<ChatHistory messages={messages} />);
    expect(screen.getByText('No answer available')).toBeInTheDocument();
  });

  it('renders answer in a styled bubble', () => {
    const messages = [
      {
        type: 'assistant' as const,
        content: 'This is a test answer',
        documents: [],
      },
    ];

    render(<ChatHistory messages={messages} />);
    const answerBubble = screen.getByText('This is a test answer').closest('div');
    expect(answerBubble).toHaveAttribute('data-testid', 'answer-bubble');
  });
}); 