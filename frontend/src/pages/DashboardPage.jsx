import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#3b82f6'];

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const d = await api.getDashboardSummary();
      setData(d);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>;

  if (!data) return <div className="page-body"><div className="alert alert-error">Failed to load dashboard</div></div>;

  const { overview, today, week_trend, class_summary, recent_activity } = data;

  const pieData = [
    { name: 'Present', value: today.present },
    { name: 'Late', value: today.late },
    { name: 'Absent', value: today.absent },
  ].filter(d => d.value > 0);

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Welcome back! Here&apos;s today&apos;s overview.</p>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--surface-500)' }}>
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </div>
      </div>

      <div className="page-body">
        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card blue">
            <div className="stat-icon blue">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <div>
              <div className="stat-value">{overview.total_students}</div>
              <div className="stat-label">Total Students</div>
            </div>
          </div>

          <div className="stat-card green">
            <div className="stat-icon green">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <div>
              <div className="stat-value">{today.present}</div>
              <div className="stat-label">Present Today</div>
            </div>
          </div>

          <div className="stat-card amber">
            <div className="stat-icon amber">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </div>
            <div>
              <div className="stat-value">{today.attendance_percentage}%</div>
              <div className="stat-label">Attendance Rate</div>
            </div>
          </div>

          <div className="stat-card red">
            <div className="stat-icon red">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><rect x="9" y="9" width="13" height="6" rx="1"/></svg>
            </div>
            <div>
              <div className="stat-value">{overview.registered_faces}</div>
              <div className="stat-label">Faces Registered</div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="charts-grid">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📊 Weekly Attendance Trend</h3>
            </div>
            <div style={{ height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={week_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="day" fontSize={12} tickLine={false} />
                  <YAxis fontSize={12} tickLine={false} />
                  <Tooltip
                    contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: '0.85rem' }}
                  />
                  <Bar dataKey="present" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Present" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">🎯 Today&apos;s Breakdown</h3>
            </div>
            <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ borderRadius: 8, fontSize: '0.85rem' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">
                  <p>No attendance data yet for today</p>
                </div>
              )}
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginTop: '8px' }}>
              {pieData.map((item, i) => (
                <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem' }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: COLORS[i] }} />
                  {item.name}: {item.value}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Class Summary & Recent Activity */}
        <div className="charts-grid" style={{ marginTop: 'var(--space-lg)' }}>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">🏫 Class Summary (Today)</h3>
            </div>
            {class_summary && class_summary.length > 0 ? (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Class</th>
                      <th>Present</th>
                      <th>Total</th>
                      <th>%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {class_summary.slice(0, 10).map(c => (
                      <tr key={c.class_id}>
                        <td style={{ fontWeight: 600 }}>{c.class_name}</td>
                        <td>{c.present}</td>
                        <td>{c.total}</td>
                        <td>
                          <span className={`badge ${c.percentage >= 75 ? 'badge-present' : c.percentage >= 50 ? 'badge-late' : 'badge-absent'}`}>
                            {c.percentage}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state"><p>No class data available</p></div>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📝 Recent Activity</h3>
            </div>
            {recent_activity && recent_activity.length > 0 ? (
              <ul className="attendance-log">
                {recent_activity.slice(0, 8).map(log => (
                  <li key={log.id} className="attendance-log-item">
                    <div className="log-avatar">
                      {log.action === 'login_success' ? '🔐' :
                       log.action === 'attendance_face' ? '📸' :
                       log.action === 'student_registered' ? '👤' : '📋'}
                    </div>
                    <div className="log-details">
                      <div className="log-name">{log.action.replace(/_/g, ' ')}</div>
                      <div className="log-meta">{log.details}</div>
                    </div>
                    <div className="log-time">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-state"><p>No recent activity</p></div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
