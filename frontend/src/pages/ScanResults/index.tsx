import { useParams, useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { CheckCircle, ShieldAlert, ArrowLeft, Info, AlertTriangle, AlertCircle } from 'lucide-react';
import './ScanResults.css';

export default function ScanResults() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: results, isLoading, error } = useAegisQuery<any>(`/scans/${id}/results`, {
    enabled: !!id
  });

  const { data: recsData } = useAegisQuery<any>('/recommendations', {
    enabled: !!id
  });

  if (isLoading) {
    return <div className="scan-results-page center">Loading scan results...</div>;
  }

  if (error || !results) {
    return <div className="scan-results-page center error">Error loading results.</div>;
  }

  const recommendations = recsData || [];
  
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return <ShieldAlert size={20} className="text-danger shrink-0 mt-1" />;
      case 'HIGH': return <AlertTriangle size={20} className="text-warning shrink-0 mt-1" />;
      case 'MEDIUM': return <AlertCircle size={20} className="text-info shrink-0 mt-1" />;
      default: return <Info size={20} className="text-success shrink-0 mt-1" />;
    }
  };

  return (
    <div className="scan-results-page">
      <div className="results-header">
        <button className="back-btn" onClick={() => navigate('/home')}>
          <ArrowLeft size={18} /> Back to Dashboard
        </button>
        <div className="header-title-row">
          <CheckCircle size={32} className="success-icon" />
          <h1>Discovery Complete</h1>
        </div>
        <p className="header-subtitle">Aegis has analyzed your environment. Here is what you need to know.</p>
      </div>

      <div className="mt-8 space-y-6">
        {recommendations.length === 0 ? (
          <div className="card text-center p-12">
            <CheckCircle size={48} className="text-success mx-auto mb-4" />
            <h2 className="text-2xl font-bold">No Issues Found</h2>
            <p className="text-secondary mt-2">Your environment looks secure based on the latest scan.</p>
            <button className="btn-primary mt-6" onClick={() => navigate('/home')}>Return to Dashboard</button>
          </div>
        ) : (
          recommendations.map((rec: any) => (
            <div key={rec.id} className="card p-0 overflow-hidden border border-border">
              <div className="bg-tertiary border-b border-border p-4 flex items-start gap-4">
                {getSeverityIcon(rec.severity)}
                <div>
                  <div className="text-xs font-bold text-secondary uppercase tracking-wider mb-1">What We Found</div>
                  <h3 className="text-xl font-bold">{rec.title}</h3>
                  <p className="text-secondary mt-1">{rec.description}</p>
                </div>
              </div>
              
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <div className="text-xs font-bold text-secondary uppercase tracking-wider mb-3">Why It Matters</div>
                  <ul className="space-y-3">
                    {rec.reason.map((r: string, i: number) => (
                      <li key={i} className="flex items-start gap-3 text-sm">
                        <AlertCircle size={16} className="text-warning shrink-0 mt-0.5" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <div className="text-xs font-bold text-secondary uppercase tracking-wider mb-3">What To Do Next</div>
                  <div className="bg-primary/5 rounded border border-primary/20 p-4">
                    <ul className="space-y-3">
                      {rec.actions.map((a: string, i: number) => (
                        <li key={i} className="flex items-start gap-3 text-sm font-medium">
                          <CheckCircle size={16} className="text-success shrink-0 mt-0.5" />
                          <span>{a}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {rec.affected_nodes && rec.affected_nodes.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-border">
                      <div className="text-xs text-secondary mb-2">Affected Assets:</div>
                      <div className="flex flex-wrap gap-2">
                        {rec.affected_nodes.map((node: string) => (
                          <span key={node} className="text-xs bg-tertiary px-2 py-1 rounded border border-border font-mono text-secondary">
                            {node}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
