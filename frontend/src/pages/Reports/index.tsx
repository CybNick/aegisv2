import { useState } from 'react';
import { useAegisQuery } from '../../api/hooks';
import { FileText, Download, Play } from 'lucide-react';
import './Reports.css';

export default function Reports() {
  const [reportType, setReportType] = useState('executive');
  const [format, setFormat] = useState('json');
  const [isGenerated, setIsGenerated] = useState(false);

  // We only fetch when "Generate" is clicked, but useAegisQuery triggers on mount by default.
  // We can control it with `enabled` flag.
  const { data: reportData, isLoading, error, refetch } = useAegisQuery<any>(
    `/reports/${reportType}?format=${format}`, 
    { enabled: isGenerated }
  );

  const handleGenerate = () => {
    setIsGenerated(true);
    refetch();
  };

  const handleDownload = () => {
    if (!reportData) return;
    
    // In JSON, format it as string. For others, it's probably already a string from the backend,
    // but axios/fetch might parse JSON automatically. We need to handle that.
    const content = typeof reportData === 'object' ? JSON.stringify(reportData, null, 2) : String(reportData);
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `aegis_${reportType}_report.${format}`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="reports-page">
      <div className="page-header">
        <h1 className="page-title"><FileText size={24} /> Reports</h1>
        <p className="page-description">Generate, preview, and download compliance and security reports.</p>
      </div>

      <div className="card report-controls">
        <div className="form-row">
          <div className="form-group">
            <label>Report Type</label>
            <select value={reportType} onChange={e => {setReportType(e.target.value); setIsGenerated(false);}}>
              <option value="executive">Executive Summary</option>
              <option value="technical">Technical Details</option>
            </select>
          </div>
          <div className="form-group">
            <label>Format</label>
            <select value={format} onChange={e => {setFormat(e.target.value); setIsGenerated(false);}}>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
              <option value="markdown">Markdown</option>
              <option value="html">HTML</option>
            </select>
          </div>
        </div>
        <div className="actions-row">
          <button className="btn btn-primary" onClick={handleGenerate} disabled={isLoading}>
            <Play size={16} /> {isLoading ? 'Generating...' : 'Generate Preview'}
          </button>
          <button className="btn btn-secondary" onClick={handleDownload} disabled={!isGenerated || isLoading || !reportData}>
            <Download size={16} /> Download
          </button>
        </div>
      </div>

      {error && (
        <div className="text-error mt-4">
          Failed to generate report: {error.message}
        </div>
      )}

      {isGenerated && reportData && (
        <div className="card preview-pane mt-4">
          <h3>Preview</h3>
          {format === 'html' ? (
            <div 
              className="html-preview" 
              dangerouslySetInnerHTML={{ __html: String(reportData) }} 
            />
          ) : (
            <pre className="text-preview">
              {typeof reportData === 'object' ? JSON.stringify(reportData, null, 2) : String(reportData)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
