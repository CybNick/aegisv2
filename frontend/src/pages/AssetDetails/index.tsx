import { useParams, Link } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { Server, ShieldAlert, Lock, User, Target, ChevronRight } from 'lucide-react';

export default function AssetDetails() {
  const { id } = useParams<{ id: string }>();
  
  const { data: detailResponse, isLoading, error } = useAegisQuery<any>(`/assets/${id}`);
  
  if (isLoading) return <div className="p-8 text-center">Loading asset context...</div>;
  if (error || !detailResponse?.data) return <div className="p-8 text-center text-error">Failed to load asset details.</div>;

  const asset = detailResponse.data;
  const attr = asset.attributes || {};

  return (
    <div className="p-8">
      <div className="mb-6">
        <div className="flex items-center text-sm text-secondary mb-2">
          <Link to="/assets" className="hover:text-primary">Asset Inventory</Link>
          <ChevronRight size={14} className="mx-1" />
          <span className="truncate">{asset.id}</span>
        </div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Server className="text-primary" /> {asset.name}
        </h1>
        <div className="flex gap-2 mt-3">
          <span className="badge badge-outline">{asset.type}</span>
          <span className={`badge ${asset.environment === 'Production' ? 'badge-primary' : 'badge-outline'}`}>
            {asset.environment}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Business Context Card */}
        <div className="card">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <Target className="text-primary" /> Business Context
          </h2>
          
          <div className="space-y-4">
            <div>
              <div className="text-sm text-secondary mb-1">Criticality</div>
              <div className="flex items-center gap-2 text-lg font-bold" style={{ color: `var(--${asset.criticality?.level === 'Critical' || asset.criticality?.level === 'High' ? 'danger' : 'warning'}-color)` }}>
                {asset.criticality?.level !== 'Low' && <ShieldAlert size={18} />}
                {asset.criticality?.level} (Score: {asset.criticality?.score})
              </div>
              <ul className="mt-2 text-sm text-secondary space-y-1">
                {asset.criticality?.factors?.map((f: string, i: number) => <li key={i}>• {f}</li>)}
              </ul>
            </div>
            
            <hr className="border-border" />
            
            <div>
              <div className="text-sm text-secondary mb-1">Data Sensitivity</div>
              <div className="flex items-center gap-2 text-lg font-bold">
                <Lock size={18} className="text-warning" /> {asset.sensitivity}
              </div>
            </div>
          </div>
        </div>

        {/* Ownership Card */}
        <div className="card">
          <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
            <User className="text-primary" /> Ownership Details
          </h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-tertiary p-3 rounded border border-border">
              <div className="text-xs text-secondary uppercase tracking-wider mb-1">Team Owner</div>
              <div className="font-mono">{asset.ownership?.team || 'Unassigned'}</div>
            </div>
            <div className="bg-tertiary p-3 rounded border border-border">
              <div className="text-xs text-secondary uppercase tracking-wider mb-1">Technical Owner</div>
              <div className="font-mono">{asset.ownership?.technical || 'Unassigned'}</div>
            </div>
            <div className="bg-tertiary p-3 rounded border border-border">
              <div className="text-xs text-secondary uppercase tracking-wider mb-1">Business Owner</div>
              <div className="font-mono">{asset.ownership?.business || 'Unassigned'}</div>
            </div>
          </div>
        </div>
        
        {/* Raw Attributes */}
        <div className="card lg:col-span-2">
          <h2 className="text-xl font-bold mb-4">Node Attributes</h2>
          <pre className="bg-tertiary p-4 rounded text-xs font-mono overflow-auto max-h-64 border border-border text-secondary">
            {JSON.stringify(attr, null, 2)}
          </pre>
        </div>

      </div>
    </div>
  );
}
