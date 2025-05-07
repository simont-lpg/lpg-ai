import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect method with methods from react-testing-library
expect.extend(matchers);

// Cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup();
});

// Mock fetch globally
global.fetch = vi.fn();

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