import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function AttendanceRecordsPage() {
  const { isAdmin } = useAuth();
  const [records, setRecords] = useState([]);
  const [absentStudents, setAbsentStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({});
  const [filters, setFilters] = useState({
    date: new Date().toISOString().split('T')[0],
    class_id: '',
  });
  const [editingId, setEditingId] = useState(null);
  const [editStatus, setEditStatus] = useState('');

  useEffect(() => {
    api.getClasses().then(d => setClasses(d.classes || [])).catch(() => {});
  }, []);

  useEffect(() => {
    fetchRecords();
  }, [filters]);

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.date) params.date = filters.date;
      if (filters.class_id) params.class_id = filters.class_id;

      const result = await api.getDailyAttendance(params);
      setRecords(result.attendance || []);
      setAbsentStudents(result.absent_students || []);
      setSummary({
        present: result.present_count,
        absent: result.absent_count,
        total: result.total_students,
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    setFilters(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleEdit = async (id) => {
    try {
      await api.updateAttendance(id, { status: editStatus });
      setEditingId(null);
      fetchRecords();
    } catch (err) {
      alert(err.message);
    }
  };

  const exportCSV = () => {
    const params = new URLSearchParams(filters).toString();
    window.open(`/api/reports/export?${params}&format=csv`, '_blank');
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Attendance Records</h1>
          <p className="page-subtitle">View and manage daily attendance data</p>
        </div>
        <button className="btn btn-outline" onClick={exportCSV}>
          📥 Export CSV
        </button>
      </div>

      <div className="page-body">
        {/* Filters */}
        <div className="filter-bar">
          <input type="date" className="form-input" name="date"
                 value={filters.date} onChange={handleFilterChange} />
          <select className="form-select" name="class_id"
                  value={filters.class_id} onChange={handleFilterChange}>
            <option value="">All Classes</option>
            {classes.map(c => (
              <option key={c.id} value={c.id}>{c.name} - {c.section}</option>
            ))}
          </select>
          <button className="btn btn-outline btn-sm" onClick={fetchRecords}>🔄 Refresh</button>
        </div>

        {/* Summary Bar */}
        <div className="stats-grid" style={{ marginBottom: '16px' }}>
          <div className="stat-card green">
            <div className="stat-icon green">✅</div>
            <div>
              <div className="stat-value">{summary.present || 0}</div>
              <div className="stat-label">Present</div>
            </div>
          </div>
          <div className="stat-card red">
            <div className="stat-icon red">❌</div>
            <div>
              <div className="stat-value">{summary.absent || 0}</div>
              <div className="stat-label">Absent</div>
            </div>
          </div>
          <div className="stat-card blue">
            <div className="stat-icon blue">📊</div>
            <div>
              <div className="stat-value">
                {summary.total ? Math.round((summary.present / summary.total) * 100) : 0}%
              </div>
              <div className="stat-label">Attendance Rate</div>
            </div>
          </div>
        </div>

        {/* Records Table */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Present Students ({records.length})</h3>
          </div>

          {loading ? (
            <div className="loading-spinner"><div className="spinner" /></div>
          ) : records.length > 0 ? (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Time In</th>
                    <th>Status</th>
                    <th>Confidence</th>
                    <th>Marked By</th>
                    {isAdmin && <th>Action</th>}
                  </tr>
                </thead>
                <tbody>
                  {records.map(r => (
                    <tr key={r.id}>
                      <td><code style={{ fontSize: '0.8rem' }}>{r.student_id}</code></td>
                      <td style={{ fontWeight: 500 }}>{r.student_name}</td>
                      <td>{r.time_in?.slice(0, 5)}</td>
                      <td>
                        {editingId === r.id ? (
                          <select className="form-select" style={{ width: 'auto', padding: '4px 8px', fontSize: '0.8rem' }}
                                  value={editStatus} onChange={e => setEditStatus(e.target.value)}>
                            <option value="present">Present</option>
                            <option value="late">Late</option>
                            <option value="absent">Absent</option>
                          </select>
                        ) : (
                          <span className={`badge badge-${r.status}`}>{r.status}</span>
                        )}
                      </td>
                      <td>{(r.confidence * 100).toFixed(1)}%</td>
                      <td><span className="badge badge-info">{r.marked_by}</span></td>
                      {isAdmin && (
                        <td>
                          {editingId === r.id ? (
                            <div style={{ display: 'flex', gap: '4px' }}>
                              <button className="btn btn-success btn-sm" onClick={() => handleEdit(r.id)}>Save</button>
                              <button className="btn btn-outline btn-sm" onClick={() => setEditingId(null)}>Cancel</button>
                            </div>
                          ) : (
                            <button className="btn btn-outline btn-sm" onClick={() => { setEditingId(r.id); setEditStatus(r.status); }}>
                              Edit
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state"><p>No attendance records for this date</p></div>
          )}
        </div>

        {/* Absent Students */}
        {absentStudents.length > 0 && (
          <div className="card" style={{ marginTop: '16px' }}>
            <div className="card-header">
              <h3 className="card-title">Absent Students ({absentStudents.length})</h3>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Class</th>
                  </tr>
                </thead>
                <tbody>
                  {absentStudents.map(s => (
                    <tr key={s.id}>
                      <td><code style={{ fontSize: '0.8rem' }}>{s.student_id}</code></td>
                      <td>{s.name}</td>
                      <td>{s.section}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
