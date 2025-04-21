import { UseToastOptions } from '@chakra-ui/react';

export const createMockToast = () => {
  const mockToast = jest.fn((options?: UseToastOptions) => Math.random());
  mockToast.close = jest.fn();
  mockToast.closeAll = jest.fn();
  mockToast.update = jest.fn();
  mockToast.isActive = jest.fn();
  mockToast.promise = jest.fn();

  return mockToast;
}; 