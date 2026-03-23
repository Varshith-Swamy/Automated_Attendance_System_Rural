import React, { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import api from '../services/api';

export default function LiveAttendancePage() {
  const [isActive, setIsActive] = useState(false);
  const [recognitionResults, setRecognitionResults] = useState([]);
  const [todayLog, setTodayLog] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [autoCapture, setAutoCapture] = useState(false);
  const [statusMsg, setStatusMsg] = useState('Camera ready');
  const webcamRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchTodayLog();
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  const fetchTodayLog = async () => {
    try {
      const result = await api.getDailyAttendance({});
      setTodayLog(result.attendance || []);
    } catch (err) {
      console.error(err);
    }
  };

  const captureAndRecognize = useCallback(async () => {
    if (!webcamRef.current || processing) return;

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return;

    const base64 = imageSrc.split(',')[1];
    setProcessing(true);
    setStatusMsg('Processing...');

    try {
      const result = await api.markAttendance({ image: base64 });
      const newResults = result.results || [];

      setRecognitionResults(newResults);

      const marked = newResults.filter(r => r.recognized && r.message === 'Attendance marked');
      if (marked.length > 0) {
        setStatusMsg(`✅ Marked: ${marked.map(m => m.student?.name).join(', ')}`);
        fetchTodayLog();
      } else if (newResults.some(r => r.message === 'Already marked today')) {
        setStatusMsg('Already marked today');
      } else if (newResults.some(r => !r.recognized)) {
        setStatusMsg('⚠️ Unknown face or low confidence');
      } else {
        setStatusMsg('No face detected');
      }

      // Clear results after 3 seconds
      setTimeout(() => {
        setRecognitionResults([]);
        setStatusMsg(autoCapture ? 'Auto-scanning...' : 'Camera ready');
      }, 3000);

    } catch (err) {
      setStatusMsg(err.message || 'Recognition failed');
      setTimeout(() => setStatusMsg('Camera ready'), 3000);
    } finally {
      setProcessing(false);
    }
  }, [processing, autoCapture]);

  const toggleAutoCapture = () => {
    if (autoCapture) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      setAutoCapture(false);
      setStatusMsg('Camera ready');
    } else {
      setAutoCapture(true);
      setStatusMsg('Auto-scanning...');
      intervalRef.current = setInterval(() => {
        captureAndRecognize();
      }, 4000);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Mark Attendance</h1>
          <p className="page-subtitle">Face recognition-based attendance marking</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className={`btn ${autoCapture ? 'btn-danger' : 'btn-success'}`} onClick={toggleAutoCapture}>
            {autoCapture ? '⏹ Stop Auto-Scan' : '▶ Auto-Scan'}
          </button>
        </div>
      </div>

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Camera Feed */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📸 Camera Feed</h3>
              <span className={`badge ${autoCapture ? 'badge-present' : 'badge-info'}`}>
                {autoCapture ? 'Auto-scanning' : 'Manual'}
              </span>
            </div>

            <div className="camera-container" style={{ maxWidth: '100%' }}>
              <Webcam
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                screenshotQuality={0.8}
                videoConstraints={{ width: 640, height: 480, facingMode: 'user' }}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />

              {/* Recognition overlay */}
              {recognitionResults.map((r, i) =>
                r.recognized ? (
                  <div key={i} className="recognition-result">
                    ✅ {r.student?.name} ({r.student?.student_id}) · {(r.confidence * 100).toFixed(1)}%
                  </div>
                ) : (
                  <div key={i} className="recognition-result unknown">
                    ❌ Unknown Face
                  </div>
                )
              )}

              <div className="camera-status">{statusMsg}</div>
            </div>

            {!autoCapture && (
              <button className="btn btn-primary" style={{ width: '100%', marginTop: '12px' }}
                      onClick={captureAndRecognize} disabled={processing}>
                {processing ? 'Processing...' : '📸 Capture & Recognize'}
              </button>
            )}
          </div>

          {/* Today's Attendance Log */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📋 Today&apos;s Attendance ({todayLog.length})</h3>
              <button className="btn btn-outline btn-sm" onClick={fetchTodayLog}>Refresh</button>
            </div>

            {todayLog.length > 0 ? (
              <ul className="attendance-log" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                {todayLog.map(record => (
                  <li key={record.id} className="attendance-log-item">
                    <div className="log-avatar">
                      {record.student_name?.charAt(0) || '?'}
                    </div>
                    <div className="log-details">
                      <div className="log-name">{record.student_name}</div>
                      <div className="log-meta">{record.student_id} · {record.marked_by}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className={`badge badge-${record.status}`}>{record.status}</span>
                      <div className="log-time">{record.time_in?.slice(0, 5)}</div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="empty-state">
                <p>No attendance recorded yet today</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
