import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { DocumentExplorer } from './components/DocumentExplorer';
import { DocumentPreview } from './components/DocumentPreview';
import {
  AppContainer,
  MainContent,
  WorkArea,
  DetailPanel,
} from './styles/layout';

function App() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  return (
    <Router>
      <AppContainer>
        <Sidebar onSelectDoc={setSelectedDocId} />
        <MainContent>
          <WorkArea>
            <Routes>
              <Route path="/documents" element={<DocumentExplorer />} />
              <Route path="/query" element={<DocumentExplorer />} />
              <Route path="/" element={<DocumentExplorer />} />
            </Routes>
          </WorkArea>
          <DetailPanel>
            <DocumentPreview selectedDocId={selectedDocId} />
          </DetailPanel>
        </MainContent>
      </AppContainer>
    </Router>
  );
}

export default App; 