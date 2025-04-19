import styled from 'styled-components';
import { Link, useLocation } from 'react-router-dom';

const SidebarContainer = styled.aside`
  width: 240px;
  background: ${({ theme }) => theme.colors.primary};
  padding: ${({ theme }) => theme.spacing.medium};
  display: flex;
  flex-direction: column;
`;

const Logo = styled.img`
  width: 100%;
  margin-bottom: ${({ theme }) => theme.spacing.large};
`;

const Nav = styled.nav`
  flex: 1;
`;

const NavList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const NavItem = styled.li`
  margin-bottom: ${({ theme }) => theme.spacing.medium};
`;

const NavLink = styled(Link)<{ $isActive: boolean }>`
  color: ${({ theme }) => theme.colors.white};
  text-decoration: none;
  font-size: ${({ theme }) => theme.typography.fontSize.medium};
  font-weight: ${({ $isActive }) => ($isActive ? 'bold' : 'normal')};
  display: block;
  padding: ${({ theme }) => theme.spacing.small} 0;
  
  &:hover {
    opacity: 0.8;
  }
`;

export const Sidebar = () => {
  const location = useLocation();

  return (
    <SidebarContainer>
      <Logo
        src="https://learnprogroup.com/wp-content/uploads/2024/09/LPG-Full-White.svg"
        alt="LearnPro Group logo"
      />
      <Nav>
        <NavList>
          <NavItem>
            <NavLink
              to="/ingest"
              $isActive={location.pathname === '/ingest'}
            >
              Ingest
            </NavLink>
          </NavItem>
          <NavItem>
            <NavLink
              to="/documents"
              $isActive={location.pathname === '/documents'}
            >
              Documents
            </NavLink>
          </NavItem>
          <NavItem>
            <NavLink
              to="/query"
              $isActive={location.pathname === '/query'}
            >
              Query
            </NavLink>
          </NavItem>
        </NavList>
      </Nav>
    </SidebarContainer>
  );
}; 