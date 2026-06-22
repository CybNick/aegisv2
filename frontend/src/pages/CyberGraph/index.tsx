import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { Core } from 'cytoscape';
import { useAegisQuery } from '../../api/hooks';
import { Search, Crosshair } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './CyberGraph.css';

export default function CyberGraph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [centerNode, setCenterNode] = useState<string>(''); // resolved from real graph data
  const [depth, setDepth] = useState(2);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  // Resolve a real center node from the live graph instead of a hardcoded id.
  const { data: nodeListData } = useAegisQuery<any>('/graph/nodes?limit=50', {
    refetchInterval: false,
    enabled: !centerNode,
  });
  useEffect(() => {
    if (centerNode) return;
    const list = nodeListData;
    const first = Array.isArray(list) ? list[0] : list?.nodes?.[0];
    if (first?.id) setCenterNode(first.id);
  }, [nodeListData, centerNode]);

  const { data: subgraphData, isLoading } = useAegisQuery<any>(`/graph/subgraph?center_node=${encodeURIComponent(centerNode)}&depth=${depth}&limit=500`, {
    refetchInterval: false,
    enabled: !!centerNode
  });
  
  const { data: searchResults } = useAegisQuery<any[]>(`/intelligence/search?q=${searchQuery}`, {
    enabled: searchQuery.length > 2,
    refetchInterval: false
  });
  
  // Also get risk for selected node
  const { data: riskData } = useAegisQuery<any>(`/intelligence/risk/${selectedNode}`, {
    enabled: !!selectedNode,
    refetchInterval: false
  });

  useEffect(() => {
    if (!containerRef.current || !subgraphData) return;

    const { nodes, edges } = subgraphData;

    const cyElements = [
      ...nodes.map((n: any) => ({
        data: { id: n.id, label: n.properties?.name || n.id, type: n.type }
      })),
      ...edges.map((e: any) => ({
        data: { id: e.id, source: e.source, target: e.target, label: e.type }
      }))
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements: cyElements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)',
            'color': '#fff',
            'font-size': '12px',
            'text-valign': 'bottom',
            'text-margin-y': 5
          }
        },
        {
          selector: 'node[type = "ASSET"]',
          style: { 'background-color': '#3b82f6' }
        },
        {
          selector: 'node[type = "SERVICE"]',
          style: { 'background-color': '#8b5cf6' }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#fbbf24'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#4b5563',
            'target-arrow-color': '#4b5563',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'color': '#9ca3af',
            'text-rotation': 'autorotate'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false
      }
    });

    cy.on('tap', 'node', (evt) => {
      setSelectedNode(evt.target.id());
    });
    
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [subgraphData]);

  // Center node from search
  const handleResultClick = (id: string) => {
    setCenterNode(id);
    setSelectedNode(id);
    setSearchQuery('');
  };

  const handleExpand = () => {
    setDepth(d => d + 1);
  };

  const selectedNodeInfo = selectedNode && subgraphData?.nodes
    ? subgraphData.nodes.find((n: any) => n.id === selectedNode)
    : null;

  return (
    <div className="cyber-graph-page">
      <div className="graph-toolbar">
        <div className="search-bar">
          <Search size={18} />
          <input 
            type="text" 
            placeholder="Search nodes..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchResults && searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map(res => (
                <div key={res.id} className="search-result-item" onClick={() => handleResultClick(res.id)}>
                  <strong>{res.value?.name || res.id}</strong> <small>({res.type})</small>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="toolbar-actions">
          <button className="btn-outline text-xs px-2" onClick={handleExpand}>+ Expand Depth ({depth})</button>
          <button onClick={() => cyRef.current?.fit()}><Crosshair size={18} /> Fit Graph</button>
        </div>
      </div>
      
      <div className="graph-container-wrapper">
        {isLoading && <div className="absolute inset-0 z-10 bg-background/50 flex items-center justify-center">Loading Subgraph...</div>}
        <div ref={containerRef} className="cytoscape-container" />
        
        {selectedNodeInfo && (
          <div className="node-details-panel">
            <h3>{selectedNodeInfo.properties?.name || selectedNode}</h3>
            <p className="node-type">{selectedNodeInfo.type}</p>
            
            <div className="detail-section">
              <h4>Properties</h4>
              <ul>
                {Object.entries(selectedNodeInfo.properties || {}).map(([k, v]) => (
                  <li key={k}><strong>{k}:</strong> {String(v)}</li>
                ))}
              </ul>
            </div>
            
            <div className="detail-section">
              <h4>Risk Intelligence</h4>
              {riskData ? (
                <div>
                  <div className={`risk-badge risk-${riskData.category.toLowerCase()}`}>
                    {riskData.category} ({riskData.score})
                  </div>
                </div>
              ) : (
                <p>Loading risk...</p>
              )}
            </div>

            <div className="detail-section actions">
              <h4>Actions</h4>
              <button onClick={() => navigate(`/dependencies?node=${selectedNode}`)}>View Dependencies</button>
              <button onClick={() => navigate(`/risk?node=${selectedNode}`)}>View Risk Factors</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
