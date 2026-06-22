import { useAegisQuery } from '../../api/hooks';
import { Activity, Server, Clock, HardDrive, CheckCircle } from 'lucide-react';

export default function SystemHealth() {
  const { data: res, isLoading, error } = useAegisQuery<any>('/health', { refetchInterval: 5000 });

  if (isLoading) return <div className="p-8">Loading system diagnostics...</div>;
  if (error || !res) return <div className="p-8 text-error">Failed to load system diagnostics.</div>;

  const health = res.data;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="text-primary" /> System Health & Diagnostics
        </h1>
        <p className="text-secondary mt-2">Real-time status of all Aegis backend components.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg flex items-center gap-2"><Server className="text-primary" /> API Server</h3>
            <span className="badge badge-success">Online</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-secondary">Uptime:</span> <span>{Math.floor(health.uptime_seconds / 3600)}h {Math.floor((health.uptime_seconds % 3600) / 60)}m</span></div>
            <div className="flex justify-between"><span className="text-secondary">Status:</span> <span>{health.api?.status}</span></div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg flex items-center gap-2"><HardDrive className="text-primary" /> Storage Engine</h3>
            <span className="badge badge-success">Online</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-secondary">Data Dir:</span> <span className="font-mono text-xs">{health.storage?.data_dir}</span></div>
            <div className="flex justify-between"><span className="text-secondary">Mode:</span> <span>Append-Only</span></div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg flex items-center gap-2"><Clock className="text-primary" /> Monitoring</h3>
            <span className="badge badge-success">Active</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between"><span className="text-secondary">Status:</span> <span>{health.monitoring?.status}</span></div>
            <div className="flex justify-between"><span className="text-secondary">Detections:</span> <span>Online</span></div>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-bold text-xl mb-4">Connector Health</h3>
        <div className="space-y-3">
          {health.connectors?.active?.map((c: string) => (
            <div key={c} className="flex items-center justify-between p-3 bg-tertiary rounded border border-border">
              <span className="font-bold">{c}</span>
              <div className="flex items-center gap-2 text-success text-sm">
                <CheckCircle size={16} /> Healthy
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
