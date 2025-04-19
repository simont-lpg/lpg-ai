import { useState, useEffect, useRef } from 'react';
import { LogoContainer, UploadButton, DocumentList, DocumentListItem } from '../styles/layout';
import logo from '../assets/LPG-Full-White.svg';

interface Document {
  id: string;
  name: string;
}

interface SidebarProps {
  onSelectDoc: (docId: string) => void;
}

export const Sidebar = ({ onSelectDoc }: SidebarProps) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch('/documents');
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await fetch('/ingest', {
        method: 'POST',
        body: formData,
      });
      fetchDocuments();
    } catch (error) {
      console.error('Error uploading file:', error);
    }
  };

  const handleDocSelect = (docId: string) => {
    setSelectedDocId(docId);
    onSelectDoc(docId);
  };

  return (
    <aside>
      <LogoContainer>
        <img 
          src={logo} 
          alt="LearnPro Group" 
          style={{ 
            width: '180px', 
            height: '40px',
            objectFit: 'contain'
          }} 
        />
      </LogoContainer>
      
      <UploadButton onClick={() => fileInputRef.current?.click()}>
        Upload
      </UploadButton>

      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileUpload}
        data-testid="file-input"
      />

      <DocumentList>
        {documents.map((doc) => (
          <DocumentListItem
            key={doc.id}
            selected={doc.id === selectedDocId}
            onClick={() => handleDocSelect(doc.id)}
          >
            {doc.name}
          </DocumentListItem>
        ))}
      </DocumentList>
    </aside>
  );
}; 