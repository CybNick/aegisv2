import { useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { ShieldCheck, TrendingUp, Target, AlertTriangle, Sparkles, Send } from 'lucide-react';

export default function ExecutiveHome() {
  const navigate = useNavigate();

  const { data: recsData } = useAegisQuery<any>('/recommendations/top');
  const { data: complianceData } = useAegisQuery<any>('/compliance');
  const { data: trendsData } = useAegisQuery<any>('/trends/risk');
  const { data: report } = useAegisQuery<any>('/reports/executive?format=json');

  // useAegisQuery returns the unwrapped payload; consume fields directly.
  const recommendations = recsData || [];
  const topCriticalCount = recommendations.filter((r: any) => r.severity === 'CRITICAL').length;
  const complianceScore = complianceData?.overall_score || 0;

  // Derive the 7-day risk trend from real metrics (current vs last_week) rather
  // than a non-existent precomputed field.
  const _metrics = trendsData?.metrics;
  const riskDelta = _metrics ? (_metrics.current.total_risk - _metrics.last_week.total_risk) : 0;
  const riskTrend = riskDelta > 0 ? 'INCREASING' : riskDelta < 0 ? 'DECREASING' : 'STABLE';
  
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          Executive Summary
        </h1>
        <p className="text-secondary mt-2">What you should worry about today.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Compliance Score */}
        <div className="card cursor-pointer hover:border-primary transition-colors" onClick={() => navigate('/compliance')}>
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheck className="text-success" />
            <span className="font-bold text-secondary uppercase tracking-wider text-xs">Compliance Score</span>
          </div>
          <div className="text-4xl font-bold">{complianceScore}%</div>
          <div className="text-sm text-secondary mt-2">Across 5 Frameworks</div>
        </div>

        {/* Critical Issues */}
        <div className="card cursor-pointer hover:border-primary transition-colors" onClick={() => navigate('/executive')}>
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle className="text-danger" />
            <span className="font-bold text-secondary uppercase tracking-wider text-xs">Critical Issues</span>
          </div>
          <div className="text-4xl font-bold">{topCriticalCount}</div>
          <div className="text-sm text-danger mt-2 font-medium">Requires immediate action</div>
        </div>

        {/* Risk Trend */}
        <div className="card cursor-pointer hover:border-primary transition-colors" onClick={() => navigate('/risk-trends')}>
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className={riskTrend === 'DECREASING' ? 'text-success' : riskTrend === 'INCREASING' ? 'text-danger' : 'text-info'} />
            <span className="font-bold text-secondary uppercase tracking-wider text-xs">Risk Trend (7d)</span>
          </div>
          <div className="text-4xl font-bold">{riskTrend === 'INCREASING' ? '+' : ''}{riskDelta.toFixed(0)}</div>
          <div className="text-sm text-secondary mt-2">Total Risk Score Delta</div>
        </div>

        {/* Total Assets */}
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <Target className="text-primary" />
            <span className="font-bold text-secondary uppercase tracking-wider text-xs">Monitored Assets</span>
          </div>
          <div className="text-4xl font-bold">{report?.total_assets || 0}</div>
          <div className="text-sm text-secondary mt-2">In current context</div>
        </div>
      </div>

      {/* Recommended Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-4">Top Recommendations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {recommendations.length > 0 ? recommendations.slice(0, 3).map((rec: any) => (
            <div key={rec.id} className="card flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span className={`badge ${rec.severity === 'CRITICAL' ? 'badge-primary' : 'badge-outline'}`}>{rec.severity}</span>
                  <span className="text-xs text-secondary font-bold uppercase tracking-wider">{rec.category}</span>
                </div>
                <h4 className="font-bold text-lg mb-2">{rec.title}</h4>
                <p className="text-sm text-secondary line-clamp-3">{rec.description}</p>
              </div>
              <button className="btn-primary mt-6 w-full" onClick={() => navigate('/recommendations')}>Review & Fix</button>
            </div>
          )) : (
            <div className="col-span-3 card text-center p-8 text-success border-success/30">
              <ShieldCheck size={48} className="mx-auto mb-4" />
              <h3 className="text-xl font-bold">All Clear</h3>
              <p>No critical or high recommendations at this time.</p>
            </div>
          )}
        </div>
      </div>
      
      {/* Ask Aegis AI Widget */}
      <div className="mb-8 card bg-primary/5 border border-primary/20">
        <div className="flex items-center gap-3 mb-4">
          <Sparkles className="text-primary" />
          <h2 className="text-xl font-bold">Ask Aegis AI</h2>
        </div>
        <p className="text-secondary text-sm mb-4">Get natural language answers derived directly from the current graph view.</p>
        
        <div className="flex items-center gap-4">
          <input 
            type="text" 
            placeholder="e.g. What is my highest risk? or Are we compliant?"
            className="flex-1 bg-tertiary border border-border outline-none px-4 py-3 rounded-lg focus:border-primary transition-colors"
            onKeyDown={e => {
              if (e.key === 'Enter') {
                navigate('/assistant');
              }
            }}
          />
          <button 
            className="btn-primary p-3 px-6 flex items-center gap-2"
            onClick={() => navigate('/assistant')}
          >
            <Send size={18} /> Ask
          </button>
        </div>
        
        <div className="flex items-center gap-3 mt-4 flex-wrap">
          <span className="text-xs text-secondary font-bold uppercase">Try asking:</span>
          <button className="badge badge-outline hover:border-primary hover:text-primary cursor-pointer transition-colors" onClick={() => navigate('/assistant')}>How secure are we?</button>
          <button className="badge badge-outline hover:border-primary hover:text-primary cursor-pointer transition-colors" onClick={() => navigate('/assistant')}>What should leadership prioritize?</button>
          <button className="badge badge-outline hover:border-primary hover:text-primary cursor-pointer transition-colors" onClick={() => navigate('/assistant')}>What teams have the most risk?</button>
        </div>
      </div>
    </div>
  );
}
