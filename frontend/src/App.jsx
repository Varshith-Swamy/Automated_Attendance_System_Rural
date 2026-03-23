import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import StudentRegistrationPage from './pages/StudentRegistrationPage';
import LiveAttendancePage from './pages/LiveAttendancePage';
import AttendanceRecordsPage from './pages/AttendanceRecordsPage';
import ReportsPage from './pages/ReportsPage';
import SyncPage from './pages/SyncPage';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="register" element={<StudentRegistrationPage />} />
        <Route path="attendance" element={<LiveAttendancePage />} />
        <Route path="records" element={<AttendanceRecordsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="sync" element={<SyncPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
