import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Recommendations from '../src/pages/Recommendations';
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

describe('Milestone 19 - Recommendations UI', () => {
  it('renders correctly and allows filtering', () => {
    vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
      data: {
        data: [
          {
            id: 'rec-001',
            severity: 'CRITICAL',
            category: 'EXPOSURE',
            title: 'Exposed Production Database',
            description: 'A database with sensitive info is exposed to the internet.',
            reason: ['Contains PCI data', 'Exposed port 5432'],
            actions: ['Restrict security groups'],
            affected_nodes: ['db-prod']
          },
          {
            id: 'rec-002',
            severity: 'MEDIUM',
            category: 'IDENTITY',
            title: 'Unused Admin Account',
            description: 'Account admin has not logged in for 90 days.',
            reason: ['Stale credential'],
            actions: ['Disable account'],
            affected_nodes: ['user-admin']
          }
        ]
      },
      isLoading: false,
      error: null
    } as any);

    render(<Wrapper><Recommendations /></Wrapper>);
    
    // Check titles
    expect(screen.getByText('Exposed Production Database')).toBeDefined();
    expect(screen.getByText('Unused Admin Account')).toBeDefined();

    // Check expand/collapse interaction
    fireEvent.click(screen.getByText('Exposed Production Database'));
    expect(screen.getByText('Contains PCI data')).toBeDefined();
    expect(screen.getByText('Restrict security groups')).toBeDefined();

    // Check filtering
    const critBtn = screen.getByText(/Critical Only/);
    fireEvent.click(critBtn);
    
    expect(screen.getByText('Exposed Production Database')).toBeDefined();
    expect(screen.queryByText('Unused Admin Account')).toBeNull();
  });
});
