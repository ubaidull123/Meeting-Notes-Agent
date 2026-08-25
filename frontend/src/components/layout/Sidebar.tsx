import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTeam } from '../../context/TeamContext';
import { cn } from '../../utils/cn';
import { BrandMark } from '../ui/BrandMark';
import {
  LayoutDashboard,
  Calendar,
  CheckSquare,
  ShieldAlert,
  Users,
  Layers,
  FolderKanban,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';

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
  const { canManageActiveTeam } = useTeam();
  const location = useLocation();

  const memberNavItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { label: 'My Tasks', icon: CheckSquare, path: '/tasks' },
    { label: 'Projects', icon: FolderKanban, path: '/projects' },
    { label: 'Meetings', icon: Calendar, path: '/meetings' },
  ];

  const managerNavItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { label: 'Projects', icon: FolderKanban, path: '/projects' },
    { label: 'Meetings', icon: Calendar, path: '/meetings' },
    { label: 'Tasks', icon: CheckSquare, path: '/tasks' },
    { label: 'Members', icon: Users, path: '/members' },
    { label: 'Team Settings', icon: Settings, path: '/team-settings' },
  ];
  const userNavItems = canManageActiveTeam ? managerNavItems : memberNavItems;

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
        'sticky top-0 flex h-screen flex-col select-none border-r border-border/80 bg-card transition-all duration-200 ease-in-out',
        isCollapsed ? 'w-[4.25rem]' : 'w-[17rem]'
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 border-b border-border/70 px-4">
        <BrandMark />
        {!isCollapsed && (
          <div className="flex flex-col overflow-hidden">
            <span className="truncate text-sm font-semibold tracking-tight text-foreground">
              Meeting Notes
            </span>
            <span className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">Team workspace</span>
          </div>
        )}
      </div>

      <div className="border-b border-border/70 p-3"><WorkspaceSwitcher collapsed={isCollapsed} /></div>

      {/* Navigation Sections */}
      <div className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        {/* User Navigation */}
        <div className="space-y-1">
          {!isCollapsed && (
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
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
                  'relative flex min-h-9 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 font-semibold text-primary before:absolute before:-left-3 before:h-5 before:w-0.5 before:rounded-r-full before:bg-primary'
                    : 'text-muted-foreground hover:bg-muted/80 hover:text-foreground',
                  isCollapsed && 'justify-center px-2'
                )}
              >
                <Icon className={cn('h-4 w-4 shrink-0', isActive && 'text-primary')} />
                {!isCollapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </div>

        {/* Admin Navigation */}
        {isAdmin && (
          <div className="space-y-1 border-t border-border/70 pt-4">
            {!isCollapsed && (
              <div className="px-3 flex items-center justify-between mb-2">
                <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Platform
                </p>
                <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
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
                    'relative flex min-h-9 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-amber-50 font-semibold text-amber-800 before:absolute before:-left-3 before:h-5 before:w-0.5 before:rounded-r-full before:bg-amber-500 dark:bg-amber-950/50 dark:text-amber-300'
                      : 'text-muted-foreground hover:bg-muted/80 hover:text-foreground',
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
      <div className="flex items-center justify-end border-t border-border/70 p-3">
        <button
          type="button"
          onClick={onToggleCollapse}
          className="ml-auto hidden rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:flex"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};
