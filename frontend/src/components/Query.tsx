import { useState } from 'react';
import styled from 'styled-components';
import { query, Document } from '../api/client';

const Container = styled.div`
  padding: ${({ theme }) => theme.spacing.large};
`;

const Header = styled.header`
  margin-bottom: ${({ theme }) => theme.spacing.large};
`;

const Title = styled.h1`
  font-size: ${({ theme }) => theme.typography.fontSize.xlarge};
  color: ${({ theme }) => theme.colors.text};
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.medium};
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 100px;
  padding: ${({ theme }) => theme.spacing.medium};
  border: 1px solid ${({ theme }) => theme.colors.primary};
  border-radius: 4px;
  font-family: ${({ theme }) => theme.typography.fontFamily};
  resize: vertical;
`;

const Button = styled.button`
  padding: ${({ theme }) => theme.spacing.medium};
  background: ${({ theme }) => theme.colors.primary};
  color: ${({ theme }) => theme.colors.white};
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: ${({ theme }) => theme.typography.fontSize.medium};

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const AnswerSection = styled.div`
  margin-top: ${({ theme }) => theme.spacing.large};
`;

const AnswerTitle = styled.h2`
  font-size: ${({ theme }) => theme.typography.fontSize.large};
  color: ${({ theme }) => theme.colors.text};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
`;

const AnswerText = styled.div`
  background: ${({ theme }) => theme.colors.white};
  padding: ${({ theme }) => theme.spacing.large};
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: ${({ theme }) => theme.spacing.large};
`;

const SourcesTitle = styled.h3`
  font-size: ${({ theme }) => theme.typography.fontSize.medium};
  color: ${({ theme }) => theme.colors.text};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
`;

const SourceList = styled.ul`
  list-style: none;
  padding: 0;
`;

const SourceItem = styled.li`
  background: ${({ theme }) => theme.colors.white};
  padding: ${({ theme }) => theme.spacing.medium};
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: ${({ theme }) => theme.spacing.medium};
`;

const ErrorMessage = styled.div`
  color: ${({ theme }) => theme.colors.error};
  margin-top: ${({ theme }) => theme.spacing.medium};
`;

export const Query = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    try {
      const response = await query(question);
      setAnswer(response.answer);
      setSources(response.sources);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get answer');
      setAnswer('');
      setSources([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container>
      <Header>
        <Title>Ask a Question</Title>
      </Header>
      <Form onSubmit={handleSubmit}>
        <TextArea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question here..."
          disabled={isLoading}
        />
        <Button type="submit" disabled={isLoading || !question.trim()}>
          {isLoading ? 'Getting answer...' : 'Get Answer'}
        </Button>
      </Form>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {answer && (
        <AnswerSection>
          <AnswerTitle>Answer</AnswerTitle>
          <AnswerText>{answer}</AnswerText>
          {sources.length > 0 && (
            <>
              <SourcesTitle>Sources</SourcesTitle>
              <SourceList>
                {sources.map((source, index) => (
                  <SourceItem key={index}>
                    {source.content.substring(0, 200)}...
                  </SourceItem>
                ))}
              </SourceList>
            </>
          )}
        </AnswerSection>
      )}
    </Container>
  );
}; 