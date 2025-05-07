import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { EnvStatus } from '../EnvStatus';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the config
vi.mock('../../config', () => ({
  getConfig: () => ({
    apiBaseUrl: 'http://localhost:8000'
  })
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('EnvStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders environment status', async () => {
    const mockSettings = {
      environment: 'development',
      embedding_model: 'all-MiniLM-L6-v2',
      generator_model_name: 'tinyllama:latest'
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSettings)
    });

    render(<EnvStatus />);

    // Initially shows loading state
    expect(screen.getByText('Loading settings...')).toBeInTheDocument();

    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByText('Environment: development')).toBeInTheDocument();
      expect(screen.getByText('Embed Model: all-MiniLM-L6-v2')).toBeInTheDocument();
      expect(screen.getByText('Gen Model: tinyllama:latest')).toBeInTheDocument();
    });
  });
}); 