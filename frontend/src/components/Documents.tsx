import { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Document, getDocuments, deleteDocument } from '../api/client';

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

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-top: ${({ theme }) => theme.spacing.medium};
`;

const Th = styled.th`
  text-align: left;
  padding: ${({ theme }) => theme.spacing.medium};
  border-bottom: 2px solid ${({ theme }) => theme.colors.primary};
`;

const Td = styled.td`
  padding: ${({ theme }) => theme.spacing.medium};
  border-bottom: 1px solid ${({ theme }) => theme.colors.primary};
`;

const DeleteButton = styled.button`
  color: ${({ theme }) => theme.colors.error};
  background: none;
  border: none;
  cursor: pointer;
  padding: ${({ theme }) => theme.spacing.small};

  &:hover {
    text-decoration: underline;
  }
`;

const ErrorMessage = styled.div`
  color: ${({ theme }) => theme.colors.error};
  margin-top: ${({ theme }) => theme.spacing.medium};
`;

const LoadingMessage = styled.div`
  color: ${({ theme }) => theme.colors.text};
  margin-top: ${({ theme }) => theme.spacing.medium};
`;

export const Documents = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch documents');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteDocument(id);
      setDocuments(documents.filter(doc => doc.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  if (isLoading) {
    return (
      <Container>
        <Header>
          <Title>Documents</Title>
        </Header>
        <LoadingMessage>Loading documents...</LoadingMessage>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <Title>Documents</Title>
      </Header>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <Table>
        <thead>
          <tr>
            <Th>ID</Th>
            <Th>Content Preview</Th>
            <Th>Namespace</Th>
            <Th>Actions</Th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <Td>{doc.id}</Td>
              <Td>{doc.content.substring(0, 100)}...</Td>
              <Td>{doc.meta.namespace || '-'}</Td>
              <Td>
                <DeleteButton onClick={() => handleDelete(doc.id)}>
                  Delete
                </DeleteButton>
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
}; 