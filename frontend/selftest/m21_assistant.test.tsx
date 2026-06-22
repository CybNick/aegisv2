import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Assistant from '../src/pages/Assistant';

const queryClient = new QueryClient();

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe('Milestone 21 - AI Assistant UI', () => {
  it('renders chat interface and suggestions', () => {
    render(<Wrapper><Assistant /></Wrapper>);
    
    expect(screen.getByText('Aegis Intelligence')).toBeDefined();
    expect(screen.getByText('What changed today?')).toBeDefined();
    expect(screen.getByText('Show exposed assets')).toBeDefined();
  });

  it('can submit a prompt', async () => {
    // Mock fetch
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({
        data: {
          response: {
            title: "Exposure & Risk Intelligence",
            findings: [
              {
                title: "Exposed Production Database",
                severity: "CRITICAL",
                evidence: "Internet -> Load Balancer -> Database",
                action: "Remove public accessibility",
                affected_assets: ["db-prod"]
              }
            ],
            confidence: 1.0
          }
        }
      })
    });

    render(<Wrapper><Assistant /></Wrapper>);
    
    const input = screen.getByPlaceholderText('Ask Aegis...');
    fireEvent.change(input, { target: { value: 'Show public databases' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(screen.getByText('Show public databases')).toBeDefined();
      expect(screen.getByText('Exposure & Risk Intelligence')).toBeDefined();
      expect(screen.getByText('Exposed Production Database')).toBeDefined();
      expect(screen.getByText('Internet -> Load Balancer -> Database')).toBeDefined();
    });
  });
});
