import { useState } from 'react';
import { PlayCircle, StopCircle, Clock, Server, Save } from 'lucide-react';
import { useAegisQuery } from '../../api/hooks';

import './Monitoring.css';

export default function Monitoring() {
  const { data: statusData, refetch } = useAegisQuery<any>('/monitoring/status');
  const [isEditing, setIsEditing] = useState(false);
  
  // Local state for config form
  const [interval, setInterval] = useState(15);
  const [networkTarget, setNetworkTarget] = useState('192.168.1.0/24');
  
  const startMonitoring = { mutate: () => fetch('/api/v1/monitoring/start', { method: 'POST' }).then(() => refetch()), isPending: false };
  
  const stopMonitoring = { mutate: () => fetch('/api/v1/monitoring/stop', { method: 'POST' }).then(() => refetch()), isPending: false };

  const configMonitoring = { mutate: (data: any) => fetch('/api/v1/monitoring/configure', { method: 'POST', body: JSON.stringify(data), headers: { 'Content-Type': 'application/json' } }).then(() => { setIsEditing(false); refetch(); }), isPending: false };

  if (!statusData) return <div className="p-8">Loading monitoring status...</div>;

  const isActive = statusData.enabled;

  const handleSave = () => {
    configMonitoring.mutate({
      interval_minutes: interval,
      targets: {
        network: [networkTarget]
      }
    });
  };

  return (
    <div className="monitoring-container">
      <header className="page-header">
        <h1>Continuous Monitoring</h1>
        <p>Aegis background observation and detection engine.</p>
      </header>

      <div className="status-banner">
        <div className="status-indicator">
          <div className={`status-dot ${isActive ? 'active' : 'inactive'}`}></div>
          <h2>{isActive ? 'Monitoring is Active' : 'Monitoring is Disabled'}</h2>
        </div>
        <div className="status-actions">
          {isActive ? (
            <button className="btn-secondary" onClick={() => stopMonitoring.mutate()}>
              <StopCircle size={18} /> Pause Monitoring
            </button>
          ) : (
            <button className="btn-primary" onClick={() => startMonitoring.mutate()}>
              <PlayCircle size={18} /> Start Monitoring
            </button>
          )}
        </div>
      </div>

      <div className="monitoring-grid">
        <div className="monitoring-card">
          <div className="card-header">
            <h3><Clock size={18} /> Schedule Configuration</h3>
            {!isEditing && <button className="btn-link" onClick={() => setIsEditing(true)}>Edit</button>}
          </div>
          
          {isEditing ? (
            <div className="config-form">
              <label>Check Interval</label>
              <select value={interval} onChange={(e) => setInterval(Number(e.target.value))}>
                <option value={5}>Every 5 minutes</option>
                <option value={15}>Every 15 minutes</option>
                <option value={30}>Every 30 minutes</option>
                <option value={60}>Every 1 hour</option>
                <option value={360}>Every 6 hours</option>
                <option value={1440}>Every 24 hours</option>
              </select>
              
              <label>Network Target</label>
              <input 
                type="text" 
                value={networkTarget} 
                onChange={(e) => setNetworkTarget(e.target.value)} 
                placeholder="192.168.1.0/24" 
              />
              
              <div className="form-actions mt-4">
                <button className="btn-primary" onClick={handleSave} disabled={configMonitoring.isPending}>
                  <Save size={16} /> Save Changes
                </button>
                <button className="btn-secondary" onClick={() => setIsEditing(false)}>Cancel</button>
              </div>
            </div>
          ) : (
            <div className="config-display">
              <div className="config-row">
                <span className="config-label">Interval</span>
                <span className="config-value">Every {statusData.interval} minutes</span>
              </div>
              <div className="config-row">
                <span className="config-label">Last Check</span>
                <span className="config-value">{statusData.last_scan_time ? new Date(statusData.last_scan_time * 1000).toLocaleTimeString() : 'Never'}</span>
              </div>
              <div className="config-row">
                <span className="config-label">Next Check</span>
                <span className="config-value">{statusData.next_scan_time ? new Date(statusData.next_scan_time * 1000).toLocaleTimeString() : 'Pending'}</span>
              </div>
            </div>
          )}
        </div>

        <div className="monitoring-card">
          <div className="card-header">
            <h3><Server size={18} /> Targets Watched</h3>
          </div>
          <ul className="watched-list">
            <li><strong>Network:</strong> {statusData.targets?.network?.[0] || 'None'}</li>
            <li><strong>Web:</strong> None</li>
            <li><strong>Cloud:</strong> None</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
