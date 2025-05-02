import '@testing-library/jest-dom';

// Mock fetch globally
global.fetch = jest.fn();

// Mock Vite environment
Object.defineProperty(global, 'import.meta', {
  value: {
    env: {
      VITE_API_BASE_URL: 'http://localhost:8000',
      DEV: true,
      PROD: false,
    },
  },
  writable: true,
}); 