import { useAegisQuery } from '../../api/hooks';
import { Building2, ShieldCheck, AlertTriangle } from 'lucide-react';

export default function BusinessUnits() {
  const { data: buRes, isLoading, error } = useAegisQuery<any>('/business-units');

  if (isLoading) return <div className="p-8 text-center card">Loading business unit data...</div>;
  if (error || !buRes) return <div className="p-8 text-center card text-error">Failed to load business units.</div>;

  const teams = buRes.data?.teams || [];
  
  // Sort by lowest security score first (highest risk)
  teams.sort((a: any, b: any) => a.security_score - b.security_score);

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Building2 className="text-primary" /> Business Units
          </h1>
          <p className="text-secondary mt-2">Security posture and accountability by team.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {teams.length > 0 ? teams.map((team: any, idx: number) => (
          <div key={idx} className="card flex flex-col justify-between hover:border-primary transition-colors">
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold truncate max-w-[70%]">{team.team}</h3>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${team.security_score >= 90 ? 'bg-success/20 text-success' : team.security_score >= 70 ? 'bg-warning/20 text-warning' : 'bg-danger/20 text-danger'}`}>
                  {team.security_score}
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between bg-tertiary p-3 rounded">
                  <span className="text-secondary font-bold text-sm">Monitored Assets</span>
                  <span className="font-mono font-bold">{team.asset_count}</span>
                </div>
                <div className="flex items-center justify-between bg-tertiary p-3 rounded">
                  <span className="text-secondary font-bold text-sm">Critical Assets</span>
                  <span className="font-mono font-bold">{team.critical_assets}</span>
                </div>
                <div className="flex items-center justify-between bg-tertiary p-3 rounded">
                  <span className="text-secondary font-bold text-sm">Open Recommendations</span>
                  <span className={`font-mono font-bold ${team.recommendations > 0 ? 'text-warning' : 'text-success'}`}>{team.recommendations}</span>
                </div>
              </div>
            </div>
            
            {team.recommendations > 0 && (
              <button className="btn-primary w-full mt-6 flex items-center justify-center gap-2">
                <AlertTriangle size={16} /> Remediate Team Issues
              </button>
            )}
            {team.recommendations === 0 && (
              <div className="mt-6 flex items-center justify-center gap-2 text-success font-bold text-sm p-2 bg-success/10 rounded border border-success/20">
                <ShieldCheck size={16} /> Fully Compliant
              </div>
            )}
          </div>
        )) : (
          <div className="col-span-3 text-center p-12 card text-secondary">
            No business units or ownership tags found in the current environment.
          </div>
        )}
      </div>
    </div>
  );
}
