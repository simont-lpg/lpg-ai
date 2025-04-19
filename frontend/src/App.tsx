import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import styled from 'styled-components';
import { Sidebar } from './components/Sidebar';
import { Ingest } from './components/Ingest';
import { Documents } from './components/Documents';
import { Query } from './components/Query';

const AppContainer = styled.div`
  display: flex;
  height: 100vh;
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: ${({ theme }) => theme.colors.background};
`;

function App() {
  return (
    <Router>
      <AppContainer>
        <Sidebar />
        <MainContent>
          <Routes>
            <Route path="/ingest" element={<Ingest />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/query" element={<Query />} />
            <Route path="/" element={<Ingest />} />
          </Routes>
        </MainContent>
      </AppContainer>
    </Router>
  );
}

export default App; 