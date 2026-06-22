import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, Cloud, Network, CheckCircle, ArrowRight, ArrowLeft, Loader2, PlayCircle, ShieldAlert } from 'lucide-react';
import { useAegisQuery } from '../../api/hooks';
import './ScanCenter.css';

type ScanType = 'network' | 'web' | 'cloud' | null;

export default function ScanCenter() {
  const navigate = useNavigate();
  const [step, setStep] = useState<number>(1);
  const [scanType, setScanType] = useState<ScanType>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Target data
  const [target, setTarget] = useState<string>('');
  
  // Cloud wizard state
  const [cloudProvider, setCloudProvider] = useState<string>('');
  const [cloudCreds, setCloudCreds] = useState<string>('');
  const [isValidating, setIsValidating] = useState<boolean>(false);

  // Scan state
  const [scanId, setScanId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isScanning, setIsScanning] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Auto-detect network hook
  const { data: detectedNetworkData } = useAegisQuery<any>('/scans/suggest-network', {
    enabled: scanType === 'network' && step === 2
  });

  const detectedNetwork = detectedNetworkData?.network || '192.168.1.0/24';
  const detectedDevices = detectedNetworkData?.last_devices_found || 0;

  // Auto-progress by polling real scan
  useEffect(() => {
    let currentStepForPolling = 0;
    if (scanType === 'cloud') {
      currentStepForPolling = 5;
    } else {
      currentStepForPolling = 4;
    }

    if (step === currentStepForPolling && isScanning && scanId) {
      const interval = setInterval(async () => {
        try {
          const res = await fetch(`/api/v1/scans/${scanId}`);
          if (!res.ok) return;
          const data = await res.json();
          const scan = data.data;
          
          setProgress(scan.progress || 0);
          
          if (scan.status === 'COMPLETED') {
            clearInterval(interval);
            setIsScanning(false);
            navigate(`/scan-results/${scanId}`);
          } else if (scan.status === 'FAILED') {
            clearInterval(interval);
            setIsScanning(false);
            setErrorMsg(scan.error_message || 'Scan failed.');
          }
        } catch (e) {
          console.error(e);
        }
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [step, isScanning, scanId, scanType, navigate]);

  const handleNext = () => setStep(s => s + 1);
  const handlePrev = () => setStep(s => Math.max(s - 1, 1));

  const startScan = async () => {
    let effectiveTarget = target;
    if (scanType === 'network') {
      effectiveTarget = detectedNetwork; // Use detected if they didn't explicitly override via advanced options
    }

    if (scanType === 'cloud') {
      setStep(5);
    } else {
      setStep(4);
    }
    
    setProgress(0);
    setIsScanning(true);
    setErrorMsg(null);
    
    try {
      const res = await fetch('/api/v1/scans/network', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: effectiveTarget })
      });
      const data = await res.json();
      if (data.data && data.data.scan_id) {
        setScanId(data.data.scan_id);
      } else {
        throw new Error('Failed to start scan');
      }
    } catch (e) {
      setIsScanning(false);
      setErrorMsg('Failed to initiate scan.');
    }
  };

  const validateCloud = () => {
    setIsValidating(true);
    setTimeout(() => {
      setIsValidating(false);
      handleNext();
    }, 1500);
  };

  return (
    <div className="scan-center-container">
      <div className="scan-wizard-header">
        <h1>Guided Scan</h1>
      </div>

      <div className="wizard-content">
        {/* STEP 1: CHOOSE SCAN TYPE */}
        {step === 1 && (
          <div className="step-pane animation-fade">
            <h2>What would you like to scan?</h2>
            <div className="scan-types-grid">
              <button className={`scan-type-btn ${scanType === 'network' ? 'selected' : ''}`} onClick={() => { setScanType('network'); handleNext(); }}>
                <Network size={32} />
                <h3>My Network</h3>
                <p>Discover local devices securely</p>
              </button>
              <button className={`scan-type-btn ${scanType === 'web' ? 'selected' : ''}`} onClick={() => { setScanType('web'); handleNext(); }}>
                <Globe size={32} />
                <h3>Analyze a Website</h3>
                <p>Check public exposure</p>
              </button>
              <button className={`scan-type-btn ${scanType === 'cloud' ? 'selected' : ''}`} onClick={() => { setScanType('cloud'); handleNext(); }}>
                <Cloud size={32} />
                <h3>Cloud Discovery</h3>
                <p>Map cloud infrastructure</p>
              </button>
            </div>
          </div>
        )}

        {/* STEP 2/3/4: DYNAMIC WIZARDS BASED ON TYPE */}
        
        {/* --- NETWORK FLOW --- */}
        {scanType === 'network' && step === 2 && (
          <div className="step-pane animation-fade">
            <h2>Scan My Network</h2>
            <div className="guided-box">
              <div className="guided-icon"><Network size={48} /></div>
              <h3>Detected Network</h3>
              {!showAdvanced ? (
                <>
                  <p className="guided-value">{detectedNetwork}</p>
                  <p className="guided-subtext">Devices Found Last Scan: {detectedDevices}</p>
                  <button className="text-primary text-sm mt-2 hover:underline" onClick={() => setShowAdvanced(true)}>Advanced Options</button>
                </>
              ) : (
                <div className="mt-4 text-left">
                  <label className="guided-label">Target CIDR / IP Range:</label>
                  <input 
                    type="text" 
                    className="guided-input"
                    value={target || detectedNetwork} 
                    onChange={(e) => setTarget(e.target.value)}
                  />
                  <button className="text-secondary text-sm mt-2 hover:underline" onClick={() => { setShowAdvanced(false); setTarget(''); }}>Hide Advanced Options</button>
                </div>
              )}
              
              <div className="wizard-actions center mt-6">
                <button className="btn-secondary" onClick={handlePrev}><ArrowLeft size={18} /> Back</button>
                <button className="btn-primary run-btn" onClick={startScan}>
                  <PlayCircle size={18} /> Start Scan
                </button>
              </div>
            </div>
          </div>
        )}

        {/* --- WEB FLOW --- */}
        {scanType === 'web' && step === 2 && (
          <div className="step-pane animation-fade">
            <h2>Analyze a Website</h2>
            <div className="guided-box text-left">
              <label className="guided-label">Website:</label>
              <input 
                type="url" 
                className="guided-input"
                value={target} 
                onChange={(e) => setTarget(e.target.value)} 
                placeholder="company.com" 
                autoFocus 
              />
              <p className="text-muted mt-2">Aegis will safely check for open ports, services, and risks.</p>
              
              <div className="wizard-actions space-between mt-6">
                <button className="btn-secondary" onClick={handlePrev}><ArrowLeft size={18} /> Back</button>
                <button className="btn-primary" disabled={!target} onClick={startScan}>
                  Analyze <ArrowRight size={18} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* --- CLOUD FLOW --- */}
        {scanType === 'cloud' && step === 2 && (
          <div className="step-pane animation-fade">
            <h2>Step 1: Select Provider</h2>
            <div className="cloud-providers">
              <button className={`cloud-btn ${cloudProvider === 'aws' ? 'selected' : ''}`} onClick={() => setCloudProvider('aws')}>AWS</button>
              <button className={`cloud-btn ${cloudProvider === 'azure' ? 'selected' : ''}`} onClick={() => setCloudProvider('azure')}>Azure</button>
              <button className={`cloud-btn ${cloudProvider === 'gcp' ? 'selected' : ''}`} onClick={() => setCloudProvider('gcp')}>GCP</button>
            </div>
            <div className="wizard-actions space-between mt-6">
              <button className="btn-secondary" onClick={handlePrev}><ArrowLeft size={18} /> Back</button>
              <button className="btn-primary" disabled={!cloudProvider} onClick={handleNext}>
                Continue <ArrowRight size={18} />
              </button>
            </div>
          </div>
        )}

        {scanType === 'cloud' && step === 3 && (
          <div className="step-pane animation-fade">
            <h2>Step 2: Connect Account</h2>
            <div className="guided-box text-left">
              <label className="guided-label">Paste Read-Only Token or Credentials</label>
              <textarea 
                className="guided-textarea"
                rows={4}
                value={cloudCreds}
                onChange={(e) => setCloudCreds(e.target.value)}
                placeholder="Enter token..."
              ></textarea>
              
              <div className="wizard-actions space-between mt-6">
                <button className="btn-secondary" onClick={handlePrev}><ArrowLeft size={18} /> Back</button>
                <button className="btn-primary" disabled={!cloudCreds || isValidating} onClick={validateCloud}>
                  {isValidating ? <><Loader2 className="spinner" size={18} /> Validating...</> : 'Validate Connection'}
                </button>
              </div>
            </div>
          </div>
        )}

        {scanType === 'cloud' && step === 4 && (
          <div className="step-pane animation-fade">
            <h2>Step 3: Ready to Discover</h2>
            <div className="guided-box">
              <CheckCircle size={48} className="success-icon" style={{margin: '0 auto 1rem'}} />
              <h3>Connection Validated!</h3>
              <p>Aegis can securely read metadata from your {cloudProvider.toUpperCase()} environment.</p>
              
              <div className="wizard-actions space-between mt-6">
                <button className="btn-secondary" onClick={handlePrev}><ArrowLeft size={18} /> Back</button>
                <button className="btn-primary run-btn" onClick={startScan}>
                  <PlayCircle size={18} /> Run Discovery
                </button>
              </div>
            </div>
          </div>
        )}

        {/* SCANNING PROGRESS (Step 4 or 5 depending on flow) */}
        {((scanType !== 'cloud' && step === 4) || (scanType === 'cloud' && step === 5)) && (
          <div className="step-pane animation-fade center-content">
            <h2>Discovery in Progress</h2>
            <p className="subtitle">Please wait while Aegis completes analysis...</p>
            <div className="progress-container">
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <div className="progress-text">{progress}% Complete</div>
            </div>
            {isScanning && <Loader2 className="spinner" size={48} />}
            {errorMsg && <div className="error-box mt-4"><ShieldAlert /> {errorMsg}</div>}
          </div>
        )}

      </div>
    </div>
  );
}
