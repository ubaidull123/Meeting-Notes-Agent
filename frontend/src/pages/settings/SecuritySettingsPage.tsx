import { FormEvent, useState } from 'react';
import { LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { authApi } from '../../api/auth';
import { SettingsSection, settingsFieldClass } from '../../components/settings/SettingsControls';
import { useAuth } from '../../context/AuthContext';
import { formatErrorMessage } from '../../utils/errors';

export function SecuritySettingsPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [saving, setSaving] = useState(false);

  const changePassword = async (event: FormEvent) => {
    event.preventDefault();
    if (form.new_password !== form.confirm_password) { toast.error('New passwords do not match'); return; }
    if (form.new_password.length < 8) { toast.error('New password must be at least 8 characters'); return; }
    setSaving(true);
    try {
      await authApi.changePassword({ current_password: form.current_password, new_password: form.new_password });
      setForm({ current_password: '', new_password: '', confirm_password: '' });
      toast.success('Password changed');
    } catch (error) { toast.error(formatErrorMessage(error)); } finally { setSaving(false); }
  };

  const signOut = async () => { await logout(); navigate('/login', { replace: true }); };

  return (
    <div>
      <SettingsSection title="Change password" description="Use a unique password with at least eight characters.">
        <form onSubmit={changePassword} className="max-w-md space-y-4">
          <label className="block text-sm font-medium">Current password<input className={settingsFieldClass} type="password" autoComplete="current-password" required value={form.current_password} onChange={(event) => setForm({ ...form, current_password: event.target.value })} /></label>
          <label className="block text-sm font-medium">New password<input className={settingsFieldClass} type="password" autoComplete="new-password" required minLength={8} value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })} /></label>
          <label className="block text-sm font-medium">Confirm new password<input className={settingsFieldClass} type="password" autoComplete="new-password" required minLength={8} value={form.confirm_password} onChange={(event) => setForm({ ...form, confirm_password: event.target.value })} /></label>
          <button disabled={saving} className="rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50">{saving ? 'Changing...' : 'Change password'}</button>
        </form>
      </SettingsSection>
      <SettingsSection title="Session" description="This application currently uses a single stateless browser session.">
        <button type="button" onClick={signOut} className="inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted"><LogOut className="h-4 w-4" />Log out</button>
        <p className="mt-3 text-sm text-muted-foreground">Active session management is not supported by the current authentication backend.</p>
      </SettingsSection>
    </div>
  );
}
