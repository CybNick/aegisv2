import { useState } from 'react';
import { useAegisQuery } from '../../api/hooks';
import { ShieldCheck, ShieldAlert, ChevronDown, ChevronRight, XCircle, CheckCircle } from 'lucide-react';

export default function Compliance() {
  const { data: complianceRes, isLoading, error } = useAegisQuery<any>('/compliance');
  const [expandedFramework, setExpandedFramework] = useState<string | null>(null);

  if (isLoading) return <div className="p-8 text-center card">Loading compliance data...</div>;
  if (error || !complianceRes) return <div className="p-8 text-center card text-error">Failed to load compliance data.</div>;

  const data = complianceRes.data;
  const frameworks = data?.frameworks || {};

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <ShieldCheck className="text-primary" /> Compliance Explorer
          </h1>
          <p className="text-secondary mt-2">Continuous compliance tracking across industry frameworks.</p>
        </div>
        <div className="text-right">
          <div className="text-sm font-bold text-secondary uppercase tracking-wider mb-1">Overall Score</div>
          <div className="text-5xl font-bold text-primary">{data.overall_score}%</div>
        </div>
      </div>

      <div className="space-y-6">
        {Object.entries(frameworks).map(([fwName, fwData]: [string, any]) => (
          <div key={fwName} className="card p-0 overflow-hidden border border-border">
            <div 
              className="p-6 flex items-center justify-between cursor-pointer hover:bg-secondary/5 transition-colors border-b border-border"
              onClick={() => setExpandedFramework(expandedFramework === fwName ? null : fwName)}
            >
              <div className="flex items-center gap-6">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold ${fwData.score >= 80 ? 'bg-success/10 text-success' : fwData.score >= 50 ? 'bg-warning/10 text-warning' : 'bg-danger/10 text-danger'}`}>
                  {fwData.score}%
                </div>
                <div>
                  <h3 className="text-2xl font-bold">{fwName}</h3>
                  <div className="flex items-center gap-4 mt-2 text-sm text-secondary">
                    <span className="flex items-center gap-1"><CheckCircle size={14} className="text-success" /> {fwData.passed_controls.length} Passed</span>
                    <span className="flex items-center gap-1"><XCircle size={14} className="text-danger" /> {fwData.failed_controls.length} Failed</span>
                  </div>
                </div>
              </div>
              <div>
                {expandedFramework === fwName ? <ChevronDown size={24} className="text-secondary" /> : <ChevronRight size={24} className="text-secondary" />}
              </div>
            </div>

            {expandedFramework === fwName && (
              <div className="p-6 bg-tertiary">
                <h4 className="font-bold mb-4 flex items-center gap-2"><ShieldAlert className="text-danger" size={18} /> Failed Controls</h4>
                {fwData.failed_controls.length > 0 ? (
                  <div className="space-y-4">
                    {fwData.failed_controls.map((fc: any, i: number) => (
                      <div key={i} className="bg-primary/5 border border-primary/20 rounded p-4">
                        <div className="flex items-start gap-4">
                          <div className="bg-danger/20 text-danger px-2 py-1 rounded text-xs font-bold border border-danger/30 whitespace-nowrap">
                            {fc.control.id}
                          </div>
                          <div>
                            <h5 className="font-bold text-md">{fc.control.title}</h5>
                            <p className="text-sm text-secondary mt-1">{fc.control.description}</p>
                            <div className="mt-3 bg-danger/5 border border-danger/20 p-3 rounded text-sm flex flex-col gap-2">
                              <div className="font-bold text-danger text-xs uppercase">Evidence</div>
                              <div>{fc.reason}</div>
                              {fc.evidence_nodes && fc.evidence_nodes.length > 0 && (
                                <div className="text-xs font-mono text-secondary">Nodes: {fc.evidence_nodes.join(', ')}</div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-success flex items-center gap-2 font-medium">
                    <CheckCircle size={18} /> No failed controls in {fwName}.
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
