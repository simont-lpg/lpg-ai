import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

export function renderWithProviders(ui: React.ReactElement) {
  return render(ui);
}

export { screen } from '@testing-library/react'; 