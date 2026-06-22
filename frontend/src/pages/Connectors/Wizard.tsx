import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Cloud, Server, Shield, CheckCircle, ArrowRight, ArrowLeft, Loader2 } from 'lucide-react';
import { api } from '../../api/client';
import './Wizard.css';

type Provider = 'AWS' | 'Azure' | 'GCP' | 'Kubernetes' | 'ActiveDirectory';

export default function ConnectorWizard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [step, setStep] = useState(1);
  const [provider, setProvider] = useState<Provider | null>(null);
  
  // Form fields
  const [accountId, setAccountId] = useState('');
  const [subscriptionId, setSubscriptionId] = useState('');
  const [projectId, setProjectId] = useState('');
  const [clusterId, setClusterId] = useState('');
  const [domain, setDomain] = useState('');

  const [isConnecting, setIsConnecting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const createMutation = useMutation({
    mutationFn: (data: any) => api.post('/connectors/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/connectors'] });
      setIsConnecting(false);
      setIsSuccess(true);
    },
    onError: (err: any) => {
      setIsConnecting(false);
      setErrorMsg(err.message || 'Connection failed.');
    }
  });

  const handleConnect = async () => {
    setIsConnecting(true);
    setErrorMsg('');
    
    // Simulate validation delay for a "premium" feel
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    if (!provider) return;
    
    let params = {};
    let connectorId = `${provider.toLowerCase()}-${Date.now()}`;
    
    if (provider === 'AWS') params = { account_id: accountId || 'default-aws-account' };
    if (provider === 'Azure') params = { subscription_id: subscriptionId || 'default-sub' };
    if (provider === 'GCP') params = { project_id: projectId || 'default-project' };
    if (provider === 'Kubernetes') params = { cluster_id: clusterId || 'default-cluster' };
    if (provider === 'ActiveDirectory') params = { domain: domain || 'corp.local' };

    createMutation.mutate({
      id: connectorId,
      type: provider,
      enabled: true,
      params
    });
  };

  const renderStep1 = () => (
    <div className="wizard-step fade-in">
      <h2>What would you like to connect?</h2>
      <p className="wizard-subtitle">Select an infrastructure provider to discover assets automatically.</p>
      
      <div className="provider-grid">
        <div className={`provider-card ${provider === 'AWS' ? 'selected' : ''}`} onClick={() => setProvider('AWS')}>
          <div className="provider-icon"><Cloud size={32} /></div>
          <h3>Amazon Web Services</h3>
          <p>Discover EC2, VPCs, IAM, and more.</p>
        </div>
        <div className={`provider-card ${provider === 'Azure' ? 'selected' : ''}`} onClick={() => setProvider('Azure')}>
          <div className="provider-icon"><Cloud size={32} /></div>
          <h3>Microsoft Azure</h3>
          <p>Discover VMs, VNets, and Managed Identities.</p>
        </div>
        <div className={`provider-card ${provider === 'GCP' ? 'selected' : ''}`} onClick={() => setProvider('GCP')}>
          <div className="provider-icon"><Cloud size={32} /></div>
          <h3>Google Cloud</h3>
          <p>Discover Compute Engine, Cloud SQL, and more.</p>
        </div>
        <div className={`provider-card ${provider === 'Kubernetes' ? 'selected' : ''}`} onClick={() => setProvider('Kubernetes')}>
          <div className="provider-icon"><Server size={32} /></div>
          <h3>Kubernetes</h3>
          <p>Discover Clusters, Nodes, Pods, and Services.</p>
        </div>
        <div className={`provider-card ${provider === 'ActiveDirectory' ? 'selected' : ''}`} onClick={() => setProvider('ActiveDirectory')}>
          <div className="provider-icon"><Shield size={32} /></div>
          <h3>Active Directory</h3>
          <p>Discover Users, Groups, and Domain Controllers.</p>
        </div>
      </div>

      <div className="wizard-actions right">
        <button className="btn-primary wizard-btn" disabled={!provider} onClick={() => setStep(2)}>
          Continue <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="wizard-step slide-in">
      <h2>Configure {provider} Connection</h2>
      <p className="wizard-subtitle">Provide read-only credentials or identifiers to authenticate.</p>
      
      <div className="config-form">
        {provider === 'AWS' && (
          <div className="form-group">
            <label>AWS Account ID</label>
            <input type="text" placeholder="e.g. 123456789012" value={accountId} onChange={e => setAccountId(e.target.value)} />
            <span className="form-hint">Aegis will use the default credential chain.</span>
          </div>
        )}
        {provider === 'Azure' && (
          <div className="form-group">
            <label>Subscription ID</label>
            <input type="text" placeholder="e.g. 00000000-0000-0000-0000-000000000000" value={subscriptionId} onChange={e => setSubscriptionId(e.target.value)} />
            <span className="form-hint">Ensure Azure CLI is authenticated locally.</span>
          </div>
        )}
        {provider === 'GCP' && (
          <div className="form-group">
            <label>Project ID</label>
            <input type="text" placeholder="e.g. my-production-project" value={projectId} onChange={e => setProjectId(e.target.value)} />
            <span className="form-hint">Application Default Credentials will be used.</span>
          </div>
        )}
        {provider === 'Kubernetes' && (
          <div className="form-group">
            <label>Cluster Context Name (Optional)</label>
            <input type="text" placeholder="e.g. k8s-prod-cluster" value={clusterId} onChange={e => setClusterId(e.target.value)} />
            <span className="form-hint">Uses current kubeconfig context by default.</span>
          </div>
        )}
        {provider === 'ActiveDirectory' && (
          <div className="form-group">
            <label>Domain Name</label>
            <input type="text" placeholder="e.g. corp.local" value={domain} onChange={e => setDomain(e.target.value)} />
            <span className="form-hint">Aegis requires an LDAP service account.</span>
          </div>
        )}

        {errorMsg && (
          <div className="wizard-error">
            {errorMsg}
          </div>
        )}
      </div>

      <div className="wizard-actions split">
        <button className="btn-secondary wizard-btn" onClick={() => setStep(1)} disabled={isConnecting}>
          <ArrowLeft size={18} /> Back
        </button>
        <button className="btn-primary wizard-btn" onClick={handleConnect} disabled={isConnecting}>
          {isConnecting ? <><Loader2 size={18} className="spin" /> Connecting...</> : 'Connect & Scan'}
        </button>
      </div>
    </div>
  );

  const renderSuccess = () => (
    <div className="wizard-step success-step pop-in">
      <div className="success-icon"><CheckCircle size={64} /></div>
      <h2>Connection Established</h2>
      <p className="wizard-subtitle">{provider} has been connected successfully.</p>
      <p className="success-details">
        Aegis is now continuously discovering assets and importing them into the temporal graph.
        You can view the real-time status in the Connectors Manager.
      </p>
      <div className="wizard-actions center">
        <button className="btn-primary wizard-btn" onClick={() => navigate('/connectors')}>
          View Integrations
        </button>
        <button className="btn-secondary wizard-btn" onClick={() => navigate('/')}>
          Return to Dashboard
        </button>
      </div>
    </div>
  );

  return (
    <div className="wizard-container">
      <div className="wizard-card">
        {isSuccess ? renderSuccess() : (step === 1 ? renderStep1() : renderStep2())}
      </div>
    </div>
  );
}
