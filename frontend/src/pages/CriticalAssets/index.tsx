import { useAegisQuery } from '../../api/hooks';
import { Star, ShieldAlert, GitMerge } from 'lucide-react';
import './CriticalAssets.css';

export default function CriticalAssets() {
  const { data: response, isLoading, error } = useAegisQuery<any>('/intelligence/critical-assets?limit=50');
  const assets = response?.assets || [];

  return (
    <div className="critical-assets-page">
      <div className="page-header">
        <h1 className="page-title"><Star size={24} /> Critical Assets</h1>
        <p className="page-description">Ranked list of the most critical entities based on graph centrality, dependencies, and risk.</p>
      </div>

      <div className="card mt-4">
        {isLoading ? (
          <div className="p-8 text-center">Loading critical assets...</div>
        ) : error ? (
          <div className="p-8 text-center text-error">Error loading critical assets.</div>
        ) : assets.length === 0 ? (
          <div className="p-8 text-center text-secondary">No critical assets found.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Asset Name (ID)</th>
                <th>Type</th>
                <th>Centrality (Degree)</th>
                <th>Downstream Dependents</th>
                <th>Criticality Score</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset: any, index: number) => (
                <tr key={asset.id} className={index < 3 ? 'top-tier' : ''}>
                  <td>
                    <div className={`rank-badge ${index < 3 ? 'top-rank' : ''}`}>
                      #{index + 1}
                    </div>
                  </td>
                  <td>
                    <strong>{asset.name}</strong>
                    <div className="text-xs text-secondary font-mono mt-1">{asset.id}</div>
                  </td>
                  <td>
                    <span className="badge badge-outline">{asset.type}</span>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      <GitMerge size={14} className="text-secondary" />
                      {asset.centrality} connections
                    </div>
                  </td>
                  <td>{asset.downstream_dependencies}</td>
                  <td>
                    <div className="flex items-center gap-2 font-bold" style={{ color: `var(--${asset.criticality_score > 20 ? 'danger' : 'warning'}-color)` }}>
                      <ShieldAlert size={16} />
                      {asset.criticality_score}
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
