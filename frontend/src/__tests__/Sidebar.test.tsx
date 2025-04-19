import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { theme } from '../styles/theme';
import { Sidebar } from '../components/Sidebar';

const renderWithProviders = (component: React.ReactNode, initialEntries = ['/']) => {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={initialEntries}>
        {component}
      </MemoryRouter>
    </ThemeProvider>
  );
};

describe('Sidebar', () => {
  it('renders the logo and navigation links', () => {
    renderWithProviders(<Sidebar />);

    // Check if logo is rendered
    const logo = screen.getByAltText('LearnPro Group logo');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('src', 'https://learnprogroup.com/wp-content/uploads/2024/09/LPG-Full-White.svg');

    // Check if navigation links are rendered
    expect(screen.getByText('Ingest')).toBeInTheDocument();
    expect(screen.getByText('Documents')).toBeInTheDocument();
    expect(screen.getByText('Query')).toBeInTheDocument();
  });

  it('highlights the active route', () => {
    renderWithProviders(<Sidebar />, ['/ingest']);

    // The Ingest link should be active
    const ingestLink = screen.getByText('Ingest').closest('a');
    expect(ingestLink).toHaveStyle({ fontWeight: 'bold' });

    // Other links should not be active
    const documentsLink = screen.getByText('Documents').closest('a');
    const queryLink = screen.getByText('Query').closest('a');
    expect(documentsLink).toHaveStyle({ fontWeight: 'normal' });
    expect(queryLink).toHaveStyle({ fontWeight: 'normal' });
  });
}); 