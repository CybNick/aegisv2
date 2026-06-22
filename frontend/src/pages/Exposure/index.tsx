import { useAegisQuery } from '../../api/hooks';
import { Shield, Globe, Cloud, Database, Server } from 'lucide-react';
import './Exposure.css';

export default function Exposure() {
  const { data: exposure, isLoading, error } = useAegisQuery<any>('/intelligence/exposure');

  if (isLoading) return <div className="p-8 text-center">Loading exposure intelligence...</div>;
  if (error) return <div className="p-8 text-center text-error">Error loading exposure data</div>;

  const renderList = (items: any[], icon: any, title: string, color: string) => (
    <div className="card exposure-card">
      <div className="exposure-header" style={{ borderBottomColor: color }}>
        <div className="flex items-center gap-2" style={{ color }}>
          {icon}
          <h3>{title}</h3>
        </div>
        <div className="badge" style={{ backgroundColor: color, color: '#fff' }}>
          {items.length}
        </div>
      </div>
      <div className="exposure-content">
        {items.length === 0 ? (
          <p className="text-secondary text-sm">No exposure found.</p>
        ) : (
          <ul className="exposure-list">
            {items.map((item, i) => (
              <li key={i}>
                <span className="exposure-id" title={item.id}>{item.name || item.id}</span>
                {item.provider && <span className="text-xs text-secondary ml-2">({item.provider})</span>}
                {item.port && <span className="text-xs text-secondary ml-2">Port: {item.port}</span>}
                {item.type && <span className="text-xs text-secondary ml-2">Type: {item.type}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );

  return (
    <div className="exposure-page">
      <div className="page-header">
        <h1 className="page-title"><Shield size={24} /> Exposure Explorer</h1>
        <p className="page-description">Identify your externally exposed attack surface.</p>
      </div>

      <div className="exposure-grid">
        {renderList(exposure?.internet_reachable_assets || [], <Globe size={20} />, "Internet Assets", "var(--danger-color)")}
        {renderList(exposure?.internet_reachable_services || [], <Server size={20} />, "Public Services", "var(--warning-color)")}
        {renderList(exposure?.exposed_datastores || [], <Database size={20} />, "Exposed Databases", "var(--accent-color)")}
        {renderList(exposure?.cloud_resources || [], <Cloud size={20} />, "Cloud Resources", "var(--primary-color)")}
      </div>
    </div>
  );
}
