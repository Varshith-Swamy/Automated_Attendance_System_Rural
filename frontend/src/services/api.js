const API_BASE = '/api';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw { status: response.status, message: data.error || 'Request failed', data };
      }
      return data;
    } catch (err) {
      if (err.status) throw err;
      throw { status: 0, message: 'Network error - working offline?', data: null };
    }
  }

  // Auth
  async login(username, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    this.setToken(data.token);
    return data;
  }

  logout() {
    this.setToken(null);
    localStorage.removeItem('user');
  }

  async getMe() {
    return this.request('/auth/me');
  }

  // Students
  async getStudents(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/students?${query}`);
  }

  async getStudent(id) {
    return this.request(`/students/${id}`);
  }

  async registerStudent(data) {
    return this.request('/students/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateStudent(id, data) {
    return this.request(`/students/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async addFaceSamples(id, faceImages) {
    return this.request(`/students/${id}/add-faces`, {
      method: 'POST',
      body: JSON.stringify({ face_images: faceImages }),
    });
  }

  async getClasses() {
    return this.request('/students/classes');
  }

  // Attendance
  async recognizeFace(imageBase64) {
    return this.request('/attendance/recognize', {
      method: 'POST',
      body: JSON.stringify({ image: imageBase64 }),
    });
  }

  async markAttendance(data) {
    return this.request('/attendance/mark', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getDailyAttendance(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/attendance/daily?${query}`);
  }

  async updateAttendance(id, data) {
    return this.request(`/attendance/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Reports
  async getStudentReport(id, params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/reports/student/${id}?${query}`);
  }

  async getClassReport(id, params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/reports/class/${id}?${query}`);
  }

  async getExportUrl(params = {}) {
    const query = new URLSearchParams(params).toString();
    return `${API_BASE}/reports/export?${query}`;
  }

  async getMonthlySummary(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/reports/monthly-summary?${query}`);
  }

  // Dashboard
  async getDashboardSummary() {
    return this.request('/dashboard/summary');
  }

  // Sync
  async getSyncStatus() {
    return this.request('/sync/status');
  }

  async triggerSync() {
    return this.request('/sync/upload', { method: 'POST' });
  }

  async getAuditLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/sync/logs?${query}`);
  }
}

const api = new ApiService();
export default api;
