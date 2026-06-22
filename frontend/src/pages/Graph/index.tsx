import { useEffect, useRef, useState } from 'react';
import { useAegisQuery } from '../../api/hooks';
import cytoscape from 'cytoscape';
import { Search, X } from 'lucide-react';
import './Graph.css';

export default function GraphExplorer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<Record<string, boolean>>({
    asset: true, service: true, identity: true, datastore: true, zone: true
  });
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  
  const { data: nodes } = useAegisQuery<any>('/graph/nodes');
  const { data: edges } = useAegisQuery<any>('/graph/edges');

  useEffect(() => {
    if (!containerRef.current || !nodes || !edges) return;
    
    const elements = [];
    
    // Process nodes
    for (const [id, state] of Object.entries(nodes)) {
      const n = (state as any).state;
      if (!filters[n.kind]) continue;
      elements.push({
        data: {
          id,
          label: n.kind === 'asset' ? n.attributes?.hostname || id.substring(0,6) : 
                 n.kind === 'service' ? `Port ${n.attributes?.port}` : 
                 n.kind === 'zone' ? n.attributes?.name : id.substring(0, 6),
          type: n.kind,
          raw: state
        }
      });
    }
    
    // Process edges
    for (const [id, state] of Object.entries(edges)) {
      const e = (state as any).state;
      // Only include edge if both source and target are in the current filter
      if (!nodes[e.source_id] || !nodes[e.target_id]) continue;
      const sKind = nodes[e.source_id].state.kind;
      const tKind = nodes[e.target_id].state.kind;
      if (!filters[sKind] || !filters[tKind]) continue;

      elements.push({
        data: {
          id,
          source: e.source_id,
          target: e.target_id,
          label: e.kind,
          raw: state
        }
      });
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)',
            'color': '#f4f4f5',
            'text-valign': 'bottom',
            'text-margin-y': 5 as any,
            'font-size': '10px'
          }
        },
        {
          selector: 'node[type="zone"]',
          style: { 'background-color': '#8b5cf6', 'shape': 'hexagon' }
        },
        {
          selector: 'node[type="asset"]',
          style: { 'background-color': '#3b82f6', 'shape': 'rectangle' }
        },
        {
          selector: 'node[type="service"]',
          style: { 'background-color': '#10b981', 'shape': 'ellipse' }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#3f3f46',
            'target-arrow-color': '#3f3f46',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'color': '#a1a1aa',
            'text-rotation': 'autorotate' as any
          }
        },
        {
          selector: 'node.highlight',
          style: {
            'border-width': 4,
            'border-color': '#fde047',
            'border-opacity': 1
          }
        },
        {
          selector: 'node.selected',
          style: {
            'border-width': 4,
            'border-color': '#fff',
            'border-opacity': 1
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false
      }
    });

    cy.on('tap', 'node', (e) => {
      cy.nodes().removeClass('selected');
      e.target.addClass('selected');
      setSelectedNode(e.target.data());
    });

    cy.on('tap', (e) => {
      if (e.target === cy) {
        cy.nodes().removeClass('selected');
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [nodes, edges, filters]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.nodes().removeClass('highlight');
    if (search.trim()) {
      const term = search.toLowerCase();
      cy.nodes().filter(n => {
        const d = n.data();
        return d.id.toLowerCase().includes(term) || (d.label && d.label.toLowerCase().includes(term));
      }).addClass('highlight');
    }
  }, [search]);

  const toggleFilter = (type: string) => {
    setFilters(prev => ({ ...prev, [type]: !prev[type] }));
  };

  return (
    <div className="graph-page">
      <div className="graph-header">
        <div>
          <h1 className="page-title">Graph Explorer</h1>
          <p className="page-description">Visual topology view of the environment.</p>
        </div>
        <div className="graph-controls">
          <div className="search-box">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search nodes by ID or label..." 
              value={search} 
              onChange={e => setSearch(e.target.value)} 
            />
          </div>
          <div className="filters">
            {Object.keys(filters).map(f => (
              <button 
                key={f} 
                className={`filter-btn ${filters[f] ? 'active' : ''}`}
                onClick={() => toggleFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div className="graph-content">
        <div className="card graph-container">
          <div ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '600px' }} />
        </div>
        {selectedNode && (
          <div className="details-panel card">
            <div className="details-header">
              <h3>Node Details</h3>
              <button className="btn-icon" onClick={() => setSelectedNode(null)}><X size={16} /></button>
            </div>
            <div className="details-body">
              <div className="detail-item">
                <span className="label">ID:</span>
                <span className="value">{selectedNode.id}</span>
              </div>
              <div className="detail-item">
                <span className="label">Type:</span>
                <span className="value badge">{selectedNode.type}</span>
              </div>
              <div className="detail-item">
                <span className="label">Confidence:</span>
                <span className="value">{((selectedNode.raw?.confidence || 1) * 100).toFixed(0)}%</span>
              </div>
              <div className="detail-section">
                <h4>Attributes</h4>
                <pre>{JSON.stringify(selectedNode.raw?.state?.attributes, null, 2)}</pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
