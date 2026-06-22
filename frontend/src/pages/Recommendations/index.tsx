import { useState } from 'react';
import { useAegisQuery } from '../../api/hooks';
import { ShieldAlert, AlertTriangle, AlertCircle, CheckCircle, ChevronDown, ChevronRight, Activity } from 'lucide-react';

export default function Recommendations() {
  const { data: recsResponse, isLoading, error } = useAegisQuery<any>('/recommendations');
  const [filter, setFilter] = useState('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const recommendations = recsResponse || [];

  const filteredRecs = recommendations.filter((r: any) => {
    if (filter === 'All') return true;
    if (filter === 'Critical Only') return r.severity === 'CRITICAL';
    if (filter === 'High Risk') return r.severity === 'CRITICAL' || r.severity === 'HIGH';
    return true;
  });

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return <ShieldAlert size={20} className="text-danger" />;
      case 'HIGH': return <AlertTriangle size={20} className="text-warning" />;
      case 'MEDIUM': return <AlertCircle size={20} className="text-info" />;
      default: return <CheckCircle size={20} className="text-success" />;
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="text-primary" /> Action Center
        </h1>
        <p className="text-secondary mt-2">Prioritized recommendations based on exposure and business criticality.</p>
      </div>

      <div className="flex gap-4 mb-6">
        <button 
          className={`btn ${filter === 'All' ? 'btn-primary' : 'bg-tertiary border border-border'}`}
          onClick={() => setFilter('All')}
        >
          All Recommendations ({recommendations.length})
        </button>
        <button 
          className={`btn ${filter === 'Critical Only' ? 'btn-primary' : 'bg-tertiary border border-border'}`}
          onClick={() => setFilter('Critical Only')}
        >
          Critical Only ({recommendations.filter((r: any) => r.severity === 'CRITICAL').length})
        </button>
        <button 
          className={`btn ${filter === 'High Risk' ? 'btn-primary' : 'bg-tertiary border border-border'}`}
          onClick={() => setFilter('High Risk')}
        >
          High Risk ({recommendations.filter((r: any) => r.severity === 'CRITICAL' || r.severity === 'HIGH').length})
        </button>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <div className="p-8 text-center card">Loading recommendations...</div>
        ) : error ? (
          <div className="p-8 text-center card text-error">Failed to load recommendations.</div>
        ) : filteredRecs.length === 0 ? (
          <div className="p-8 text-center card text-success flex flex-col items-center gap-4">
            <CheckCircle size={48} />
            <p>No critical recommendations found! Your environment is secure.</p>
          </div>
        ) : (
          filteredRecs.map((rec: any) => (
            <div key={rec.id} className="card p-0 overflow-hidden border border-border">
              <div 
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-secondary/5 transition-colors"
                onClick={() => setExpandedId(expandedId === rec.id ? null : rec.id)}
              >
                <div className="flex items-center gap-4">
                  {getSeverityIcon(rec.severity)}
                  <div>
                    <h3 className="font-bold text-lg">{rec.title}</h3>
                    <p className="text-sm text-secondary truncate max-w-2xl">{rec.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="badge badge-outline">{rec.category}</span>
                  {expandedId === rec.id ? <ChevronDown size={20} className="text-secondary" /> : <ChevronRight size={20} className="text-secondary" />}
                </div>
              </div>
              
              {expandedId === rec.id && (
                <div className="p-4 bg-tertiary border-t border-border grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-bold mb-2 text-sm uppercase tracking-wider text-secondary">Why It Matters</h4>
                    <ul className="space-y-2">
                      {rec.reason.map((r: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <AlertCircle size={16} className="text-warning shrink-0 mt-0.5" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-bold mb-2 text-sm uppercase tracking-wider text-secondary">What To Do Next</h4>
                    <ul className="space-y-2">
                      {rec.actions.map((a: string, i: number) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle size={16} className="text-success shrink-0 mt-0.5" />
                          <span>{a}</span>
                        </li>
                      ))}
                    </ul>
                    {rec.affected_nodes && rec.affected_nodes.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-bold mb-2 text-sm uppercase tracking-wider text-secondary">Affected Assets</h4>
                        <div className="flex flex-wrap gap-2">
                          {rec.affected_nodes.map((node: string) => (
                            <a key={node} href={`/assets/${node}`} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded border border-primary/20 hover:bg-primary/20 transition-colors">
                              {node}
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
