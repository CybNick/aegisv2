import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAegisQuery } from '../../api/hooks';
import { api } from '../../api/client';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plug, Play, Trash2, Plus, AlertCircle, CheckCircle, Clock, Shield } from 'lucide-react';
import './Connectors.css';

export default function Connectors() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: connectors, isLoading, error } = useAegisQuery<any[]>('/connectors');
  
  const [notification, setNotification] = useState<{msg: string, type: 'success' | 'error'} | null>(null);

  const showNotif = (msg: string, type: 'success' | 'error') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3000);
  };



  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/connectors/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/connectors'] });
      showNotif('Connector deleted', 'success');
    },
    onError: (err: any) => showNotif(err.message, 'error')
  });

  const syncMutation = useMutation({
    mutationFn: (id: string) => api.post(`/connectors/${id}/sync`),
    onSuccess: () => showNotif('Sync completed successfully', 'success'),
    onError: (err: any) => showNotif(err.message, 'error')
  });

  // We removed the manual creation form in favor of the Wizard.

  const handleDelete = (id: string) => {
    if (window.confirm(`Are you sure you want to delete connector '${id}'?`)) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="connectors-page">
      <div className="page-header">
        <h1 className="page-title"><Plug size={24} /> Integrations & Connectors</h1>
        <p className="page-description">Manage your enterprise cloud connections and discovery sources.</p>
        <button className="btn btn-primary mt-2" onClick={() => navigate('/connectors/wizard')}>
          <Plus size={16} /> Add Integration
        </button>
      </div>

      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span>{notification.msg}</span>
        </div>
      )}

      <div className="card">
        {isLoading ? (
          <div className="p-4 text-center">Loading integrations...</div>
        ) : error ? (
          <div className="p-4 text-error">Error loading integrations.</div>
        ) : !connectors || connectors.length === 0 ? (
          <div className="empty-state p-8 text-center">
            <Shield size={48} className="mx-auto mb-4 text-secondary" />
            <h3>No Integrations Active</h3>
            <p className="text-secondary mb-4">Connect your cloud providers to start discovering assets.</p>
            <button className="btn-primary" onClick={() => navigate('/connectors/wizard')}>
              Connect Cloud Provider
            </button>
          </div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Connection ID</th>
                <th>Provider</th>
                <th>Status</th>
                <th>Last Synced</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {connectors.map((conn: any) => (
                <tr key={conn.id}>
                  <td><strong>{conn.id}</strong></td>
                  <td>
                    <span className="badge badge-outline">{conn.type}</span>
                  </td>
                  <td>
                    <span className={`badge ${conn.health === 'FAILED' ? 'badge-danger' : conn.health === 'RUNNING' ? 'badge-warning' : 'badge-success'}`}>
                      {conn.health}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-secondary" />
                      {conn.last_run ? new Date(conn.last_run * 1000).toLocaleString() : 'Never'}
                    </div>
                  </td>
                  <td>
                    <div className="actions">
                      <button 
                        className="btn btn-icon text-accent" 
                        title="Sync Now"
                        onClick={() => syncMutation.mutate(conn.id)}
                        disabled={syncMutation.isPending && syncMutation.variables === conn.id}
                      >
                        <Play size={16} />
                      </button>
                      <button 
                        className="btn btn-icon text-error" 
                        title="Delete"
                        onClick={() => handleDelete(conn.id)}
                        disabled={deleteMutation.isPending && deleteMutation.variables === conn.id}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
