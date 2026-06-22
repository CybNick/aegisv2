import { useState } from 'react';
import { useTimeline } from '../../hooks/useTimeline';

export default function Timeline() {
  const { asOf, setAsOf } = useTimeline();
  const [inputVal, setInputVal] = useState(asOf);

  const apply = () => setAsOf(inputVal);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Timeline Controls</h1>
        <p className="page-description">Travel through time to view historical states of the graph.</p>
      </div>
      <div className="card">
        <h3>AS OF Selector</h3>
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
          <input 
            type="text" 
            value={inputVal} 
            onChange={e => setInputVal(e.target.value)}
            style={{ padding: '8px', background: 'var(--bg-input)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '4px', width: '300px' }}
            placeholder="Timestamp or 'now'"
          />
          <button onClick={apply} style={{ background: 'var(--accent-color)', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}>Apply Timestamp</button>
          <button onClick={() => { setInputVal('now'); setAsOf('now'); }} style={{ background: 'var(--bg-hover)', color: 'white', border: '1px solid var(--border-color)', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer' }}>Reset to Now</button>
        </div>
      </div>
    </div>
  );
}
