export const theme = {
  colors: {
    primary: '#002f5f', // brand-navy
    secondary: '#fbc12d', // brand-yellow
    background: '#f7f9fc',
    text: '#002f5f',
    white: '#ffffff',
    error: '#dc3545',
    success: '#28a745',
  },
  typography: {
    fontFamily: "'Open Sans', sans-serif",
    fontSize: {
      small: '0.875rem',
      medium: '1rem',
      large: '1.25rem',
      xlarge: '1.5rem',
    },
  },
  spacing: {
    small: '0.5rem',
    medium: '1rem',
    large: '2rem',
  },
  breakpoints: {
    mobile: '320px',
    tablet: '768px',
    desktop: '1024px',
  },
} as const;

export type Theme = typeof theme; 