import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ModeProvider } from '../src/hooks/useMode';
import { TimelineProvider } from '../src/hooks/useTimeline';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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
                <Route path="dashboard" element={<div>Dashboard Page</div>} />
                <Route path="reports" element={<div>Reports Page</div>} />
                <Route path="monitoring" element={<div>Monitoring Page</div>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </TimelineProvider>
      </ModeProvider>
    </QueryClientProvider>
  );
}

describe('M12 Implementation Verification', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('[PASS] home_page_renders_in_simple_mode', async () => {
    renderWithProviders('/home');
    
    // Verify default mode is simple mode
    expect(screen.getByText(/Home/i)).toBeDefined();
    expect(screen.getByText(/Scan Center/i)).toBeDefined();
    expect(screen.queryByText(/APQL Workspace/i)).toBeNull(); // Hidden in simple mode
    
    // Verify Home content
    expect(screen.getByText(/Welcome to Aegis/i)).toBeDefined();
    expect(screen.getByText(/Security Score/i)).toBeDefined();
    expect(screen.getByText('Assets')).toBeDefined();
    expect(screen.getByText('Services')).toBeDefined();
    expect(screen.getByText(/Start Scan/i)).toBeDefined();
  });

  it('[PASS] mode_switching_works_and_navigation_updates', async () => {
    renderWithProviders('/home');
    
    // Switch to Professional Mode
    const modeSelect = screen.getByRole('combobox');
    fireEvent.change(modeSelect, { target: { value: 'professional' } });
    
    // Verify navigation expands
    expect(screen.getByText(/APQL Workspace/i)).toBeDefined();
    expect(screen.getByText(/Graph Explorer/i)).toBeDefined();
    expect(screen.getByText(/Connectors/i)).toBeDefined();
    
    // Switch back to Simple Mode
    fireEvent.change(modeSelect, { target: { value: 'simple' } });
    expect(screen.queryByText(/APQL Workspace/i)).toBeNull();
  });

  it('[PASS] scan_center_renders_and_wizard_flow_works', { timeout: 10000 }, async () => {
    renderWithProviders('/scan-center');
    
    // Step 1: Scan Center Renders
    expect(screen.getByText(/What would you like to discover/i)).toBeDefined();
    
    // Select Network Discovery
    const networkBtn = screen.getByText(/Network Discovery/i);
    fireEvent.click(networkBtn);
    
    // Continue
    const continueBtn = screen.getByText(/Continue/i);
    fireEvent.click(continueBtn);
    
    // Step 2: Target Input
    expect(screen.getByText(/Enter Target Information/i)).toBeDefined();
    const targetInput = screen.getByRole('textbox');
    fireEvent.change(targetInput, { target: { value: '192.168.1.0/24' } });
    
    // Continue
    const continueBtn2 = screen.getByText(/Continue/i);
    fireEvent.click(continueBtn2);
    
    // Step 3: Review
    expect(screen.getByText(/Review Scan Details/i)).toBeDefined();
    expect(screen.getByText('192.168.1.0/24')).toBeDefined();
    
    // Run Scan
    const runBtn = screen.getByText(/Run Scan/i);
    fireEvent.click(runBtn);
    
    // Step 4: Run (Scanning Target)
    expect(screen.getByText(/Scanning Target/i)).toBeDefined();
    
    // Wait for the mock scan to complete (it auto-advances step when progress reaches 100)
    await waitFor(() => {
      expect(screen.getByText(/Scan Complete/i)).toBeDefined();
    }, { timeout: 6000 });
    
    // Step 5: Results Render
    expect(screen.getByText(/Risk Score/i)).toBeDefined();
    expect(screen.getByText(/Assets Found/i)).toBeDefined();
    expect(screen.getByText(/Services Found/i)).toBeDefined();
    expect(screen.getByText(/Identities/i)).toBeDefined();
    expect(screen.getByText(/Datastores/i)).toBeDefined();
  });
});
