import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ModeProvider } from '../src/hooks/useMode';
import { TimelineProvider } from '../src/hooks/useTimeline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import Monitoring from '../src/pages/Monitoring';
import AlertCenter from '../src/pages/AlertCenter';
import MainLayout from '../src/layouts/MainLayout';

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
              <Route element={<MainLayout />}>
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/alerts" element={<AlertCenter />} />
              </Route>
            </Routes>
          </MemoryRouter>
        </TimelineProvider>
      </ModeProvider>
    </QueryClientProvider>
  );
}

describe('M15 Monitoring UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mode for tests is professional to see the nav links
    localStorage.setItem('aegis-mode', 'professional');

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/monitoring/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { enabled: true, interval: 15, targets: { network: ['10.0.0.0/8'] } } })
        });
      }
      if (url.includes('/api/v1/monitoring/alerts')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: [
            { id: '1', severity: 'CRITICAL', title: 'Risk Score Increased', description: 'Test', timestamp: 12345, resolved: false }
          ] })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} })
      });
    });
  });

  it('renders Monitoring page with status', async () => {
    renderWithProviders('/monitoring');
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Continuous Monitoring/i })).toBeDefined();
      expect(screen.getByText(/Monitoring is Active/i)).toBeDefined();
      expect(screen.getByText(/Every 15 minutes/i)).toBeDefined();
    });
  });

  it('renders Alert Center with active alerts', async () => {
    renderWithProviders('/alerts');
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Alert Center/i })).toBeDefined();
      expect(screen.getByText(/Risk Score Increased/i)).toBeDefined();
      expect(screen.getByText(/CRITICAL/i)).toBeDefined();
    });
  });

  it('renders Monitoring and Alerts in Professional Nav', async () => {
    renderWithProviders('/monitoring');
    await waitFor(() => {
      // Sidebar should contain both links
      const navLinks = screen.getAllByRole('link');
      const hasMonitoring = navLinks.some(l => l.textContent?.includes('Monitoring'));
      const hasAlerts = navLinks.some(l => l.textContent?.includes('Alerts'));
      expect(hasMonitoring).toBe(true);
      expect(hasAlerts).toBe(true);
    });
  });
});
