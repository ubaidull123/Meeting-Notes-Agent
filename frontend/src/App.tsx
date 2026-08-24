import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { LoginPage, RegisterPage, MeetingPage, AdminDashboardPage, AdminUsersPage, AdminMeetingsPage } from './pages';
import { DashboardPage } from './pages/DashboardPage';
import { LandingPage } from './pages/LandingPage';
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
import { MembersPage, ProjectPage, ProjectsPage, TeamSettingsPage } from './pages/TeamPages';
import { CreateMeetingWorkspacePage, MeetingsWorkspacePage } from './pages/MeetingWorkspacePages';
import { TasksWorkspacePage } from './pages/TasksWorkspacePage';

export function App() {
  return <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
      <Route path="dashboard" element={<DashboardPage />} />
      <Route path="meetings" element={<MeetingsWorkspacePage />} />
      <Route path="meetings/new" element={<ProtectedRoute requireTeamAdmin><CreateMeetingWorkspacePage /></ProtectedRoute>} />
      <Route path="meetings/:meetingId" element={<MeetingPage />} />
      <Route path="tasks" element={<TasksWorkspacePage />} />
      <Route path="projects" element={<ProjectsPage />} />
      <Route path="projects/:projectId" element={<ProjectPage />} />
      <Route path="members" element={<ProtectedRoute requireTeamAdmin><MembersPage /></ProtectedRoute>} />
      <Route path="team-settings" element={<ProtectedRoute requireTeamAdmin><TeamSettingsPage /></ProtectedRoute>} />
      <Route path="usage" element={<Navigate to="/settings/usage" replace />} />
      <Route path="settings" element={<SettingsLayout />}>
        <Route index element={<Navigate to="profile" replace />} />
        <Route path="profile" element={<ProfileSettingsPage />} />
        <Route path="ai" element={<ProtectedRoute requireTeamAdmin><AISettingsPage /></ProtectedRoute>} />
        <Route path="transcription" element={<ProtectedRoute requireTeamAdmin><TranscriptionSettingsPage /></ProtectedRoute>} />
        <Route path="meetings" element={<ProtectedRoute requireTeamAdmin><MeetingDefaultsPage /></ProtectedRoute>} />
        <Route path="email" element={<ProtectedRoute requireTeamAdmin><EmailSettingsPage /></ProtectedRoute>} />
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
