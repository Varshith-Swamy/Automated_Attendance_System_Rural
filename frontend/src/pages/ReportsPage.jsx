import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

export default function ReportsPage() {
  const [view, setView] = useState('class'); // 'class' or 'student'
  const [classes, setClasses] = useState([]);
  const [students, setStudents] = useState([]);
  const [selectedClass, setSelectedClass] = useState('');
  const [selectedStudent, setSelectedStudent] = useState('');
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [classReport, setClassReport] = useState(null);
  const [studentReport, setStudentReport] = useState(null);
  const [monthlySummary, setMonthlySummary] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getClasses().then(d => setClasses(d.classes || [])).catch(() => {});
    api.getStudents({ per_page: 200 }).then(d => setStudents(d.students || [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (view === 'class' && selectedClass) {
      fetchClassReport();
    }
  }, [selectedClass, month]);

  useEffect(() => {
    if (view === 'student' && selectedStudent) {
      fetchStudentReport();
    }
  }, [selectedStudent, month]);

  useEffect(() => {
    fetchMonthlySummary();
  }, [month]);

  const fetchClassReport = async () => {
    setLoading(true);
    try {
      const data = await api.getClassReport(selectedClass, { month });
      setClassReport(data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const fetchStudentReport = async () => {
    setLoading(true);
    try {
      const data = await api.getStudentReport(selectedStudent, { month });
      setStudentReport(data);
    } catch (err) { console.error(err); }
    finally { setLoading(false) }
  };

  const fetchMonthlySummary = async () => {
    try {
      const data = await api.getMonthlySummary({ month });
      setMonthlySummary(data);
    } catch (err) { console.error(err); }
  };

  const monthlyChartData = monthlySummary?.daily_breakdown
    ? Object.entries(monthlySummary.daily_breakdown).map(([date, counts]) => ({
        date: date.slice(-2),
        present: counts.present || 0,
        late: counts.late || 0,
        absent: counts.absent || 0,
      })).sort((a, b) => a.date.localeCompare(b.date))
    : [];

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports & Analytics</h1>
          <p className="page-subtitle">Attendance trends and insights</p>
        </div>
      </div>

      <div className="page-body">
        {/* View Tabs & Filters */}
        <div className="filter-bar">
          <button className={`btn ${view === 'class' ? 'btn-primary' : 'btn-outline'} btn-sm`}
                  onClick={() => setView('class')}>
            🏫 Class Report
          </button>
          <button className={`btn ${view === 'student' ? 'btn-primary' : 'btn-outline'} btn-sm`}
                  onClick={() => setView('student')}>
            👤 Student Report
          </button>
          <input type="month" className="form-input" value={month}
                 onChange={e => setMonth(e.target.value)} />
          {view === 'class' && (
            <select className="form-select" value={selectedClass}
                    onChange={e => setSelectedClass(e.target.value)}>
              <option value="">Select Class</option>
              {classes.map(c => (
                <option key={c.id} value={c.id}>{c.name} - {c.section}</option>
              ))}
            </select>
          )}
          {view === 'student' && (
            <select className="form-select" value={selectedStudent}
                    onChange={e => setSelectedStudent(e.target.value)}>
              <option value="">Select Student</option>
              {students.map(s => (
                <option key={s.id} value={s.id}>{s.name} ({s.student_id})</option>
              ))}
            </select>
          )}
        </div>

        {/* Monthly Overview Chart */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <h3 className="card-title">📊 Monthly Attendance Overview</h3>
          </div>
          {monthlyChartData.length > 0 ? (
            <div style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" fontSize={11} tickLine={false} />
                  <YAxis fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: '0.8rem' }} />
                  <Bar dataKey="present" fill="#10b981" stackId="a" name="Present" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="late" fill="#f59e0b" stackId="a" name="Late" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state"><p>No data for this month</p></div>
          )}
        </div>

        {/* Class Report */}
        {view === 'class' && classReport && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">
                🏫 {classReport.class?.name} — Avg: {classReport.average_attendance}%
              </h3>
              <span className="badge badge-info">{classReport.student_count} students</span>
            </div>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>Days Present</th>
                    <th>Total Days</th>
                    <th>%</th>
                  </tr>
                </thead>
                <tbody>
                  {classReport.students?.map(s => (
                    <tr key={s.student.id}>
                      <td><code>{s.student.student_id}</code></td>
                      <td style={{ fontWeight: 500 }}>{s.student.name}</td>
                      <td>{s.present_days}</td>
                      <td>{s.total_days}</td>
                      <td>
                        <span className={`badge ${s.attendance_percentage >= 75 ? 'badge-present' : s.attendance_percentage >= 50 ? 'badge-late' : 'badge-absent'}`}>
                          {s.attendance_percentage}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Student Report */}
        {view === 'student' && studentReport && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">👤 {studentReport.student?.name}</h3>
            </div>

            <div className="stats-grid" style={{ marginBottom: '16px' }}>
              <div className="stat-card green">
                <div><div className="stat-value">{studentReport.summary?.present}</div><div className="stat-label">Present</div></div>
              </div>
              <div className="stat-card amber">
                <div><div className="stat-value">{studentReport.summary?.late}</div><div className="stat-label">Late</div></div>
              </div>
              <div className="stat-card red">
                <div><div className="stat-value">{studentReport.summary?.absent}</div><div className="stat-label">Absent</div></div>
              </div>
              <div className="stat-card blue">
                <div><div className="stat-value">{studentReport.summary?.attendance_percentage}%</div><div className="stat-label">Rate</div></div>
              </div>
            </div>

            {studentReport.records?.length > 0 && (
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={studentReport.records.slice().reverse().map(r => ({
                    date: r.date?.slice(-2),
                    present: r.status === 'present' ? 1 : r.status === 'late' ? 0.5 : 0,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" fontSize={11} />
                    <YAxis domain={[0, 1]} ticks={[0, 0.5, 1]} fontSize={11}
                           tickFormatter={v => v === 1 ? 'P' : v === 0.5 ? 'L' : 'A'} />
                    <Tooltip contentStyle={{ borderRadius: 8, fontSize: '0.8rem' }} />
                    <Line type="stepAfter" dataKey="present" stroke="#3b82f6" strokeWidth={2}
                          dot={{ fill: '#3b82f6', r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {loading && <div className="loading-spinner"><div className="spinner" /></div>}
      </div>
    </>
  );
}
