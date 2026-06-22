import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Exposure from '../src/pages/Exposure';
import CriticalAssets from '../src/pages/CriticalAssets';
import BlastRadius from '../src/pages/BlastRadius';
import AttackPaths from '../src/pages/AttackPaths';
import * as apiHooks from '../src/api/hooks';

// Mock the API hooks
vi.mock('../src/api/hooks', () => ({
  useAegisQuery: vi.fn(),
}));

const queryClient = new QueryClient();

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>{children}</BrowserRouter>
  </QueryClientProvider>
);

describe('Milestone 17 - Exposure & Attack Path Intelligence', () => {
  
  describe('Exposure Explorer', () => {
    it('renders exposure categories correctly', () => {
      vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
        data: {
          internet_reachable_assets: [{ id: 'asset1', name: 'Public Web' }],
          cloud_resources: [{ id: 'cloud1', provider: 'AWS' }],
          exposed_datastores: [{ id: 'db1', type: 'postgres' }],
        },
        isLoading: false,
        error: null
      } as any);

      render(<Wrapper><Exposure /></Wrapper>);
      expect(screen.getByText('Exposure Explorer')).toBeDefined();
      expect(screen.getByText('Public Web')).toBeDefined();
      expect(screen.getByText('(AWS)')).toBeDefined();
    });
  });

  describe('Critical Assets', () => {
    it('renders ranked assets based on centrality and risk', () => {
      vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
        data: {
          assets: [
            { id: '1', name: 'Core DB', type: 'DATASTORE', centrality: 5, downstream_dependencies: 10, criticality_score: 95 }
          ]
        },
        isLoading: false,
        error: null
      } as any);

      render(<Wrapper><CriticalAssets /></Wrapper>);
      expect(screen.getByText('Critical Assets')).toBeDefined();
      expect(screen.getByText('Core DB')).toBeDefined();
      expect(screen.getByText('95')).toBeDefined();
    });
  });

  describe('Blast Radius', () => {
    it('calculates downstream cascading impacts', async () => {
      vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
        data: {
          total_impacted: 3,
          impact_by_type: { ASSET: 2, SERVICE: 1 },
          affected_resources: [
            { id: 'res1', type: 'ASSET', name: 'Downstream App' }
          ]
        },
        isLoading: false,
        error: null
      } as any);

      render(<Wrapper><BlastRadius /></Wrapper>);
      expect(screen.getByText('Blast Radius')).toBeDefined();

      const input = screen.getByPlaceholderText(/Enter Entity ID/);
      fireEvent.change(input, { target: { value: 'node_test' } });
      fireEvent.click(screen.getByText('Analyze Impact'));

      await waitFor(() => {
        expect(screen.getByText('Total Resources Impacted')).toBeDefined();
        expect(screen.getByText('Downstream App')).toBeDefined();
      });
    });
  });

  describe('Attack Paths', () => {
    it('calculates and visualizes shortest paths', async () => {
      vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
        data: {
          distance: 3,
          severity: 'HIGH',
          nodes: ['n1', 'n2', 'n3']
        },
        isLoading: false,
        error: null
      } as any);

      render(<Wrapper><AttackPaths /></Wrapper>);
      expect(screen.getByText('Attack Paths')).toBeDefined();

      const sourceInputs = screen.getAllByRole('textbox');
      fireEvent.change(sourceInputs[0], { target: { value: 'source_node' } });
      fireEvent.change(sourceInputs[1], { target: { value: 'target_node' } });
      fireEvent.click(screen.getByText('Find Path'));

      await waitFor(() => {
        expect(screen.getByText('Path Discovered')).toBeDefined();
        expect(screen.getByText('Distance: 3 hops')).toBeDefined();
        expect(screen.getByText('HIGH SEVERITY')).toBeDefined();
        expect(screen.getByText('n1')).toBeDefined();
        expect(screen.getByText('n3')).toBeDefined();
      });
    });
  });
});
