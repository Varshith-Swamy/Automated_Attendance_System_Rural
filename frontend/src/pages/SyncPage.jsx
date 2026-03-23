import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function SyncPage() {
  const { isAdmin } = useAuth();
  const [syncStatus, setSyncStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setOnline(true);
    const handleOffline = () => setOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [status, logsData] = await Promise.all([
        api.getSyncStatus(),
        isAdmin ? api.getAuditLogs({ per_page: 30 }) : Promise.resolve({ logs: [] }),
      ]);
      setSyncStatus(status);
      setLogs(logsData.logs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.triggerSync();
      await fetchData();
    } catch (err) {
      alert(err.message || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Sync & Audit Logs</h1>
          <p className="page-subtitle">Offline sync status and system activity logs</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className={`sync-indicator ${online ? 'online' : 'offline'}`}>
            <span className={`sync-dot ${online ? 'online' : 'offline'}`} />
            {online ? 'Online' : 'Offline'}
          </div>
          {isAdmin && (
            <button className="btn btn-primary" onClick={handleSync} disabled={syncing}>
              {syncing ? '⏳ Syncing...' : '🔄 Sync Now'}
            </button>
          )}
        </div>
      </div>

      <div className="page-body">
        {/* Sync Stats */}
        <div className="stats-grid">
          <div className="stat-card amber">
            <div className="stat-icon amber">⏳</div>
            <div>
              <div className="stat-value">{syncStatus?.pending || 0}</div>
              <div className="stat-label">Pending Sync</div>
            </div>
          </div>
          <div className="stat-card green">
            <div className="stat-icon green">✅</div>
            <div>
              <div className="stat-value">{syncStatus?.synced || 0}</div>
              <div className="stat-label">Synced</div>
            </div>
          </div>
          <div className="stat-card red">
            <div className="stat-icon red">❌</div>
            <div>
              <div className="stat-value">{syncStatus?.failed || 0}</div>
              <div className="stat-label">Failed</div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Sync Queue */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">🔄 Sync Queue</h3>
              <button className="btn btn-outline btn-sm" onClick={fetchData}>Refresh</button>
            </div>
            {syncStatus?.recent && syncStatus.recent.length > 0 ? (
              <ul className="attendance-log">
                {syncStatus.recent.map(item => (
                  <li key={item.id} className="attendance-log-item">
                    <div className="log-avatar" style={{
                      background: item.synced ? '#ecfdf5' : '#fffbeb',
                      color: item.synced ? 'var(--accent-600)' : 'var(--warning-600)',
                    }}>
                      {item.synced ? '✓' : '⏳'}
                    </div>
                    <div className="log-details">
                      <div className="log-name">{item.action?.replace(/_/g, ' ')}</div>
                      <div className="log-meta">
                        {item.synced ? `Synced: ${item.synced_at ? new Date(item.synced_at).toLocaleString() : 'yes'}` :
                         `Retries: ${item.retry_count}`}
                      </div>
                    </div>
                    <span className={`badge ${item.synced ? 'badge-present' : 'badge-late'}`}>
                      {item.synced ? 'Synced' : 'Pending'}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-state"><p>No sync items in queue</p></div>
            )}
          </div>

          {/* Audit Logs */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📝 Audit Logs</h3>
            </div>
            {logs.length > 0 ? (
              <ul className="attendance-log" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {logs.map(log => (
                  <li key={log.id} className="attendance-log-item">
                    <div className="log-avatar">
                      {log.status === 'success' ? '✅' : '❌'}
                    </div>
                    <div className="log-details">
                      <div className="log-name">{log.action?.replace(/_/g, ' ')}</div>
                      <div className="log-meta">{log.details}</div>
                    </div>
                    <div className="log-time">
                      {log.created_at ? new Date(log.created_at).toLocaleString('en-IN', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      }) : ''}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-state"><p>No audit logs available</p></div>
            )}
          </div>
        </div>

        {/* Offline-First Explanation */}
        <div className="card" style={{ marginTop: '24px' }}>
          <div className="card-header">
            <h3 className="card-title">ℹ️ How Offline Sync Works</h3>
          </div>
          <div style={{ fontSize: '0.9rem', color: 'var(--surface-600)', lineHeight: 1.8 }}>
            <p>
              <strong>1. Record Locally:</strong> All attendance marking works offline. Data is saved to the local SQLite database immediately.
            </p>
            <p>
              <strong>2. Queue for Sync:</strong> Each action is added to the sync queue automatically.
            </p>
            <p>
              <strong>3. Sync When Online:</strong> When internet becomes available, click "Sync Now" to push all pending data to the cloud server.
            </p>
            <p>
              <strong>4. Retry on Failure:</strong> Failed sync items are automatically retried. The retry count tracks attempts.
            </p>
            <p style={{ marginTop: '8px', color: 'var(--surface-400)', fontSize: '0.8rem' }}>
              💡 This offline-first design ensures the system works reliably in rural areas with intermittent or no internet connectivity.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
