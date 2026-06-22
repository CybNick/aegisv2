import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ModeProvider } from '../src/hooks/useMode';
import { TimelineProvider } from '../src/hooks/useTimeline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import MainLayout from '../src/layouts/MainLayout';
import Dependencies from '../src/pages/Intelligence/Dependencies';
import Evidence from '../src/pages/Intelligence/Evidence';
import Risk from '../src/pages/Intelligence/Risk';
import CyberGraph from '../src/pages/CyberGraph';

// Mock cytoscape entirely since it relies on DOM features
vi.mock('cytoscape', () => ({
  default: vi.fn(() => ({
    on: vi.fn(),
    destroy: vi.fn(),
    fit: vi.fn(),
    center: vi.fn(),
    zoom: vi.fn(),
    getElementById: vi.fn()
  }))
}));

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
              <Route path="/" element={<MainLayout />}>
                <Route path="cyber-graph" element={<CyberGraph />} />
                <Route path="dependencies" element={<Dependencies />} />
                <Route path="evidence" element={<Evidence />} />
                <Route path="risk" element={<Risk />} />
              </Route>
            </Routes>
          </MemoryRouter>
        </TimelineProvider>
      </ModeProvider>
    </QueryClientProvider>
  );
}

describe('M13 Intelligence Frontend Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    // Mock global fetch
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/v1/graph/nodes')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { "node_1": { type: "ASSET", value: { name: "test-node" } } } })
        });
      }
      if (url.includes('/api/v1/graph/edges')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { "edge_1": { type: "DEPENDS_ON", src: "node_1", dst: "node_2" } } })
        });
      }
      if (url.includes('/api/v1/intelligence/dependencies')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { upstream: ["node_2"], downstream: [], impact: { assets: 0, services: 0, datastores: 0 } } })
        });
      }
      if (url.includes('/api/v1/intelligence/evidence')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { source: "node_1", target: "node_2", confidence: 1.0, tier: "VERIFIED", sources: ["test"], evidence: [], observed_at: 1000 } })
        });
      }
      if (url.includes('/api/v1/intelligence/risk')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true, data: { score: 85, category: "CRITICAL", contributing_factors: { "factor_a": 1.2 } } })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, data: {} })
      });
    });
  });

  it('renders Cyber Graph', async () => {
    renderWithProviders('/cyber-graph');
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Search nodes/i)).toBeDefined();
    });
  });

  it('renders Dependencies page', async () => {
    renderWithProviders('/dependencies?node=node_1');
    await waitFor(() => {
      expect(screen.getByText(/Dependency Explorer/i)).toBeDefined();
      expect(screen.getByText('node_2')).toBeDefined(); // Upstream
    });
  });

  it('renders Evidence page', async () => {
    renderWithProviders('/evidence?edge=edge_1');
    await waitFor(() => {
      expect(screen.getByText(/Evidence Explorer/i)).toBeDefined();
      expect(screen.getByText('VERIFIED')).toBeDefined();
    });
  });

  it('renders Risk page', async () => {
    renderWithProviders('/risk?node=node_1');
    await waitFor(() => {
      expect(screen.getByText(/Risk Explorer/i)).toBeDefined();
      expect(screen.getByText('85')).toBeDefined();
    });
  });
});
