import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { LoginPage, RegisterPage, MeetingsPage, CreateMeetingPage, MeetingPage, TasksPage, AdminDashboardPage, AdminUsersPage, AdminMeetingsPage } from './pages';
import { DashboardPage } from './pages/DashboardPage';
import { SettingsLayout } from './components/settings/SettingsLayout';
import { ProfileSettingsPage } from './pages/settings/ProfileSettingsPage';
import { AISettingsPage } from './pages/settings/AISettingsPage';
import { TranscriptionSettingsPage } from './pages/settings/TranscriptionSettingsPage';
import { MeetingDefaultsPage } from './pages/settings/MeetingDefaultsPage';
import { NotificationSettingsPage } from './pages/settings/NotificationSettingsPage';
import { PrivacySettingsPage } from './pages/settings/PrivacySettingsPage';
import { SecuritySettingsPage } from './pages/settings/SecuritySettingsPage';
import { UsageSettingsPage } from './pages/settings/UsageSettingsPage';
import { EmailSettingsPage } from './pages/settings/EmailSettingsPage';

export function App() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
      <Route index element={<Navigate to="/dashboard" replace />} />
      <Route path="dashboard" element={<DashboardPage />} />
      <Route path="meetings" element={<MeetingsPage />} />
      <Route path="meetings/new" element={<CreateMeetingPage />} />
      <Route path="meetings/:meetingId" element={<MeetingPage />} />
      <Route path="tasks" element={<TasksPage />} />
      <Route path="usage" element={<Navigate to="/settings/usage" replace />} />
      <Route path="settings" element={<SettingsLayout />}>
        <Route index element={<Navigate to="profile" replace />} />
        <Route path="profile" element={<ProfileSettingsPage />} />
        <Route path="ai" element={<AISettingsPage />} />
        <Route path="transcription" element={<TranscriptionSettingsPage />} />
        <Route path="meetings" element={<MeetingDefaultsPage />} />
        <Route path="email" element={<EmailSettingsPage />} />
        <Route path="notifications" element={<NotificationSettingsPage />} />
        <Route path="usage" element={<UsageSettingsPage />} />
        <Route path="privacy" element={<PrivacySettingsPage />} />
        <Route path="security" element={<SecuritySettingsPage />} />
      </Route>
      <Route path="admin" element={<ProtectedRoute requireAdmin><AdminDashboardPage /></ProtectedRoute>} />
      <Route path="admin/users" element={<ProtectedRoute requireAdmin><AdminUsersPage /></ProtectedRoute>} />
      <Route path="admin/meetings" element={<ProtectedRoute requireAdmin><AdminMeetingsPage /></ProtectedRoute>} />
    </Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>;
}
