import { useState } from 'react';
import styled from 'styled-components';
import { ingestDocument } from '../api/client';

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

const UploadContainer = styled.div`
  border: 2px dashed ${({ theme }) => theme.colors.primary};
  border-radius: 4px;
  padding: ${({ theme }) => theme.spacing.large};
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${({ theme }) => theme.colors.background};
  }
`;

const FileInput = styled.input`
  display: none;
`;

const UploadText = styled.p`
  color: ${({ theme }) => theme.colors.text};
  margin-bottom: ${({ theme }) => theme.spacing.medium};
`;

const ErrorMessage = styled.div`
  color: ${({ theme }) => theme.colors.error};
  margin-top: ${({ theme }) => theme.spacing.medium};
`;

const SuccessMessage = styled.div`
  color: ${({ theme }) => theme.colors.success};
  margin-top: ${({ theme }) => theme.spacing.medium};
`;

export const Ingest = () => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      setSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setIsLoading(true);
    try {
      const response = await ingestDocument(file);
      setSuccess(`Successfully ingested ${response.files_ingested} file(s) with ${response.total_chunks} chunks`);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to ingest document');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container>
      <Header>
        <Title>Ingest Documents</Title>
      </Header>
      <UploadContainer onClick={() => document.getElementById('file-input')?.click()}>
        <FileInput
          id="file-input"
          type="file"
          onChange={handleFileChange}
          accept=".txt,.pdf,.doc,.docx"
        />
        <UploadText>
          {file ? file.name : 'Click to select a file or drag and drop'}
        </UploadText>
        {file && (
          <button onClick={handleUpload} disabled={isLoading}>
            {isLoading ? 'Uploading...' : 'Upload'}
          </button>
        )}
      </UploadContainer>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {success && <SuccessMessage>{success}</SuccessMessage>}
    </Container>
  );
}; 