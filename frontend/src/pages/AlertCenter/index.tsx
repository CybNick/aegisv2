import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Info, Clock, CheckCircle, ExternalLink } from 'lucide-react';
import { useAegisQuery } from '../../api/hooks';
import './AlertCenter.css';

export default function AlertCenter() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState('all'); // all, critical, resolved
  const { data: alerts } = useAegisQuery<any[]>('/monitoring/alerts');

  if (!alerts) return <div className="p-8">Loading alerts...</div>;

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'critical') return a.severity === 'CRITICAL';
    if (filter === 'resolved') return a.resolved;
    return !a.resolved; // 'all' means all unresolved
  });

  return (
    <div className="alert-center-container">
      <header className="page-header">
        <div className="flex justify-between items-center">
          <div>
            <h1>Alert Center</h1>
            <p>Review and act on deterministic monitoring events.</p>
          </div>
          <div className="filter-controls">
            <button className={`filter-btn ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>Active</button>
            <button className={`filter-btn ${filter === 'critical' ? 'active' : ''}`} onClick={() => setFilter('critical')}>Critical</button>
            <button className={`filter-btn ${filter === 'resolved' ? 'active' : ''}`} onClick={() => setFilter('resolved')}>Resolved</button>
          </div>
        </div>
      </header>

      <div className="alerts-list">
        {filteredAlerts.length === 0 ? (
          <div className="empty-alerts">
            <CheckCircle size={48} className="text-success mb-4" />
            <h2>No Alerts Found</h2>
            <p>Your environment matches your security baselines.</p>
          </div>
        ) : (
          filteredAlerts.map(alert => (
            <div key={alert.id} className={`alert-card severity-${alert.severity.toLowerCase()}`}>
              <div className="alert-header">
                <div className="alert-title-row">
                  <ShieldAlert size={20} />
                  <h3>{alert.title}</h3>
                  <span className="severity-badge">{alert.severity}</span>
                </div>
                <div className="alert-time">
                  <Clock size={14} />
                  {new Date(alert.timestamp * 1000).toLocaleString()}
                </div>
              </div>
              <div className="alert-body">
                <p>{alert.description}</p>
                {alert.details && (
                  <pre className="alert-details">{JSON.stringify(alert.details, null, 2)}</pre>
                )}
              </div>
              <div className="alert-footer">
                <div className="alert-actions">
                  <button className="btn-secondary btn-sm" onClick={() => navigate('/evidence')}>
                    <Info size={14} /> View Evidence
                  </button>
                  <button className="btn-secondary btn-sm" onClick={() => navigate('/risk')}>
                    <ShieldAlert size={14} /> Analyze Risk
                  </button>
                  <button className="btn-secondary btn-sm" onClick={() => navigate('/dependencies')}>
                    <ExternalLink size={14} /> Show Dependencies
                  </button>
                </div>
                {!alert.resolved && (
                  <button className="btn-primary btn-sm">Mark Resolved</button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
