import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function Layout() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const [syncPending, setSyncPending] = useState(0);

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
    api.getSyncStatus().then(d => setSyncPending(d.pending || 0)).catch(() => {});
  }, [location]);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/attendance', label: 'Mark Attendance', icon: '📸' },
    { path: '/records', label: 'Records', icon: '📋' },
    { path: '/register', label: 'Register Student', icon: '👤' },
    { path: '/reports', label: 'Reports', icon: '📈' },
    { path: '/sync', label: 'Sync & Logs', icon: '🔄' },
  ];

  const handleNav = (path) => {
    navigate(path);
    setSidebarOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || 'U';

  return (
    <div className="app-layout">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 99 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <span>📚 Smart Attendance</span>
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--surface-400)', marginTop: '4px' }}>
            Rural School System v1.0
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <button
              key={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => handleNav(item.path)}
            >
              <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ marginBottom: '12px' }}>
            <div className={`sync-indicator ${online ? 'online' : 'offline'}`}>
              <span className={`sync-dot ${online ? 'online' : 'offline'}`} />
              {online ? 'Online' : 'Offline'}
              {syncPending > 0 && ` · ${syncPending} pending`}
            </div>
          </div>
          <div className="user-info">
            <div className="user-avatar">{initials}</div>
            <div className="user-details">
              <div className="user-name">{user?.full_name}</div>
              <div className="user-role">{user?.role}</div>
            </div>
          </div>
          <button
            className="btn btn-outline btn-sm"
            style={{ width: '100%', marginTop: '12px', color: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)' }}
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="main-content">
        {/* Mobile header */}
        <div style={{ display: 'none', padding: '12px 16px', background: 'white', borderBottom: '1px solid var(--surface-200)', alignItems: 'center', justifyContent: 'space-between' }}
             className="mobile-header"
        >
          <button className="mobile-menu-btn" onClick={() => setSidebarOpen(true)}>
            ☰
          </button>
          <span style={{ fontWeight: 600 }}>Smart Attendance</span>
          <div className={`sync-indicator ${online ? 'online' : 'offline'}`} style={{ padding: '4px 8px' }}>
            <span className={`sync-dot ${online ? 'online' : 'offline'}`} />
          </div>
        </div>

        <div className="page-enter">
          <Outlet />
        </div>
      </main>

      <style>{`
        @media(max-width:768px){
          .mobile-header{display:flex!important}
        }
      `}</style>
    </div>
  );
}
