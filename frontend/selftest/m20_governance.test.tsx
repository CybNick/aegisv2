import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Governance from '../src/pages/Governance';
import * as apiHooks from '../src/api/hooks';

vi.mock('../src/api/hooks', () => ({
  useAegisQuery: vi.fn(),
}));

const queryClient = new QueryClient();

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe('Milestone 20 - Governance UI', () => {
  it('renders governance findings correctly', () => {
    vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
      data: {
        data: {
          findings: [
            {
              id: "gov-own-1234",
              title: "Unowned Asset Detected",
              severity: "HIGH",
              action: "Assign Technical or Team Owner",
              target_id: "server-prod-01",
              target_name: "Production Server",
              category: "OWNERSHIP_GAP"
            }
          ]
        }
      },
      isLoading: false,
      error: null
    } as any);

    render(<Wrapper><Governance /></Wrapper>);
    
    // Check total count
    expect(screen.getByText('1')).toBeDefined();
    
    // Check finding details
    expect(screen.getByText('Unowned Asset Detected')).toBeDefined();
    expect(screen.getByText('OWNERSHIP_GAP')).toBeDefined();
    expect(screen.getByText('Assign Technical or Team Owner')).toBeDefined();
    expect(screen.getByText('Production Server')).toBeDefined();
  });
});
