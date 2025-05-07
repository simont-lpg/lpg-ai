import { UseToastOptions } from '@chakra-ui/react';
import { vi } from 'vitest';

interface MockToast {
  (options?: UseToastOptions): number;
  close: () => void;
  closeAll: () => void;
  update: () => void;
  isActive: () => boolean;
  promise: () => Promise<any>;
}

const mockToast = Object.assign(
  vi.fn((options?: UseToastOptions) => Math.random()),
  {
    close: vi.fn(),
    closeAll: vi.fn(),
    update: vi.fn(),
    isActive: vi.fn(),
    promise: vi.fn()
  }
) as MockToast;

export { mockToast }; 