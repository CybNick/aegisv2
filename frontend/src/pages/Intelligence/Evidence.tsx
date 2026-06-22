import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { ArrowLeft, Layers, ShieldCheck } from 'lucide-react';
import './Intelligence.css';

export default function Evidence() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const edgeId = searchParams.get('edge');

  const { data, isLoading, error } = useAegisQuery<any>(`/intelligence/evidence/${edgeId}`, {
    enabled: !!edgeId
  });

  if (!edgeId) {
    return (
      <div className="intelligence-page empty-state">
        <Layers size={48} className="empty-icon" />
        <h2>Evidence Explorer</h2>
        <p>No relationship selected. Please select an edge from the Cyber Graph to view its evidence.</p>
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
        <h1 className="page-title"><Layers size={24} /> Evidence Explorer</h1>
        <p className="page-description">Why does Aegis believe this relationship exists?</p>
      </div>

      {isLoading ? (
        <div className="loading-state">Loading evidence...</div>
      ) : error ? (
        <div className="error-state">Error loading evidence.</div>
      ) : data ? (
        <div className="evidence-container">
          <div className="relationship-summary card">
            <h3>Relationship</h3>
            <div className="relationship-flow">
              <span className="node-pill">{data.source}</span>
              <span className="flow-arrow">→</span>
              <span className="node-pill">{data.target}</span>
            </div>
            <div className="relationship-meta mt-4">
              <div className="meta-item">
                <span className="meta-label">Confidence:</span>
                <span className="meta-value">{(data.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Tier:</span>
                <span className={`meta-badge tier-${data.tier.toLowerCase()}`}>{data.tier}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Observed At:</span>
                <span className="meta-value">{new Date(data.observed_at * 1000).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="sources-container card mt-4">
            <h3><ShieldCheck size={18} /> Observation Sources</h3>
            {data.sources.length === 0 ? (
              <p className="text-muted">No specific sources identified.</p>
            ) : (
              <ul className="source-list">
                {data.sources.map((src: string) => (
                  <li key={src} className="source-item">{src}</li>
                ))}
              </ul>
            )}
          </div>
          
          <div className="evidence-docs card mt-4">
            <h3>Evidence Documents</h3>
            {data.evidence.length === 0 ? (
              <p className="text-muted">No evidence documents attached.</p>
            ) : (
              <ul className="evidence-list">
                {data.evidence.map((ev: string) => (
                  <li key={ev} className="evidence-item">{ev}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
