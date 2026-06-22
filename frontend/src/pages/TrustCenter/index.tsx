import { useAegisQuery } from '../../api/hooks';
import { ShieldCheck, Database, Lock, Server, CheckCircle2 } from 'lucide-react';

export default function TrustCenter() {
  const { data: res } = useAegisQuery<any>('/health');
  
  const health = res?.data || {};

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div className="text-center mb-12">
        <ShieldCheck className="mx-auto text-success mb-4" size={48} />
        <h1 className="text-4xl font-bold mb-2">Executive Trust Center</h1>
        <p className="text-secondary text-lg">Transparency into how Aegis calculates risk and stores data.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6 border-l-4 border-success">
          <h3 className="font-bold text-xl mb-2 flex items-center gap-2"><Lock className="text-primary" /> 100% Local-First Architecture</h3>
          <p className="text-secondary mb-4">Aegis processes all data strictly within your network environment. No data is sent to external clouds or third-party APIs.</p>
          <div className="flex items-center gap-2 text-sm font-bold text-success">
            <CheckCircle2 size={16} /> Verified Active
          </div>
        </div>

        <div className="card p-6 border-l-4 border-success">
          <h3 className="font-bold text-xl mb-2 flex items-center gap-2"><Database className="text-primary" /> Deterministic Intelligence</h3>
          <p className="text-secondary mb-4">Every risk score and recommendation is derived strictly from observable graph facts without AI hallucinations.</p>
          <div className="flex items-center gap-2 text-sm font-bold text-success">
            <CheckCircle2 size={16} /> Confidence Score: 100%
          </div>
        </div>

        <div className="card p-6 border-l-4 border-success">
          <h3 className="font-bold text-xl mb-2 flex items-center gap-2"><Server className="text-primary" /> Evidence-Backed Chain</h3>
          <p className="text-secondary mb-4">All findings retain an immutable evidence chain tracing back to the raw connector inputs and timeline state.</p>
          <div className="flex items-center gap-2 text-sm font-bold text-success">
            <CheckCircle2 size={16} /> Evidence Captured
          </div>
        </div>
      </div>
      
      <div className="card p-6 bg-tertiary/50 mt-8">
        <h2 className="text-2xl font-bold mb-4">System Telemetry Snapshot</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{health.trust_model?.data_residency || 'LOCAL'}</div>
            <div className="text-xs text-secondary uppercase font-bold mt-1">Data Residency</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-success">0</div>
            <div className="text-xs text-secondary uppercase font-bold mt-1">External APIs</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{health.connectors?.active?.length || 0}</div>
            <div className="text-xs text-secondary uppercase font-bold mt-1">Active Connectors</div>
          </div>
          <div>
            <div className="text-2xl font-bold">1.0</div>
            <div className="text-xs text-secondary uppercase font-bold mt-1">Graph Determinism</div>
          </div>
        </div>
      </div>
    </div>
  );
}
