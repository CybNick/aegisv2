import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import APQLWorkspace from '../src/pages/APQL';
import { TimelineProvider } from '../src/hooks/useTimeline';
import { MemoryRouter } from 'react-router-dom';
import * as apiClient from '../src/api/client';

// Mock the API client
vi.mock('../src/api/client', () => ({
  api: {
    post: vi.fn(),
  }
}));

// Mock react-router useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual as any,
    useNavigate: () => mockNavigate,
  };
});

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <TimelineProvider>
      <MemoryRouter>
        {ui}
      </MemoryRouter>
    </TimelineProvider>
  );
}

describe('M11 Integration Verification (APQL)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('[PASS] editor_render', () => {
    renderWithProviders(<APQLWorkspace />);
    expect(screen.getByText(/APQL Workspace/i)).toBeDefined();
    expect(screen.getByRole('textbox')).toBeDefined();
    expect(screen.getByRole('button', { name: /Run Query/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Clear/i })).toBeDefined();
    expect(screen.getByRole('button', { name: /Save/i })).toBeDefined();
  });

  it('[PASS] query_execution and results_render', async () => {
    const mockResults = {
      success: true,
      data: {
        results: [
          { id: 'asset-1', type: 'ASSET', confidence: 0.9, attributes: { risk: 8 } }
        ]
      }
    };
    (apiClient.api.post as any).mockResolvedValueOnce(mockResults);

    renderWithProviders(<APQLWorkspace />);
    
    const editor = screen.getByRole('textbox');
    fireEvent.change(editor, { target: { value: 'FIND ASSETS' } });
    
    const runBtn = screen.getByRole('button', { name: /Run Query/i });
    fireEvent.click(runBtn);
    
    expect(apiClient.api.post).toHaveBeenCalledWith('/apql/query', { query: 'FIND ASSETS' }, { as_of: 'now' });
    
    // Wait for results
    await screen.findByText('Results (1)');
    expect(screen.getByText('asset-1...')).toBeDefined();
    expect(screen.getByText('90%')).toBeDefined();
    expect(screen.getByText('8')).toBeDefined(); // risk
  });

  it('[PASS] query_history', async () => {
    const mockResults = { success: true, data: { results: [] } };
    (apiClient.api.post as any).mockResolvedValue(mockResults);

    renderWithProviders(<APQLWorkspace />);
    
    const editor = screen.getByRole('textbox');
    fireEvent.change(editor, { target: { value: 'FIND ZONES' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Query/i }));
    
    await waitFor(() => {
      expect(localStorage.getItem('apql_history')).toContain('FIND ZONES');
    });
    
    // History list should render
    expect(screen.getByText('FIND ZONES', { selector: '.query-text' })).toBeDefined();
  });

  it('[PASS] saved_queries', async () => {
    renderWithProviders(<APQLWorkspace />);
    
    const editor = screen.getByRole('textbox');
    fireEvent.change(editor, { target: { value: 'SHOW IDENTITIES' } });
    
    // Save
    const saveBtn = screen.getByRole('button', { name: /Save/i });
    fireEvent.click(saveBtn);
    
    expect(localStorage.getItem('apql_saved')).toContain('SHOW IDENTITIES');
    expect(screen.getByText('SHOW IDENTITIES', { selector: '.query-text' })).toBeDefined();
    
    // Delete
    const deleteBtn = document.querySelector('.text-danger');
    if (deleteBtn) {
        fireEvent.click(deleteBtn);
    }
    
    expect(localStorage.getItem('apql_saved')).not.toContain('SHOW IDENTITIES');
  });

  it('[PASS] graph_navigation', async () => {
    const mockResults = {
      success: true,
      data: {
        results: [
          { id: 'node-to-graph', type: 'SERVICE', confidence: 1.0, attributes: {} }
        ]
      }
    };
    (apiClient.api.post as any).mockResolvedValueOnce(mockResults);

    renderWithProviders(<APQLWorkspace />);
    
    const editor = screen.getByRole('textbox');
    fireEvent.change(editor, { target: { value: 'FIND SERVICES' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Query/i }));
    
    await screen.findByText('node-to-graph...');
    
    // Click View in Graph button
    const viewBtn = document.querySelector('button[title="View in Graph"]');
    expect(viewBtn).toBeDefined();
    fireEvent.click(viewBtn!);
    
    expect(mockNavigate).toHaveBeenCalledWith('/graph?search=node-to-graph');
  });
});
