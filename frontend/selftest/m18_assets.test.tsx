import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AssetInventory from '../src/pages/AssetInventory';
import AssetDetails from '../src/pages/AssetDetails';
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

describe('Milestone 18 - Asset Intelligence & Classification', () => {
  
  describe('Asset Inventory', () => {
    it('renders and filters classified assets', () => {
      vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
        data: {
          data: [
            { id: '1', name: 'Prod DB', type: 'DATASTORE', environment: 'Production', criticality: 'High', tags: { env: 'prod' } },
            { id: '2', name: 'Dev API', type: 'SERVICE', environment: 'Development', criticality: 'Low', tags: { env: 'dev' } }
          ]
        },
        isLoading: false,
        error: null
      } as any);

      render(<Wrapper><AssetInventory /></Wrapper>);
      expect(screen.getByText('Asset Inventory')).toBeDefined();
      expect(screen.getByText('Prod DB')).toBeDefined();
      expect(screen.getByText('Dev API')).toBeDefined();
      
      // Filter by Production
      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: 'Production' } });
      
      expect(screen.getByText('Prod DB')).toBeDefined();
      expect(screen.queryByText('Dev API')).toBeNull();
    });
  });

  describe('Asset Details', () => {
    it('renders classification, sensitivity, and ownership', () => {
      // Mock useParams
      vi.mock('react-router-dom', async () => {
        const actual = await vi.importActual('react-router-dom');
        return {
          ...actual,
          useParams: () => ({ id: 'node_1' })
        };
      });
      
      vi.mocked(apiHooks.useAegisQuery).mockReturnValue({
        data: {
          data: {
            id: 'node_1',
            name: 'Customer Database',
            type: 'DATASTORE',
            environment: 'Production',
            sensitivity: 'Restricted',
            criticality: { level: 'Critical', score: 95, factors: ['Holds PII'] },
            ownership: { team: 'Data Platform', technical: 'alice@corp', business: 'bob@corp' },
            attributes: { "some": "val" }
          }
        },
        isLoading: false,
        error: null
      } as any);

      render(<Wrapper><AssetDetails /></Wrapper>);
      
      expect(screen.getByText('Customer Database')).toBeDefined();
      expect(screen.getByText('Production')).toBeDefined();
      expect(screen.getByText('Restricted')).toBeDefined();
      expect(screen.getByText(/Critical \(Score:/)).toBeDefined();
      expect(screen.getByText('Data Platform')).toBeDefined();
      expect(screen.getByText('alice@corp')).toBeDefined();
      expect(screen.getByText('bob@corp')).toBeDefined();
      expect(screen.getByText('Holds PII', { exact: false })).toBeDefined();
    });
  });

});
