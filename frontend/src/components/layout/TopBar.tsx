import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { ConfirmDialog } from '../ui/ConfirmDialog';
import {
  Menu,
  Sun,
  Moon,
  Laptop,
  LogOut,
  User,
  Settings,
  Shield,
  CreditCard,
} from 'lucide-react';

interface TopBarProps {
  onOpenMobileMenu: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onOpenMobileMenu }) => {
  const { user, profile, logout, isAdmin } = useAuth();
  const { theme, setTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isThemeMenuOpen, setIsThemeMenuOpen] = useState(false);
  const [isLogoutDialogOpen, setIsLogoutDialogOpen] = useState(false);

  const userMenuRef = useRef<HTMLDivElement>(null);
  const themeMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
      if (themeMenuRef.current && !themeMenuRef.current.contains(event.target as Node)) {
        setIsThemeMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getPageContext = (): { parent?: { label: string; path: string }; label: string } => {
    const path = location.pathname;
    if (path === '/dashboard' || path === '/') return { label: 'Dashboard' };
    if (path === '/meetings') return { label: 'Meetings' };
    if (path === '/meetings/new') return { parent: { label: 'Meetings', path: '/meetings' }, label: 'Create meeting' };
    if (path.startsWith('/meetings/')) return { parent: { label: 'Meetings', path: '/meetings' }, label: 'Meeting details' };
    if (path === '/tasks') return { label: 'Tasks' };
    if (path === '/projects') return { label: 'Projects' };
    if (path.startsWith('/projects/')) return { parent: { label: 'Projects', path: '/projects' }, label: 'Project details' };
    if (path === '/members') return { label: 'Team members' };
    if (path === '/team-settings') return { label: 'Team settings' };
    if (path === '/usage') return { parent: { label: 'Settings', path: '/settings/profile' }, label: 'Usage & credits' };
    if (path.startsWith('/settings')) return { label: 'Settings' };
    if (path === '/admin') return { label: 'Admin dashboard' };
    if (path === '/admin/users') return { parent: { label: 'Admin', path: '/admin' }, label: 'Users' };
    if (path === '/admin/meetings') return { parent: { label: 'Admin', path: '/admin' }, label: 'Meetings audit' };
    return { label: 'Meeting Notes Agent' };
  };

  const pageContext = getPageContext();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <>
      <header className="h-16 border-b border-border bg-card/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30">
        {/* Left Side: Mobile Menu Button & Page Title */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="md:hidden p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>
          <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-2 text-sm sm:text-base">
            {pageContext.parent && <>
              <Link className="font-medium text-muted-foreground transition-colors hover:text-foreground" to={pageContext.parent.path}>{pageContext.parent.label}</Link>
              <span className="text-muted-foreground/60" aria-hidden="true">/</span>
            </>}
            <span className="truncate font-semibold text-foreground">{pageContext.label}</span>
          </nav>
        </div>

        {/* Right Side: Usage pill, Theme toggle, User profile */}
        <div className="flex items-center gap-3">
          {/* Quick credits indicator */}
          {profile?.credits && (
            <div
              onClick={() => navigate('/settings/usage')}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1 text-xs font-medium bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 rounded-full cursor-pointer hover:opacity-90 transition-opacity"
              title="Available Credits"
            >
              <CreditCard className="w-3.5 h-3.5" />
              <span>{profile.credits.balance} credits</span>
            </div>
          )}

          {/* Theme Selector */}
          <div className="relative" ref={themeMenuRef}>
            <button
              type="button"
              onClick={() => setIsThemeMenuOpen(!isThemeMenuOpen)}
              className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Switch theme"
            >
              {theme === 'dark' ? (
                <Moon className="w-4 h-4" />
              ) : theme === 'light' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Laptop className="w-4 h-4" />
              )}
            </button>

            {isThemeMenuOpen && (
              <div className="absolute right-0 mt-2 w-36 rounded-xl border bg-card p-1 shadow-lg z-50 text-xs">
                <button
                  type="button"
                  onClick={() => {
                    setTheme('light');
                    setIsThemeMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left hover:bg-muted transition-colors"
                >
                  <Sun className="w-4 h-4 text-amber-500" />
                  <span>Light</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTheme('dark');
                    setIsThemeMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left hover:bg-muted transition-colors"
                >
                  <Moon className="w-4 h-4 text-indigo-400" />
                  <span>Dark</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTheme('system');
                    setIsThemeMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left hover:bg-muted transition-colors"
                >
                  <Laptop className="w-4 h-4 text-slate-400" />
                  <span>System</span>
                </button>
              </div>
            )}
          </div>

          {/* User Profile Dropdown */}
          <div className="relative" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-muted transition-colors focus:outline-none"
            >
              <div className="w-7 h-7 rounded-full bg-teal-600 text-white flex items-center justify-center text-xs font-semibold">
                {user?.full_name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="hidden sm:inline text-xs font-medium text-foreground max-w-[120px] truncate">
                {user?.full_name || 'Account'}
              </span>
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl border bg-card p-2 shadow-xl z-50 animate-in fade-in zoom-in-95">
                <div className="px-3 py-2 border-b border-border mb-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-foreground truncate">{user?.full_name}</p>
                    {isAdmin && (
                      <span className="px-1.5 py-0.5 text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 rounded">
                        ADMIN
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">{user?.email}</p>
                </div>

                <div className="space-y-0.5 text-xs">
                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      navigate('/settings/profile');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-foreground hover:bg-muted transition-colors text-left"
                  >
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span>My Profile</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      navigate('/settings/usage');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-foreground hover:bg-muted transition-colors text-left"
                  >
                    <CreditCard className="w-4 h-4 text-muted-foreground" />
                    <span>Usage & Credits</span>
                  </button>

                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() => {
                        setIsUserMenuOpen(false);
                        navigate('/admin');
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-950/40 transition-colors text-left font-medium"
                    >
                      <Shield className="w-4 h-4 text-amber-600" />
                      <span>Admin Center</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      navigate('/settings/profile');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-foreground hover:bg-muted transition-colors text-left"
                  >
                    <Settings className="w-4 h-4 text-muted-foreground" />
                    <span>Settings</span>
                  </button>

                  <div className="pt-1 border-t border-border mt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setIsUserMenuOpen(false);
                        setIsLogoutDialogOpen(true);
                      }}
                      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors text-left"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Logout Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isLogoutDialogOpen}
        onClose={() => setIsLogoutDialogOpen(false)}
        onConfirm={handleLogout}
        title="Sign Out"
        description="Are you sure you want to sign out of your account?"
        confirmLabel="Sign Out"
      />
    </>
  );
};
