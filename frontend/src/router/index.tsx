import { createBrowserRouter, Navigate } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import Dashboard from '../pages/Dashboard';
import GraphExplorer from '../pages/Graph';
import Timeline from '../pages/Timeline';
import APQLWorkspace from '../pages/APQL';
import Reports from '../pages/Reports';
import Connectors from '../pages/Connectors';
import ConnectorWizard from '../pages/Connectors/Wizard';
import Home from '../pages/Home';
import ScanCenter from '../pages/ScanCenter';
import CyberGraph from '../pages/CyberGraph';
import Dependencies from '../pages/Intelligence/Dependencies';
import Evidence from '../pages/Intelligence/Evidence';
import Risk from '../pages/Intelligence/Risk';
import ScanResults from '../pages/ScanResults';
import Monitoring from '../pages/Monitoring';
import AlertCenter from '../pages/AlertCenter';
import AttackPaths from '../pages/AttackPaths';
import Exposure from '../pages/Exposure';
import CriticalAssets from '../pages/CriticalAssets';
import BlastRadius from '../pages/BlastRadius';
import AssetInventory from '../pages/AssetInventory';
import AssetDetails from '../pages/AssetDetails';
import Recommendations from '../pages/Recommendations';
import ExecutiveHome from '../pages/ExecutiveHome';
import Compliance from '../pages/Compliance';
import Governance from '../pages/Governance';
import RiskTrends from '../pages/RiskTrends';
import BusinessUnits from '../pages/BusinessUnits';
import Assistant from '../pages/Assistant';
import SearchResults from '../pages/Search';
import Lifecycle from '../pages/Lifecycle';
import TrustCenter from '../pages/TrustCenter';
import SystemHealth from '../pages/SystemHealth';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <Navigate to="/home" replace /> },
      { path: 'home', element: <Home /> },
      { path: 'scan-center', element: <ScanCenter /> },
      { path: 'scan-results/:id', element: <ScanResults /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'graph', element: <GraphExplorer /> },
      { path: 'cyber-graph', element: <CyberGraph /> },
      { path: 'dependencies', element: <Dependencies /> },
      { path: 'evidence', element: <Evidence /> },
      { path: 'risk', element: <Risk /> },
      { path: 'monitoring', element: <Monitoring /> },
      { path: 'alerts', element: <AlertCenter /> },
      { path: 'timeline', element: <Timeline /> },
      { path: 'apql', element: <APQLWorkspace /> },
      { path: 'reports', element: <Reports /> },
      { path: 'connectors', element: <Connectors /> },
      { path: 'connectors/wizard', element: <ConnectorWizard /> },
      { path: 'attack-paths', element: <AttackPaths /> },
      { path: 'exposure', element: <Exposure /> },
      { path: 'critical-assets', element: <CriticalAssets /> },
      { path: 'blast-radius', element: <BlastRadius /> },
      { path: 'assets', element: <AssetInventory /> },
      { path: 'assets/:id', element: <AssetDetails /> },
      { path: 'recommendations', element: <Recommendations /> },
      { path: 'executive', element: <ExecutiveHome /> },
      { path: 'compliance', element: <Compliance /> },
      { path: 'governance', element: <Governance /> },
      { path: 'risk-trends', element: <RiskTrends /> },
      { path: 'business-units', element: <BusinessUnits /> },
      { path: 'assistant', element: <Assistant /> },
      { path: 'search', element: <SearchResults /> },
      { path: 'lifecycle', element: <Lifecycle /> },
      { path: 'trust-center', element: <TrustCenter /> },
      { path: 'system-health', element: <SystemHealth /> },
    ],
  },
]);
