import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { ArrowLeft, ShieldAlert, AlertTriangle } from 'lucide-react';
import './Intelligence.css';

export default function Risk() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const nodeId = searchParams.get('node');

  const { data, isLoading, error } = useAegisQuery<any>(`/intelligence/risk/${nodeId}`, {
    enabled: !!nodeId
  });

  if (!nodeId) {
    return (
      <div className="intelligence-page empty-state">
        <ShieldAlert size={48} className="empty-icon" />
        <h2>Risk Explorer</h2>
        <p>No node selected. Please select a node from the Cyber Graph to view its risk factors.</p>
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
        <h1 className="page-title"><ShieldAlert size={24} /> Risk Explorer</h1>
        <p className="page-description">Explainable risk scoring for: <strong>{nodeId}</strong></p>
      </div>

      {isLoading ? (
        <div className="loading-state">Loading risk analysis...</div>
      ) : error ? (
        <div className="error-state">Error loading risk data.</div>
      ) : data ? (
        <div className="risk-container">
          <div className="risk-summary card">
            <div className="risk-score-display">
              <span className="risk-score-value">{data.score}</span>
              <span className="risk-score-label">/ 100</span>
            </div>
            <div className={`risk-category-badge risk-${data.category.toLowerCase()}`}>
              {data.category} RISK
            </div>
          </div>

          <div className="factors-container card mt-4">
            <h3><AlertTriangle size={18} /> Contributing Factors</h3>
            <p className="text-muted mb-4">Aegis risk is deterministically calculated. No black-box AI scoring.</p>
            
            {(!data.contributing_factors || Object.keys(data.contributing_factors).length === 0) ? (
              <p className="text-muted">No specific risk factors identified.</p>
            ) : (
              <ul className="factors-list">
                {Object.entries(data.contributing_factors).map(([factor, value]) => (
                  <li key={factor} className="factor-item">
                    <span className="factor-name capitalize">{factor.replace(/_/g, ' ')}</span>
                    <span className="factor-value">
                      {typeof value === 'number' ? value.toFixed(2) : String(value)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
