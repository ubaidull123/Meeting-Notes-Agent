import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../utils/cn';
import {
  LayoutDashboard,
  Calendar,
  CheckSquare,
  ShieldAlert,
  Users,
  Layers,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  onNavigateMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isCollapsed,
  onToggleCollapse,
  onNavigateMobile,
}) => {
  const { isAdmin } = useAuth();
  const location = useLocation();

  const userNavItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { label: 'Meetings', icon: Calendar, path: '/meetings' },
    { label: 'Tasks', icon: CheckSquare, path: '/tasks' },
  ];

  const adminNavItems = [
    { label: 'Admin Overview', icon: ShieldAlert, path: '/admin' },
    { label: 'Manage Users', icon: Users, path: '/admin/users' },
    { label: 'All Meetings', icon: Layers, path: '/admin/meetings' },
  ];

  const handleLinkClick = () => {
    if (onNavigateMobile) {
      onNavigateMobile();
    }
  };

  return (
    <aside
      className={cn(
        'relative flex flex-col border-r border-border bg-card transition-all duration-200 ease-in-out select-none',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-border gap-3">
        <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white shrink-0 shadow-sm">
          <Sparkles className="w-4 h-4" />
        </div>
        {!isCollapsed && (
          <div className="flex flex-col overflow-hidden">
            <span className="font-semibold text-sm text-foreground truncate tracking-tight">
              Meeting Notes Agent
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">v1.0 AI Pipeline</span>
          </div>
        )}
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {/* User Navigation */}
        <div className="space-y-1">
          {!isCollapsed && (
            <p className="px-3 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Workspace
            </p>
          )}
          {userNavItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.path === '/dashboard'
                ? location.pathname === '/dashboard' || location.pathname === '/'
                : location.pathname.startsWith(item.path);

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={handleLinkClick}
                title={isCollapsed ? item.label : undefined}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300 font-semibold'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                  isCollapsed && 'justify-center px-2'
                )}
              >
                <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-teal-600 dark:text-teal-400' : '')} />
                {!isCollapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </div>

        {/* Admin Navigation */}
        {isAdmin && (
          <div className="space-y-1 pt-3 border-t border-border">
            {!isCollapsed && (
              <div className="px-3 flex items-center justify-between mb-2">
                <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Administration
                </p>
                <span className="px-1.5 py-0.2 text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 rounded">
                  Admin
                </span>
              </div>
            )}
            {adminNavItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                item.path === '/admin'
                  ? location.pathname === '/admin'
                  : location.pathname.startsWith(item.path);

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={handleLinkClick}
                  title={isCollapsed ? item.label : undefined}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 font-semibold'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    isCollapsed && 'justify-center px-2'
                  )}
                >
                  <Icon className={cn('w-4 h-4 shrink-0', isActive ? 'text-amber-600 dark:text-amber-400' : '')} />
                  {!isCollapsed && <span>{item.label}</span>}
                </NavLink>
              );
            })}
          </div>
        )}
      </div>

      {/* Workspace-only footer */}
      <div className="p-3 border-t border-border flex items-center justify-end">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="hidden md:flex p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors ml-auto"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};
