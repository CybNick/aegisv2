import { useAegisQuery } from '../../api/hooks';
import { ShieldAlert, AlertTriangle, Users } from 'lucide-react';

export default function Governance() {
  const { data: govRes, isLoading, error } = useAegisQuery<any>('/governance/findings');

  if (isLoading) return <div className="p-8 text-center card">Loading governance data...</div>;
  if (error || !govRes) return <div className="p-8 text-center card text-error">Failed to load governance findings.</div>;

  const findings = govRes.data?.findings || [];

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Users className="text-primary" /> Governance & Ownership
          </h1>
          <p className="text-secondary mt-2">Track ownership hygiene and systemic classification gaps.</p>
        </div>
        <div className="text-right">
          <div className="text-sm font-bold text-secondary uppercase tracking-wider mb-1">Open Findings</div>
          <div className="text-5xl font-bold text-primary">{findings.length}</div>
        </div>
      </div>

      <div className="space-y-4">
        {findings.length > 0 ? findings.map((f: any) => (
          <div key={f.id} className="card flex items-start gap-6 border border-border hover:border-primary/50 transition-colors">
            <div className="mt-1">
              {f.severity === 'CRITICAL' ? <ShieldAlert size={24} className="text-danger" /> : 
               f.severity === 'HIGH' ? <AlertTriangle size={24} className="text-warning" /> : 
               <AlertTriangle size={24} className="text-info" />}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <span className={`badge ${f.severity === 'CRITICAL' ? 'badge-primary' : 'badge-outline'}`}>{f.severity}</span>
                <span className="text-xs font-bold text-secondary uppercase tracking-wider">{f.category}</span>
              </div>
              <h3 className="text-xl font-bold mb-1">{f.title}</h3>
              <div className="text-sm text-secondary mb-4">
                Target: <span className="font-mono text-primary bg-primary/10 px-1 rounded">{f.target_name}</span> ({f.target_id})
              </div>
              
              <div className="bg-tertiary border border-border p-3 rounded">
                <div className="text-xs font-bold text-secondary uppercase mb-1">Required Action</div>
                <div className="font-medium">{f.action}</div>
              </div>
            </div>
          </div>
        )) : (
          <div className="card text-center p-12 text-success border-success/30">
            <ShieldAlert size={48} className="mx-auto mb-4" />
            <h3 className="text-xl font-bold">Perfect Hygiene</h3>
            <p>No unowned assets or unclassified production systems found.</p>
          </div>
        )}
      </div>
    </div>
  );
}
