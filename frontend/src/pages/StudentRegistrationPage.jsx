import React, { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import api from '../services/api';

export default function StudentRegistrationPage() {
  const [formData, setFormData] = useState({
    student_id: '',
    name: '',
    class_id: '',
    section: 'A',
    guardian_name: '',
    guardian_phone: '',
    gender: 'male',
  });
  const [classes, setClasses] = useState([]);
  const [capturedImages, setCapturedImages] = useState([]);
  const [showCamera, setShowCamera] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const webcamRef = useRef(null);

  useEffect(() => {
    api.getClasses().then(d => setClasses(d.classes || [])).catch(() => {});
    // Generate a default student ID
    const year = new Date().getFullYear();
    const rand = Math.floor(Math.random() * 9000) + 1000;
    setFormData(prev => ({ ...prev, student_id: `STU-${year}-${rand}` }));
  }, []);

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const capturePhoto = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        // Remove the data URL prefix to get base64
        const base64 = imageSrc.split(',')[1];
        setCapturedImages(prev => [...prev, { src: imageSrc, base64 }]);

        if (capturedImages.length >= 4) {
          setShowCamera(false);
        }
      }
    }
  }, [capturedImages]);

  const removeImage = (index) => {
    setCapturedImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);

    if (!formData.student_id || !formData.name || !formData.class_id) {
      setMessage({ type: 'error', text: 'Please fill in Student ID, Name, and Class.' });
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...formData,
        class_id: parseInt(formData.class_id),
        face_images: capturedImages.map(img => img.base64),
      };

      const result = await api.registerStudent(payload);
      setMessage({
        type: 'success',
        text: `✅ ${result.student.name} registered successfully! ${result.embeddings_saved} face samples saved.`,
      });

      // Reset form
      setFormData({
        student_id: `STU-${new Date().getFullYear()}-${Math.floor(Math.random() * 9000) + 1000}`,
        name: '',
        class_id: '',
        section: 'A',
        guardian_name: '',
        guardian_phone: '',
        gender: 'male',
      });
      setCapturedImages([]);
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Registration failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Register Student</h1>
          <p className="page-subtitle">Add a new student with face samples for attendance</p>
        </div>
      </div>

      <div className="page-body">
        {message && (
          <div className={`alert ${message.type === 'error' ? 'alert-error' : 'alert-success'}`}>
            {message.text}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Student Info Form */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📝 Student Information</h3>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-student-id">Student ID</label>
                  <input id="reg-student-id" type="text" className="form-input" name="student_id"
                         value={formData.student_id} onChange={handleChange} required />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-name">Full Name</label>
                  <input id="reg-name" type="text" className="form-input" name="name"
                         value={formData.name} onChange={handleChange} placeholder="e.g., Aarav Sharma" required />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-class">Class</label>
                  <select id="reg-class" className="form-select" name="class_id"
                          value={formData.class_id} onChange={handleChange} required>
                    <option value="">Select class</option>
                    {classes.map(c => (
                      <option key={c.id} value={c.id}>{c.name} - {c.section}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-section">Section</label>
                  <select id="reg-section" className="form-select" name="section"
                          value={formData.section} onChange={handleChange}>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-guardian">Guardian Name</label>
                  <input id="reg-guardian" type="text" className="form-input" name="guardian_name"
                         value={formData.guardian_name} onChange={handleChange} placeholder="Parent/Guardian name" />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="reg-phone">Guardian Phone</label>
                  <input id="reg-phone" type="tel" className="form-input" name="guardian_phone"
                         value={formData.guardian_phone} onChange={handleChange} placeholder="10-digit number" />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="reg-gender">Gender</label>
                <select id="reg-gender" className="form-select" name="gender"
                        value={formData.gender} onChange={handleChange}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%' }}
                      disabled={loading}>
                {loading ? 'Registering...' : `Register Student (${capturedImages.length} face samples)`}
              </button>
            </form>
          </div>

          {/* Face Capture */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📸 Face Samples</h3>
              <button className="btn btn-outline btn-sm" onClick={() => setShowCamera(!showCamera)}>
                {showCamera ? 'Close Camera' : 'Open Camera'}
              </button>
            </div>

            {showCamera && (
              <div style={{ marginBottom: '16px' }}>
                <div className="camera-container" style={{ maxWidth: '100%' }}>
                  <Webcam
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    screenshotQuality={0.8}
                    videoConstraints={{ width: 480, height: 360, facingMode: 'user' }}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                  <div className="camera-overlay">
                    <div className="face-guide" />
                  </div>
                  <div className="camera-status">
                    Position your face in the oval • {capturedImages.length}/5 captured
                  </div>
                </div>
                <button className="btn btn-success" style={{ width: '100%', marginTop: '12px' }}
                        onClick={capturePhoto} disabled={capturedImages.length >= 5}>
                  📸 Capture ({capturedImages.length}/5)
                </button>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {capturedImages.map((img, i) => (
                <div key={i} style={{ position: 'relative', borderRadius: '8px', overflow: 'hidden', border: '2px solid var(--surface-200)' }}>
                  <img src={img.src} alt={`Sample ${i + 1}`} style={{ width: '100%', display: 'block' }} />
                  <button
                    onClick={() => removeImage(i)}
                    style={{
                      position: 'absolute', top: 4, right: 4,
                      background: 'rgba(239,68,68,0.9)', color: 'white',
                      border: 'none', borderRadius: '50%', width: 22, height: 22,
                      cursor: 'pointer', fontSize: '12px', lineHeight: 1,
                    }}
                  >✕</button>
                  <div style={{
                    position: 'absolute', bottom: 0, left: 0, right: 0,
                    background: 'rgba(0,0,0,0.6)', color: 'white',
                    fontSize: '0.7rem', textAlign: 'center', padding: '2px',
                  }}>
                    Sample {i + 1}
                  </div>
                </div>
              ))}
            </div>

            {capturedImages.length === 0 && !showCamera && (
              <div className="empty-state">
                <p>📷 Open camera to capture face samples<br/>
                   <small>Minimum 3 samples recommended for accuracy</small></p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
