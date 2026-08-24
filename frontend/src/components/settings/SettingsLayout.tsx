import {
  Bell,
  Bot,
  Captions,
  CreditCard,
  FileLock2,
  Mail,
  Settings2,
  Shield,
  UserRound,
} from 'lucide-react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';

const settingsNavigation = [
  { path: '/settings/profile', label: 'Profile', icon: UserRound },
  { path: '/settings/ai', label: 'AI & Models', icon: Bot },
  { path: '/settings/transcription', label: 'Transcription', icon: Captions },
  { path: '/settings/meetings', label: 'Meeting Defaults', icon: Settings2 },
  { path: '/settings/email', label: 'Email', icon: Mail },
  { path: '/settings/notifications', label: 'Notifications', icon: Bell },
  { path: '/settings/usage', label: 'Credits & Usage', icon: CreditCard },
  { path: '/settings/privacy', label: 'Privacy & Data', icon: FileLock2 },
  { path: '/settings/security', label: 'Security', icon: Shield },
];

export function SettingsLayout() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your account and meeting workflow defaults.</p>
      </header>

      <label className="block md:hidden">
        <span className="sr-only">Settings section</span>
        <select
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={location.pathname}
          onChange={(event) => navigate(event.target.value)}
        >
          {settingsNavigation.map((item) => (
            <option key={item.path} value={item.path}>{item.label}</option>
          ))}
        </select>
      </label>

      <div className="grid gap-8 md:grid-cols-[210px_minmax(0,1fr)]">
        <nav className="hidden space-y-1 md:block" aria-label="Settings">
          {settingsNavigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                  isActive
                    ? 'bg-teal-50 text-teal-800 dark:bg-teal-950/60 dark:text-teal-200'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="min-w-0 max-w-4xl"><Outlet /></div>
      </div>
    </div>
  );
}
