import { useState } from 'react';
import { useAegisQuery } from '../../api/hooks';
import { Target, Activity, Flame, ShieldAlert, AlertTriangle } from 'lucide-react';
import './BlastRadius.css';

export default function BlastRadius() {
  const [nodeId, setNodeId] = useState('');
  const [searchTrigger, setSearchTrigger] = useState(0);

  const { data: blast, isLoading, error } = useAegisQuery<any>(
    `/intelligence/blast-radius/${nodeId}`,
    { enabled: searchTrigger > 0 && !!nodeId }
  );

  return (
    <div className="blast-radius-page">
      <div className="page-header">
        <h1 className="page-title"><Flame size={24} /> Blast Radius</h1>
        <p className="page-description">Identify downstream cascading impact if a specific entity is compromised or fails.</p>
      </div>

      <div className="card max-w-2xl mx-auto mt-8">
        <div className="form-group flex gap-4">
          <input 
            type="text" 
            className="flex-1"
            placeholder="Enter Entity ID (e.g., node_critical_database)"
            value={nodeId}
            onChange={e => setNodeId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && setSearchTrigger(prev => prev + 1)}
          />
          <button 
            className="btn-primary flex items-center gap-2"
            onClick={() => setSearchTrigger(prev => prev + 1)}
            disabled={!nodeId || isLoading}
          >
            {isLoading ? 'Calculating...' : <><Target size={18} /> Analyze Impact</>}
          </button>
        </div>
      </div>

      {error && (
        <div className="card max-w-2xl mx-auto text-center p-8 mt-4 text-error border-error">
          <AlertTriangle size={48} className="mx-auto mb-4" />
          <h3>Analysis Failed</h3>
          <p>{error.message || 'Entity not found or analysis failed.'}</p>
        </div>
      )}

      {blast && (
        <div className="impact-results mt-8">
          <div className="impact-summary-grid">
            <div className="card impact-metric border-danger">
              <div className="metric-icon bg-danger-light text-danger"><Flame size={24} /></div>
              <div className="metric-content">
                <div className="metric-label">Total Resources Impacted</div>
                <div className="metric-value text-danger">{blast.total_impacted}</div>
              </div>
            </div>
            <div className="card impact-metric">
              <div className="metric-icon bg-primary-light text-primary"><Activity size={24} /></div>
              <div className="metric-content">
                <div className="metric-label">Assets Affected</div>
                <div className="metric-value">{blast.impact_by_type?.ASSET || 0}</div>
              </div>
            </div>
            <div className="card impact-metric">
              <div className="metric-icon bg-warning-light text-warning"><ShieldAlert size={24} /></div>
              <div className="metric-content">
                <div className="metric-label">Services Affected</div>
                <div className="metric-value">{blast.impact_by_type?.SERVICE || 0}</div>
              </div>
            </div>
          </div>

          <div className="card mt-8">
            <h3 className="mb-4">Affected Downstream Resources</h3>
            {blast.affected_resources && blast.affected_resources.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Resource Name</th>
                    <th>Type</th>
                    <th>ID</th>
                  </tr>
                </thead>
                <tbody>
                  {blast.affected_resources.map((res: any, idx: number) => (
                    <tr key={idx}>
                      <td><strong>{res.name}</strong></td>
                      <td><span className="badge badge-outline">{res.type}</span></td>
                      <td className="font-mono text-sm text-secondary">{res.id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-secondary p-4 text-center">No downstream impact found for this entity.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
