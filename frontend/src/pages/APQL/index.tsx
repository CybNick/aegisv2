import { useState, useEffect } from 'react';
import { Play, Trash2, Save, Clock, Search, ExternalLink } from 'lucide-react';
import { api } from '../../api/client';
import { useTimeline } from '../../hooks/useTimeline';
import { useNavigate } from 'react-router-dom';
import './APQL.css';

export default function APQLWorkspace() {
  const navigate = useNavigate();
  const { asOf } = useTimeline();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [history, setHistory] = useState<string[]>([]);
  const [saved, setSaved] = useState<string[]>([]);

  useEffect(() => {
    const h = localStorage.getItem('apql_history');
    if (h) setHistory(JSON.parse(h));
    
    const s = localStorage.getItem('apql_saved');
    if (s) setSaved(JSON.parse(s));
  }, []);

  const saveToHistory = (q: string) => {
    const h = [q, ...history.filter(x => x !== q)].slice(0, 20);
    setHistory(h);
    localStorage.setItem('apql_history', JSON.stringify(h));
  };

  const handleSave = () => {
    if (!query.trim()) return;
    if (saved.includes(query)) return;
    const s = [...saved, query];
    setSaved(s);
    localStorage.setItem('apql_saved', JSON.stringify(s));
  };

  const handleDeleteSaved = (q: string) => {
    const s = saved.filter(x => x !== q);
    setSaved(s);
    localStorage.setItem('apql_saved', JSON.stringify(s));
  };

  const executeQuery = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await api.post<any>('/apql/query', { query: q }, { as_of: asOf });
      if (res.success) {
        setResults(res.data.results);
        saveToHistory(q);
      } else {
        setError(res.message);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute query');
    } finally {
      setLoading(false);
    }
  };

  const handleRun = () => {
    executeQuery(query);
  };

  const viewInGraph = (id: string) => {
    navigate(`/graph?search=${encodeURIComponent(id)}`);
  };

  return (
    <div className="apql-workspace">
      <div className="apql-main">
        <div className="page-header">
          <h1 className="page-title"><Search size={24} /> APQL Workspace</h1>
          <p className="page-description">Execute read-only queries against the temporal graph.</p>
        </div>

        <div className="card query-editor-container">
          <textarea
            className="query-editor"
            placeholder="FIND ASSETS&#10;WHERE exposure = internet&#10;ORDER BY risk DESC"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            spellCheck={false}
          />
          <div className="query-actions">
            <button className="btn btn-secondary" onClick={() => setQuery('')}>
              Clear
            </button>
            <button className="btn btn-secondary" onClick={handleSave}>
              <Save size={16} /> Save
            </button>
            <button className="btn btn-primary" onClick={handleRun} disabled={loading || !query.trim()}>
              <Play size={16} /> {loading ? 'Running...' : 'Run Query'}
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-error mt-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        {results !== null && (
          <div className="card results-container mt-4">
            <div className="results-header">
              <h3>Results ({results.length})</h3>
            </div>
            <div className="table-responsive">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Type</th>
                    <th>Confidence</th>
                    <th>Risk</th>
                    <th>Criticality</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((r, i) => (
                    <tr key={r.id + i}>
                      <td className="font-mono">{r.id.substring(0, 16)}...</td>
                      <td><span className="badge">{r.type}</span></td>
                      <td>{(r.confidence * 100).toFixed(0)}%</td>
                      <td>{r.attributes?.risk || '-'}</td>
                      <td>{r.attributes?.criticality || '-'}</td>
                      <td>
                        <button className="btn-icon" title="View in Graph" onClick={() => viewInGraph(r.id)}>
                          <ExternalLink size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {results.length === 0 && (
                    <tr>
                      <td colSpan={6} className="text-center text-muted">No results found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="apql-sidebar">
        <div className="card">
          <h3 className="flex items-center gap-2 mb-3"><Save size={16} /> Saved Queries</h3>
          {saved.length === 0 ? (
            <p className="text-muted text-sm">No saved queries.</p>
          ) : (
            <ul className="query-list">
              {saved.map((q, i) => (
                <li key={i} className="query-item">
                  <div className="query-text" onClick={() => { setQuery(q); executeQuery(q); }}>
                    {q}
                  </div>
                  <button className="btn-icon text-danger" onClick={() => handleDeleteSaved(q)}>
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card mt-4">
          <h3 className="flex items-center gap-2 mb-3"><Clock size={16} /> History</h3>
          {history.length === 0 ? (
            <p className="text-muted text-sm">No history yet.</p>
          ) : (
            <ul className="query-list">
              {history.map((q, i) => (
                <li key={i} className="query-item" onClick={() => { setQuery(q); executeQuery(q); }}>
                  <div className="query-text text-muted">{q}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
