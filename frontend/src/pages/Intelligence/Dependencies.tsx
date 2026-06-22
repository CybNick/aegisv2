import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { ArrowLeft, GitBranch, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import './Intelligence.css';

export default function Dependencies() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const nodeId = searchParams.get('node');

  const { data, isLoading, error } = useAegisQuery<any>(`/intelligence/dependencies/${nodeId}`, {
    enabled: !!nodeId
  });

  if (!nodeId) {
    return (
      <div className="intelligence-page empty-state">
        <GitBranch size={48} className="empty-icon" />
        <h2>Dependency Explorer</h2>
        <p>No node selected. Please select a node from the Cyber Graph to view its dependencies.</p>
        <button onClick={() => navigate('/cyber-graph')} className="btn-primary">Go to Cyber Graph</button>
      </div>
    );
  }

  return (
    <div className="intelligence-page">
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate('/cyber-graph')}>
          <ArrowLeft size={18} /> Back to Graph
        </button>
        <h1 className="page-title"><GitBranch size={24} /> Dependency Explorer</h1>
        <p className="page-description">Exploring operational dependencies for: <strong>{nodeId}</strong></p>
      </div>

      {isLoading ? (
        <div className="loading-state">Loading dependencies...</div>
      ) : error ? (
        <div className="error-state">Error loading dependencies.</div>
      ) : data ? (
        <div className="dependency-grid">
          <div className="dependency-column">
            <h3><ArrowUpCircle size={18} /> Upstream Dependencies</h3>
            <p className="column-desc">Nodes that <strong>{nodeId}</strong> depends on to function.</p>
            {data.upstream.length === 0 ? (
              <p className="text-muted">No upstream dependencies found.</p>
            ) : (
              <ul className="dependency-list">
                {data.upstream.map((id: string) => (
                  <li key={id} onClick={() => navigate(`/dependencies?node=${id}`)}>{id}</li>
                ))}
              </ul>
            )}
          </div>
          
          <div className="dependency-column">
            <h3><ArrowDownCircle size={18} /> Downstream Impact</h3>
            <p className="column-desc">Nodes that depend on <strong>{nodeId}</strong>.</p>
            
            <div className="impact-summary">
              <h4>Impact Summary</h4>
              <div className="impact-stats">
                <div className="impact-stat">
                  <span className="stat-value">{data.impact.assets}</span>
                  <span className="stat-label">Assets Affected</span>
                </div>
                <div className="impact-stat">
                  <span className="stat-value">{data.impact.services}</span>
                  <span className="stat-label">Services Degraded</span>
                </div>
                <div className="impact-stat">
                  <span className="stat-value">{data.impact.datastores}</span>
                  <span className="stat-label">Datastores Unavailable</span>
                </div>
              </div>
            </div>

            {data.downstream.length === 0 ? (
              <p className="text-muted">No downstream impact found.</p>
            ) : (
              <ul className="dependency-list mt-4">
                {data.downstream.map((id: string) => (
                  <li key={id} onClick={() => navigate(`/dependencies?node=${id}`)}>{id}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
