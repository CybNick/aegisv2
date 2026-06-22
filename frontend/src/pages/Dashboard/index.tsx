import { useAegisQuery } from '../../api/hooks';
import { Server, Network, Users, Database, ShieldAlert, Activity } from 'lucide-react';
import './Dashboard.css';

interface ExecReport {
  total_assets: number;
  total_services: number;
  total_identities: number;
  total_datastores: number;
  total_relationships: number;
}

export default function Dashboard() {
  const { data: report, isLoading } = useAegisQuery<ExecReport>('/reports/executive?format=json');
  const { data: recsData } = useAegisQuery<any>('/recommendations/top');
  const { data: events } = useAegisQuery<any[]>('/events');

  if (isLoading) return <div className="p-8 text-center card">Loading dashboard...</div>;
  
  const topRecs = recsData || [];

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-description">Overview of your environment's exposure and assets.</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon"><Server /></div>
          <div className="kpi-value">{report?.total_assets || 0}</div>
          <div className="kpi-label">Assets</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon"><Network /></div>
          <div className="kpi-value">{report?.total_services || 0}</div>
          <div className="kpi-label">Services</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon"><Users /></div>
          <div className="kpi-value">{report?.total_identities || 0}</div>
          <div className="kpi-label">Identities</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon"><Database /></div>
          <div className="kpi-value">{report?.total_datastores || 0}</div>
          <div className="kpi-label">Datastores</div>
        </div>
      </div>

      <div className="dashboard-row">
        <div className="card risk-card">
          <h3><ShieldAlert size={18} /> Top Recommendations</h3>
          {topRecs && topRecs.length > 0 ? (
            <ul className="risk-list">
              {topRecs.map((r: any, i: number) => (
                <li key={i} className="risk-item">
                  <span className={`badge ${r.severity === 'CRITICAL' ? 'badge-primary' : 'badge-outline'}`}>{r.severity}</span>
                  <div className="flex flex-col">
                    <span className="font-bold">{r.title}</span>
                    <span className="text-xs text-secondary truncate w-48">{r.description}</span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-text">No active risks detected.</p>
          )}
        </div>

        <div className="card events-card">
          <h3><Activity size={18} /> Recent Events</h3>
          {events && events.length > 0 ? (
            <ul className="events-list">
              {[...events].reverse().slice(0, 10).map((e: any, i: number) => (
                <li key={i} className="event-item">
                  <span className="event-time">{new Date(e.timestamp * 1000).toLocaleString()}</span>
                  <span className="event-action badge">{e.metadata?.action || e.event_type}</span>
                  <span className="event-entity">{e.metadata?.target || e.affected_entities?.[0] || 'System'}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-text">No recent events in the current context.</p>
          )}
        </div>
      </div>
    </div>
  );
}
