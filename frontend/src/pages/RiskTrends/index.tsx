import { useAegisQuery } from '../../api/hooks';
import { TrendingUp, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

export default function RiskTrends() {
  const { data: trendRes, isLoading, error } = useAegisQuery<any>('/trends/risk');

  if (isLoading) return <div className="p-8 text-center card">Loading trend data...</div>;
  if (error || !trendRes) return <div className="p-8 text-center card text-error">Failed to load risk trends.</div>;

  const data = trendRes.data;
  const metrics = data.metrics;

  const renderTrendBox = (label: string, metricData: any) => {
    return (
      <div className="card text-center flex flex-col items-center justify-center py-10">
        <div className="text-sm font-bold text-secondary uppercase tracking-wider mb-2">{label}</div>
        <div className="text-5xl font-bold">{metricData?.total_risk?.toFixed(0) || 0}</div>
        <div className="text-sm text-secondary mt-2">{metricData?.critical_findings || 0} Critical Findings</div>
      </div>
    );
  };

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <TrendingUp className="text-primary" /> Risk Trends
          </h1>
          <p className="text-secondary mt-2">Temporal tracking of organizational risk.</p>
        </div>
        <div className="text-right">
          <div className="text-sm font-bold text-secondary uppercase tracking-wider mb-1">7-Day Trend</div>
          <div className={`text-5xl font-bold flex items-center gap-2 ${data.trend === 'INCREASING' ? 'text-danger' : data.trend === 'DECREASING' ? 'text-success' : 'text-info'}`}>
            {data.trend === 'INCREASING' ? <ArrowUpRight size={36} /> : data.trend === 'DECREASING' ? <ArrowDownRight size={36} /> : <Minus size={36} />}
            {data.trend === 'INCREASING' ? '+' : ''}{data.delta.toFixed(0)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {renderTrendBox("Current", metrics.current)}
        {renderTrendBox("Last Week", metrics.last_week)}
        {renderTrendBox("Last Month", metrics.last_month)}
        {renderTrendBox("Last Quarter", metrics.last_quarter)}
      </div>

      <div className="card p-8 text-center border-dashed border-2 border-border bg-tertiary">
        <h3 className="text-lg font-bold mb-2">Trend Chart Pipeline</h3>
        <p className="text-secondary">Aegis retains 100% of historical graph states deterministically. Time-series chart visualization will be plotted here using D3/Recharts based on the temporal snapshots.</p>
      </div>
    </div>
  );
}
