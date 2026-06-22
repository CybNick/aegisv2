import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Compliance from '../src/pages/Compliance';
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

describe('Milestone 20 - Compliance UI', () => {
  it('renders framework data correctly', () => {
    vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
      data: {
        data: {
          overall_score: 82,
          frameworks: {
            "PCI DSS": {
              score: 50,
              passed_controls: [],
              failed_controls: [
                {
                  control: { id: "1.2", title: "Restrict connections to untrusted networks", description: "Firewall config" },
                  reason: "Failed due to CRITICAL risk: Exposed Database",
                  evidence_nodes: ["db-prod"]
                }
              ]
            }
          }
        }
      },
      isLoading: false,
      error: null
    } as any);

    render(<Wrapper><Compliance /></Wrapper>);
    
    // Check overall score
    expect(screen.getByText('82%')).toBeDefined();
    expect(screen.getByText('PCI DSS')).toBeDefined();
    
    // Expand framework
    fireEvent.click(screen.getByText('PCI DSS'));
    
    // Check failed control details
    expect(screen.getByText('1.2')).toBeDefined();
    expect(screen.getByText('Restrict connections to untrusted networks')).toBeDefined();
    expect(screen.getByText('Failed due to CRITICAL risk: Exposed Database')).toBeDefined();
    expect(screen.getByText('Nodes: db-prod')).toBeDefined();
  });
});
