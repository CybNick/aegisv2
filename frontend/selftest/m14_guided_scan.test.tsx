import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ModeProvider } from '../src/hooks/useMode';
import { TimelineProvider } from '../src/hooks/useTimeline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import ScanCenter from '../src/pages/ScanCenter';
import Home from '../src/pages/Home';
import ScanResults from '../src/pages/ScanResults';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

function renderWithProviders(initialEntry: string) {
  return render(
    <QueryClientProvider client={queryClient}>
      <ModeProvider>
        <TimelineProvider>
          <MemoryRouter initialEntries={[initialEntry]}>
            <Routes>
              <Route path="/home" element={<Home />} />
              <Route path="/scan-center" element={<ScanCenter />} />
              <Route path="/scan-results/:id" element={<ScanResults />} />
            </Routes>
          </MemoryRouter>
        </TimelineProvider>
      </ModeProvider>
    </QueryClientProvider>
  );
}

describe('M14 Guided Scan UI integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/scans/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: [] }) // Empty history triggers FTUX
        });
      }
      if (url.includes('/api/v1/scans/suggest-network')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { network: "10.0.0.0/8", last_devices_found: 42 } })
        });
      }
      if (url.includes('/api/v1/scans/scan_123/results')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { assets_found: 10, services_found: 5, riskScore: 'A' } })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} })
      });
    });
  });

  it('renders FTUX on Home when history is empty', async () => {
    renderWithProviders('/home');
    await waitFor(() => {
      expect(screen.getByText(/Welcome to Aegis/i)).toBeDefined();
      expect(screen.getByText(/Start First Scan/i)).toBeDefined();
    });
  });

  it('renders Guided Scan Wizard', async () => {
    renderWithProviders('/scan-center');
    await waitFor(() => {
      expect(screen.getByText(/What would you like to scan/i)).toBeDefined();
      expect(screen.getByText(/My Network/i)).toBeDefined();
    });
  });

  it('renders Scan Results Page', async () => {
    renderWithProviders('/scan-results/scan_123');
    await waitFor(() => {
      expect(screen.getByText(/Discovery Complete/i)).toBeDefined();
      expect(screen.getByText(/Security Grade/i)).toBeDefined();
      expect(screen.getByText('10')).toBeDefined(); // assets found
    });
  });
});
