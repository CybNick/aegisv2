import { useSearchParams } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { Search, Target, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function SearchResults() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  
  const { data: res, isLoading, error } = useAegisQuery<any>(`/search?q=${encodeURIComponent(query)}`);

  if (!query) return <div className="p-8">Enter a search term.</div>;
  if (isLoading) return <div className="p-8 text-center card">Searching for "{query}"...</div>;
  if (error || !res) return <div className="p-8 text-center card text-error">Failed to load search results.</div>;

  const data = res.data;
  const assets = data.assets || [];
  const recs = data.recommendations || [];
  const comp = data.compliance || [];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Search className="text-primary" /> Search Results for "{query}"
        </h1>
        <p className="text-secondary mt-2">Found {assets.length} assets, {recs.length} recommendations, {comp.length} compliance findings.</p>
      </div>

      <div className="space-y-8">
        {/* Assets */}
        {assets.length > 0 && (
          <section>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Target className="text-info" /> Assets</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {assets.map((a: any, i: number) => (
                <div key={i} className="card p-4 hover:border-primary transition-colors">
                  <div className="text-xs font-bold text-secondary uppercase mb-1">{a.type}</div>
                  <div className="font-bold">{a.name}</div>
                  <div className="text-sm text-secondary font-mono mt-1">{a.id}</div>
                  {a.match_field && (
                    <div className="text-xs bg-primary/10 text-primary p-1 px-2 rounded inline-block mt-2">Matched: {a.match_field}</div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Recommendations */}
        {recs.length > 0 && (
          <section>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><AlertTriangle className="text-warning" /> Recommendations</h2>
            <div className="space-y-4">
              {recs.map((r: any, i: number) => (
                <div key={i} className="card p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`badge ${r.severity === 'CRITICAL' ? 'badge-primary' : 'badge-outline'}`}>{r.severity}</span>
                    <span className="font-bold">{r.title}</span>
                  </div>
                  <p className="text-sm text-secondary">{r.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Compliance */}
        {comp.length > 0 && (
          <section>
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><ShieldCheck className="text-success" /> Compliance</h2>
            <div className="space-y-4">
              {comp.map((c: any, i: number) => (
                <div key={i} className="card p-4 flex items-center justify-between">
                  <div>
                    <div className="font-bold text-lg">{c.framework}</div>
                    {c.control && <div className="text-sm text-secondary mt-1">{c.control} - {c.title}</div>}
                  </div>
                  {c.score !== undefined && (
                    <div className="text-2xl font-bold text-primary">{c.score}%</div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {assets.length === 0 && recs.length === 0 && comp.length === 0 && (
          <div className="card text-center p-12 text-secondary">
            No results found for "{query}". Try a different term.
          </div>
        )}
      </div>
    </div>
  );
}
