import { useNavigate } from 'react-router-dom';
import { Shield, Server, Box, Activity, ShieldAlert, ArrowRight, CheckCircle, Cloud, AlertTriangle, AlertCircle } from 'lucide-react';
import { useAegisQuery } from '../../api/hooks';
import { useMode } from '../../hooks/useMode';
import './Home.css';

export default function Home() {
  const navigate = useNavigate();
  const { setMode } = useMode();

  // Fetch status and scan history
  const { data: statusData } = useAegisQuery<any>('/system/status', { refetchInterval: 10000 });
  const { data: historyData } = useAegisQuery<any[]>('/scans/history');

  // Fetch exposure & intelligence
  const { data: exposureData } = useAegisQuery<any>('/intelligence/exposure', { enabled: !!historyData && historyData.length > 0 });
  const { data: inventoryData } = useAegisQuery<any>('/assets/inventory', { enabled: !!historyData && historyData.length > 0 });
  const { data: recsData } = useAegisQuery<any>('/recommendations/top', { enabled: !!historyData && historyData.length > 0 });

  const nodes = statusData?.subsystems?.graph?.nodes || 0;
  const assetsCount = inventoryData ? inventoryData.length : 0;
  const servicesCount = Math.max(0, nodes - assetsCount);
  
  const hasScans = historyData && historyData.length > 0;
  // useAegisQuery already unwraps the envelope's `data`; these endpoints return a
  // list directly, so consume it as-is (no extra `.data`).
  const recommendations = recsData || [];
  const topCriticalCount = recommendations.filter((r: any) => r.severity === 'CRITICAL').length;
  const internetExposed = exposureData?.internet_reachable_assets?.length || 0;

  const assets = inventoryData || [];
  const prodAssetsCount = assets.filter((a: any) => a.environment === 'Production').length;
  const customerServicesCount = exposureData?.internet_reachable_services?.length || 0;

  const navigateToDashboard = () => {
    setMode('professional');
    navigate('/dashboard');
  };

  // FTUX View
  if (historyData !== undefined && !hasScans) {
    return (
      <div className="home-container">
        <div className="ftux-card">
          <div className="ftux-icon-wrapper"><Shield size={48} /></div>
          <h1>Welcome to Aegis</h1>
          <p className="ftux-subtitle">Your infrastructure intelligence center.</p>
          
          <div className="ftux-steps">
            <div className="ftux-step">
              <div className="ftux-step-num">1</div>
              <div>
                <h3>Scan your network</h3>
                <p>Discover assets securely without complex configuration.</p>
              </div>
            </div>
            <div className="ftux-step">
              <div className="ftux-step-num">2</div>
              <div>
                <h3>Review findings</h3>
                <p>Understand your security posture and exposed risks.</p>
              </div>
            </div>
            <div className="ftux-step">
              <div className="ftux-step-num">3</div>
              <div>
                <h3>Monitor changes</h3>
                <p>Track how your environment evolves over time.</p>
              </div>
            </div>
          </div>

          <div className="flex gap-4 mt-6">
            <button className="btn-primary ftux-btn" onClick={() => navigate('/scan-center')}>
              Start First Scan <ArrowRight size={18} />
            </button>
            <button className="btn-secondary ftux-btn" onClick={() => navigate('/connectors/wizard')}>
              Connect Cloud <Cloud size={18} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Dashboard View (Outcomes)
  return (
    <div className="home-container">
      <header className="home-header">
        <h1>Overview</h1>
        <p>A simple summary of your environment's health.</p>
      </header>

      {/* Main Score & Metrics */}
      <div className="metrics-grid">
        <div className="metric-card security-score">
          <div className="metric-icon"><Shield size={24} /></div>
          <div className="metric-content">
            <span className="metric-label">Security Score</span>
            <span className="metric-value">{statusData?.subsystems?.intelligence?.health === 'healthy' ? 'A' : 'TBD'}</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon"><Server size={24} /></div>
          <div className="metric-content">
            <span className="metric-label">Assets</span>
            <span className="metric-value">{assetsCount}</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon"><Box size={24} /></div>
          <div className="metric-content">
            <span className="metric-label">Services</span>
            <span className="metric-value">{servicesCount}</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon"><ShieldAlert size={24} className="text-warning" /></div>
          <div className="metric-content">
            <span className="metric-label">Risks</span>
            <span className="metric-value">{topCriticalCount}</span>
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-icon"><Activity size={24} /></div>
          <div className="metric-content">
            <span className="metric-label">Exposed</span>
            <span className="metric-value">{internetExposed}</span>
          </div>
        </div>
      </div>

      <div className="outcomes-grid">
        {/* Recent Discoveries & Exposure */}
        <div className="outcome-card">
          <div className="outcome-header">
            <h3>Exposure Overview</h3>
            <button className="btn-link" onClick={() => navigate('/scan-center')}>Scan Again</button>
          </div>
          <ul className="outcome-list">
            <li>
              <div className="outcome-icon"><CheckCircle size={16} className="text-success" /></div>
              <span><strong>{customerServicesCount} customer-facing services</strong> are internet accessible.</span>
            </li>
            <li>
              <div className="outcome-icon"><Server size={16} className="text-info" /></div>
              <span><strong>{prodAssetsCount} assets</strong> classified as Production.</span>
            </li>
            <li>
              <div className="outcome-icon"><ShieldAlert size={16} className="text-warning" /></div>
              <span><strong>{exposureData?.exposed_datastores?.length || 0} sensitive databases</strong> exposed.</span>
            </li>
          </ul>
        </div>

        {/* Top Issues */}
        <div className="outcome-card">
          <div className="outcome-header">
            <h3>Top Issues</h3>
            <button className="btn-link" onClick={navigateToDashboard}>View All</button>
          </div>
          <ul className="outcome-list">
            {recommendations.length > 0 ? recommendations.map((rec: any) => (
              <li key={rec.id}>
                <div className="outcome-icon">
                  {rec.severity === 'CRITICAL' ? <ShieldAlert size={16} className="text-danger" /> : 
                   rec.severity === 'HIGH' ? <AlertTriangle size={16} className="text-warning" /> : 
                   <AlertCircle size={16} className="text-info" />}
                </div>
                <span><strong>[{rec.severity}]</strong> {rec.title}</span>
              </li>
            )) : (
              <li>
                <div className="outcome-icon"><CheckCircle size={16} className="text-success" /></div>
                <span>No critical issues detected.</span>
              </li>
            )}
          </ul>
        </div>

        {/* Recommended Actions */}
        <div className="outcome-card full-width">
          <div className="outcome-header">
            <h3>Recommended Actions</h3>
          </div>
          {recommendations.length > 0 ? recommendations.slice(0, 3).map((rec: any) => (
            <div key={rec.id} className="recommendation-box">
              <div className="rec-text">
                <h4>{rec.actions[0]}</h4>
                <p>{rec.description}</p>
              </div>
              <button className="btn-primary btn-sm" onClick={() => navigate('/recommendations')}>Fix Now</button>
            </div>
          )) : (
            <div className="recommendation-box">
              <div className="rec-text">
                <h4>Review Deep Intelligence</h4>
                <p>Switch to Professional Mode to see the exact relationship mapping of your infrastructure.</p>
              </div>
              <button className="btn-secondary btn-sm" onClick={navigateToDashboard}>Open Professional Workspace</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
