import { useAegisQuery } from '../../api/hooks';
import { Activity, Clock, BoxSelect, Link } from 'lucide-react';

export default function Lifecycle() {
  const { data: res, isLoading, error } = useAegisQuery<any>('/lifecycle');

  if (isLoading) return <div className="p-8">Loading lifecycle intelligence...</div>;
  if (error || !res) return <div className="p-8 text-error">Failed to load lifecycle intelligence.</div>;

  const data = res.data;

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="text-primary" /> Asset Lifecycle Explorer
        </h1>
        <p className="text-secondary mt-2">Track newly discovered, dormant, and orphaned assets across the environment.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6 flex flex-col items-center justify-center text-center">
          <BoxSelect className="text-info mb-2" size={32} />
          <div className="text-3xl font-bold">{data.summary.total_assets}</div>
          <div className="text-sm text-secondary uppercase font-bold mt-1">Total Assets</div>
        </div>
        <div className="card p-6 flex flex-col items-center justify-center text-center">
          <Link className="text-warning mb-2" size={32} />
          <div className="text-3xl font-bold">{data.summary.orphaned_count}</div>
          <div className="text-sm text-secondary uppercase font-bold mt-1">Orphaned Assets</div>
        </div>
        <div className="card p-6 flex flex-col items-center justify-center text-center">
          <Clock className="text-secondary mb-2" size={32} />
          <div className="text-3xl font-bold">{data.summary.dormant_count}</div>
          <div className="text-sm text-secondary uppercase font-bold mt-1">Dormant Assets</div>
        </div>
      </div>

      <div className="space-y-6">
        <section>
          <h2 className="text-xl font-bold mb-4">Orphaned Assets</h2>
          <p className="text-sm text-secondary mb-4">Assets that exist in the environment but have no known relationships to other assets.</p>
          
          {data.orphaned.length === 0 ? (
            <div className="card bg-success/5 border-success/20 p-6 text-center text-success">
              No orphaned assets detected. All assets are mapped in the graph.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.orphaned.map((a: any, i: number) => (
                <div key={i} className="card p-4 hover:border-primary transition-colors">
                  <div className="text-xs font-bold text-secondary uppercase mb-1">{a.type}</div>
                  <div className="font-bold">{a.name}</div>
                  <div className="text-sm text-secondary font-mono mt-1">{a.id}</div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
