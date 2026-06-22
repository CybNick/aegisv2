
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, Share2, Clock, Search,
  FileText, Plug, Terminal, Activity, ShieldAlert, GitBranch, Layers, 
  Briefcase, TrendingUp, ShieldCheck, Building2, Sparkles
} from 'lucide-react';
import './MainLayout.css';
import { useTimeline } from '../hooks/useTimeline';
import { useMode } from '../hooks/useMode';

export default function MainLayout() {
  const { context, asOf } = useTimeline();
  const { isSimple, isProfessional, isExecutive, setMode } = useMode();

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Aegis CCEIP</h2>
        </div>
        <nav className="sidebar-nav">
          {isSimple && (
            <>
              <NavLink to="/home" className="nav-item"><LayoutDashboard size={18} /> Home</NavLink>
              <NavLink to="/scan-center" className="nav-item"><Search size={18} /> Scan Center</NavLink>
              <NavLink to="/monitoring" className="nav-item"><Activity size={18} /> Monitoring</NavLink>
              <NavLink to="/reports" className="nav-item"><FileText size={18} /> Reports</NavLink>
            </>
          )}
          {isProfessional && (
            <>
              <NavLink to="/dashboard" className="nav-item"><LayoutDashboard size={18} /> Dashboard</NavLink>
              <NavLink to="/cyber-graph" className="nav-item"><Share2 size={18} /> Cyber Graph</NavLink>
              <NavLink to="/dependencies" className="nav-item"><GitBranch size={18} /> Dependencies</NavLink>
              <NavLink to="/evidence" className="nav-item"><Layers size={18} /> Evidence</NavLink>
              <NavLink to="/risk" className="nav-item"><ShieldAlert size={18} /> Risk</NavLink>
              <NavLink to="/monitoring" className="nav-item"><Activity size={18} /> Monitoring</NavLink>
              <NavLink to="/alerts" className="nav-item"><ShieldAlert size={18} /> Alerts</NavLink>
              <NavLink to="/timeline" className="nav-item"><Clock size={18} /> Timeline</NavLink>
              <NavLink to="/apql" className="nav-item"><Terminal size={18} /> APQL Workspace</NavLink>
              <NavLink to="/connectors" className="nav-item"><Plug size={18} /> Connectors</NavLink>
              <div className="my-4 border-t border-border/50"></div>
              <NavLink to="/assistant" className="nav-item bg-primary/10 text-primary hover:bg-primary/20"><Sparkles size={18} /> Ask Aegis AI</NavLink>
            </>
          )}
          {isExecutive && (
            <>
              <NavLink to="/executive" className="nav-item"><Briefcase size={18} /> Exec Summary</NavLink>
              <NavLink to="/risk-trends" className="nav-item"><TrendingUp size={18} /> Risk Trends</NavLink>
              <NavLink to="/compliance" className="nav-item"><ShieldCheck size={18} /> Compliance</NavLink>
              <NavLink to="/governance" className="nav-item"><ShieldAlert size={18} /> Governance</NavLink>
              <NavLink to="/business-units" className="nav-item"><Building2 size={18} /> Business Units</NavLink>
              <NavLink to="/lifecycle" className="nav-item"><Activity size={18} /> Asset Lifecycle</NavLink>
              <NavLink to="/reports" className="nav-item"><FileText size={18} /> Reports</NavLink>
              <div className="my-4 border-t border-border/50"></div>
              <NavLink to="/assistant" className="nav-item bg-primary/10 text-primary hover:bg-primary/20"><Sparkles size={18} /> Ask Aegis AI</NavLink>
              <div className="my-4 border-t border-border/50"></div>
              <NavLink to="/trust-center" className="nav-item"><ShieldCheck size={18} /> Trust Center</NavLink>
              <NavLink to="/system-health" className="nav-item"><Activity size={18} /> System Health</NavLink>
            </>
          )}
        </nav>
        <div className="mode-toggle">
          <label className="mode-label">Mode</label>
          <select 
            value={isSimple ? 'simple' : isProfessional ? 'professional' : 'executive'} 
            onChange={(e) => setMode(e.target.value as any)}
            className="mode-select"
          >
            <option value="executive">Executive Mode</option>
            <option value="simple">Simple Mode</option>
            <option value="professional">Professional Workspace</option>
          </select>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="flex-1 max-w-2xl flex items-center gap-4">
            <div className="global-search relative flex-1">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
              <input 
                type="text" 
                placeholder="Global Search: Assets, Risks, Compliance..." 
                className="w-full bg-tertiary border border-border outline-none pl-10 pr-4 py-2 rounded-lg focus:border-primary transition-colors"
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    const val = e.currentTarget.value;
                    if (val) window.location.href = `/search?q=${encodeURIComponent(val)}`;
                  }
                }}
              />
            </div>
            
            {isProfessional && (
              <div className="apql-bar hidden lg:flex items-center">
                <Terminal size={18} className="apql-icon mr-2 text-primary" />
                <span className="text-sm font-mono text-secondary">APQL Workspace Active</span>
              </div>
            )}
          </div>
          
          {isProfessional && (
            <div className="timeline-context hidden md:flex items-center">
              <span className="context-label">Context:</span>
              <span className="context-value">{context}</span>
              <span className="context-label ml-4">As Of:</span>
              <span className="context-value text-blue">{asOf}</span>
            </div>
          )}
        </header>
        <div className="page-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
