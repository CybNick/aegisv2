import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { Server, Filter, Search, ShieldAlert } from 'lucide-react';
import './AssetInventory.css';

export default function AssetInventory() {
  const navigate = useNavigate();
  const { data: response, isLoading, error } = useAegisQuery<any>('/assets/inventory');
  const [searchTerm, setSearchTerm] = useState('');
  const [envFilter, setEnvFilter] = useState('All');

  const assets = response?.data || [];

  const filteredAssets = assets.filter((a: any) => {
    const matchesSearch = a.name?.toLowerCase().includes(searchTerm.toLowerCase()) || a.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesEnv = envFilter === 'All' || a.environment === envFilter;
    return matchesSearch && matchesEnv;
  });

  return (
    <div className="asset-inventory-page">
      <div className="page-header">
        <h1 className="page-title"><Server size={24} /> Asset Inventory</h1>
        <p className="page-description">Business-aware inventory classified by environment and criticality.</p>
      </div>

      <div className="filters-bar card mt-4">
        <div className="search-box">
          <Search size={18} className="text-secondary" />
          <input 
            type="text" 
            placeholder="Search assets by name or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-select">
          <Filter size={18} className="text-secondary" />
          <select value={envFilter} onChange={(e) => setEnvFilter(e.target.value)}>
            <option value="All">All Environments</option>
            <option value="Production">Production</option>
            <option value="Staging">Staging</option>
            <option value="Development">Development</option>
            <option value="Testing">Testing</option>
            <option value="Unknown">Unknown</option>
          </select>
        </div>
      </div>

      <div className="card mt-4 p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">Loading inventory...</div>
        ) : error ? (
          <div className="p-8 text-center text-error">Error loading inventory</div>
        ) : filteredAssets.length === 0 ? (
          <div className="p-8 text-center text-secondary">No assets found matching filters.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Asset / Service</th>
                <th>Type</th>
                <th>Environment</th>
                <th>Criticality</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {filteredAssets.map((asset: any) => (
                <tr key={asset.id} className="cursor-pointer hover:bg-secondary/10" onClick={() => navigate(`/assets/${asset.id}`)}>
                  <td>
                    <strong>{asset.name}</strong>
                    <div className="text-xs text-secondary font-mono truncate max-w-[200px]" title={asset.id}>{asset.id}</div>
                  </td>
                  <td><span className="badge badge-outline">{asset.type}</span></td>
                  <td>
                    <span className={`badge ${asset.environment === 'Production' ? 'badge-primary' : 'badge-outline'}`}>
                      {asset.environment}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2 font-bold" style={{ color: `var(--${asset.criticality === 'Critical' || asset.criticality === 'High' ? 'danger' : 'warning'}-color)` }}>
                      {asset.criticality !== 'Low' && <ShieldAlert size={14} />}
                      {asset.criticality}
                    </div>
                  </td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(asset.tags || {}).slice(0, 2).map(([k, v]) => (
                        <span key={k} className="text-xs bg-tertiary px-1 py-0.5 rounded border">
                          {k}: {String(v)}
                        </span>
                      ))}
                      {Object.keys(asset.tags || {}).length > 2 && <span className="text-xs text-secondary">+{Object.keys(asset.tags).length - 2} more</span>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
