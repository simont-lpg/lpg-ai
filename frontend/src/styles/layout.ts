import styled from 'styled-components';

export const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  width: 100%;
  font-family: 'Open Sans', sans-serif;
`;

export const Sidebar = styled.aside`
  width: fit-content;
  min-width: 250px;
  background-color: #0B1B4D;
  flex-shrink: 0;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  padding: 1.5rem;
  color: white;
  display: flex;
  flex-direction: column;
`;

export const MainContent = styled.main`
  flex: 1;
  display: flex;
  margin-left: fit-content;
  min-width: 250px;
  height: 100vh;
  background: white;
`;

export const WorkArea = styled.section`
  flex: 1;
  padding: 1.5rem;
  background: white;
  overflow-y: auto;
`;

export const DetailPanel = styled.aside`
  width: 300px;
  background: #F8F9FA;
  padding: 1.5rem;
  border-left: 1px solid #E5E7EB;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
`;

export const DetailPanelHeader = styled.header`
  font-size: 1.25rem;
  font-weight: 600;
  padding: 1rem 0;
  color: #1F2937;
`;

export const DetailPanelContent = styled.div`
  flex: 1;
  overflow-y: auto;
`;

export const LogoContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  padding: 0.5rem;
`;

export const UploadButton = styled.button`
  background-color: #EEC966;
  color: #1F2937;
  border: none;
  border-radius: 6px;
  padding: 0.75rem;
  width: 100%;
  font-weight: 600;
  margin-bottom: 1.5rem;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #E5B94C;
  }
`;

export const DocumentList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
`;

export const DocumentListItem = styled.li<{ selected?: boolean }>`
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
  border-left: ${props => props.selected ? '3px solid #EEC966' : 'none'};
  transition: background-color 0.2s;

  &:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
`;

export const PageTitle = styled.h1`
  font-size: 1.5rem;
  font-weight: 700;
  padding-top: 2rem;
  margin-bottom: 2rem;
  color: #1F2937;
`;

export const QueryInput = styled.textarea`
  width: 100%;
  border: 2px solid #0B1B4D;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 100px;
`;

export const RunButton = styled.button`
  background-color: #EEC966;
  color: #1F2937;
  border: none;
  border-radius: 6px;
  padding: 0.75rem;
  width: 100%;
  font-weight: 600;
  margin-bottom: 2rem;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #E5B94C;
  }
`;

export const AnswerCard = styled.div`
  background: white;
  padding: 1rem;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 1rem;
`;

export const AnswerCardHeader = styled.div`
  height: 10px;
  background-color: #EEC966;
  margin-bottom: 1rem;
`;

export const ContextMapPlaceholder = styled.div`
  width: 200px;
  height: 150px;
  border: 1px solid #E5E7EB;
  margin-top: auto;
  align-self: center;
`; 