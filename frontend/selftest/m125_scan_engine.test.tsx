import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ModeProvider } from '../src/hooks/useMode';
import { TimelineProvider } from '../src/hooks/useTimeline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import MainLayout from '../src/layouts/MainLayout';
import Home from '../src/pages/Home';
import ScanCenter from '../src/pages/ScanCenter';

// Mock the API client
vi.mock('../src/api/client', () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: {
        status: 'ok',
        subsystems: { graph: { nodes: 100 } }
      }
    }),
  }
}));

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

function renderWithProviders(initialEntry: string = '/') {
  return render(
    <QueryClientProvider client={queryClient}>
      <ModeProvider>
        <TimelineProvider>
          <MemoryRouter initialEntries={[initialEntry]}>
            <Routes>
              <Route path="/" element={<MainLayout />}>
                <Route path="home" element={<Home />} />
                <Route path="scan-center" element={<ScanCenter />} />
              </Route>
            </Routes>
          </MemoryRouter>
        </TimelineProvider>
      </ModeProvider>
    </QueryClientProvider>
  );
}

describe('M12.5 Scan Engine Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    // Mock global fetch for the scan center API calls
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/scans/network')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: { scan_id: 'mock-scan-123', status: 'queued' } })
        });
      }
      if (url.includes('/api/v1/scans/mock-scan-123/results')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            data: {
              assets_found: 10,
              services_found: 20,
              identities_found: 0,
              datastores_found: 0,
              findings: 5,
              graph_impact: 30
            }
          })
        });
      }
      if (url.includes('/api/v1/scans/mock-scan-123')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            data: {
              scan_id: 'mock-scan-123',
              status: 'COMPLETED',
              progress: 100
            }
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: {} })
      });
    });
  });

  it('navigates to Scan Center and starts a scan', async () => {
    renderWithProviders('/home');
    
    // UI should default to Home in Simple mode
    await waitFor(() => {
      expect(screen.getByText(/Continuous Monitoring/i)).toBeDefined();
    });

    // Go to Scan Center
    const startScanBtn = screen.getByText(/Start Scan/i);
    fireEvent.click(startScanBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/What would you like to discover/i)).toBeDefined();
    });
    
    // Select Network Discovery
    fireEvent.click(screen.getByText(/Network Discovery/i));
    fireEvent.click(screen.getByText(/Continue/i));
    
    // Verify it asks for target
    await waitFor(() => {
      expect(screen.getByText(/Enter Target Information/i)).toBeDefined();
    });
    
    const targetInput = screen.getByRole('textbox');
    fireEvent.change(targetInput, { target: { value: '192.168.1.0/24' } });
    fireEvent.click(screen.getByText(/Continue/i));
    
    // Review and run
    fireEvent.click(screen.getByText(/Run Scan/i));
    
    // Check results
    await waitFor(() => {
      expect(screen.getByText(/Scan Complete/i)).toBeDefined();
    }, { timeout: 3000 });
  });
});
