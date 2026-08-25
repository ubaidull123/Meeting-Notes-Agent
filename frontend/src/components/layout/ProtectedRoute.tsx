import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../ui/LoadingState';
import { ShieldAlert } from 'lucide-react';
import { useTeam } from '../../context/TeamContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
  requireTeamAdmin?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAdmin = false,
  requireTeamAdmin = false,
}) => {
  const { isAuthenticated, isLoading, isAdmin } = useAuth();
  const { canManageActiveTeam, isLoading: isTeamLoading } = useTeam();
  const location = useLocation();

  if (isLoading || (isAuthenticated && isTeamLoading)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner size="lg" label="Authenticating session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if ((requireAdmin && !isAdmin) || (requireTeamAdmin && !canManageActiveTeam)) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center mt-12 rounded-2xl border border-border bg-card shadow-sm">
        <div className="w-12 h-12 rounded-full bg-rose-100 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">Access Restricted</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          You do not have the required administrative privileges to view this section.
        </p>
        <a
          href="/dashboard"
          className="mt-6 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition-colors"
        >
          Return to Dashboard
        </a>
      </div>
    );
  }

  return <>{children}</>;
};
