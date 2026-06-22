import { useState } from 'react';
import { useAegisQuery } from '../../api/hooks';
import { ShieldAlert, ArrowRight, Target, Activity, CheckCircle, Crosshair } from 'lucide-react';
import './AttackPaths.css';

export default function AttackPaths() {
  const [sourceId, setSourceId] = useState('');
  const [targetId, setTargetId] = useState('');
  const [searchTrigger, setSearchTrigger] = useState(0);

  const { data: path, isLoading, error } = useAegisQuery<any>(
    `/intelligence/attack-paths?source_id=${sourceId}&target_id=${targetId}`,
    { enabled: searchTrigger > 0 && !!sourceId && !!targetId }
  );

  return (
    <div className="attack-paths-page">
      <div className="page-header">
        <h1 className="page-title"><Target size={24} /> Attack Paths</h1>
        <p className="page-description">Calculate deterministic shortest paths between any two entities.</p>
      </div>

      <div className="card path-finder">
        <div className="finder-inputs">
          <div className="form-group">
            <label>Source Node ID</label>
            <input 
              type="text" 
              placeholder="e.g., node_internet_attacker"
              value={sourceId}
              onChange={e => setSourceId(e.target.value)}
            />
          </div>
          <div className="form-group flex items-center justify-center pt-6 text-secondary">
            <ArrowRight size={24} />
          </div>
          <div className="form-group">
            <label>Target Node ID</label>
            <input 
              type="text" 
              placeholder="e.g., node_critical_database"
              value={targetId}
              onChange={e => setTargetId(e.target.value)}
            />
          </div>
          <div className="form-group pt-6">
            <button 
              className="btn-primary" 
              onClick={() => setSearchTrigger(prev => prev + 1)}
              disabled={!sourceId || !targetId || isLoading}
            >
              {isLoading ? 'Calculating...' : 'Find Path'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="card text-center p-8 mt-4 text-error border-error">
          <ShieldAlert size={48} className="mx-auto mb-4" />
          <h3>Path Not Found</h3>
          <p>{error.message || 'No deterministic path exists between these entities.'}</p>
        </div>
      )}

      {path && path.nodes && (
        <div className="card mt-4">
          <div className="path-summary flex justify-between items-center mb-6">
            <div>
              <h3 className="flex items-center gap-2">
                <Crosshair size={20} className="text-accent" />
                Path Discovered
              </h3>
              <p className="text-secondary">Distance: {path.distance} hops</p>
            </div>
            <div className={`badge badge-${path.severity === 'CRITICAL' ? 'danger' : 'warning'}`}>
              {path.severity} SEVERITY
            </div>
          </div>

          <div className="path-visualization">
            {path.nodes.map((node: string, index: number) => (
              <div key={index} className="path-step">
                <div className="step-circle">
                  {index === 0 ? <Activity size={16} /> : index === path.nodes.length - 1 ? <Target size={16} /> : <CheckCircle size={16} />}
                </div>
                <div className="step-content">
                  <div className="step-id">{node}</div>
                </div>
                {index < path.nodes.length - 1 && (
                  <div className="step-line" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
