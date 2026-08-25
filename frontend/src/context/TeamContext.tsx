import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { teamsApi } from '../api/teams';
import { setActiveTeamScope } from '../api/client';
import { Team, TeamRole } from '../types/team';
import { useAuth } from './AuthContext';

interface TeamContextValue {
  teams: Team[];
  activeTeam: Team | null;
  activeRole: TeamRole | null;
  isLoading: boolean;
  canManageActiveTeam: boolean;
  selectTeam: (teamId: string) => void;
  createTeam: (data: { name: string; description?: string | null }) => Promise<Team>;
  roleForTeam: (teamId?: string | null) => TeamRole | null;
  canManageTeam: (teamId?: string | null) => boolean;
  refreshTeams: () => Promise<void>;
}

const TeamContext = createContext<TeamContextValue | undefined>(undefined);
const scopedQueryRoots = new Set([
  'dashboard',
  'projects',
  'project',
  'meetings',
  'meeting',
  'status',
  'review',
  'email-review',
  'tasks',
  'team-members',
  'project-members',
  'meeting-participant-options',
  'task-assignee-options',
]);

export function TeamProvider({ children }: { children: ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTeamId, setActiveTeamId] = useState<string | null>(null);
  const teamsQuery = useQuery({
    queryKey: ['teams', user?.id],
    queryFn: teamsApi.listTeams,
    enabled: isAuthenticated,
  });
  const teams = useMemo(() => teamsQuery.data ?? [], [teamsQuery.data]);

  useEffect(() => {
    if (!user) {
      setActiveTeamId(null);
      return;
    }
    const storageKey = `meeting-notes-active-team:${user.id}`;
    const stored = window.localStorage.getItem(storageKey);
    const next = teams.find(team => team.id === stored)?.id ?? teams[0]?.id ?? null;
    setActiveTeamId(current => teams.some(team => team.id === current) ? current : next);
  }, [teams, user]);

  const activateTeam = useCallback((teamId: string) => {
    if (!user) return;
    window.localStorage.setItem(`meeting-notes-active-team:${user.id}`, teamId);
    setActiveTeamScope(teamId);
    queryClient.removeQueries({
      predicate: query => scopedQueryRoots.has(String(query.queryKey[0])),
    });
    setActiveTeamId(teamId);
    navigate('/dashboard');
  }, [navigate, queryClient, user]);

  const selectTeam = useCallback((teamId: string) => {
    if (!teams.some(team => team.id === teamId) || teamId === activeTeamId) return;
    activateTeam(teamId);
  }, [activateTeam, activeTeamId, teams]);

  const createTeam = useCallback(async (data: { name: string; description?: string | null }) => {
    if (!user) throw new Error('Sign in before creating a workspace.');
    const created = await teamsApi.createTeam(data);
    queryClient.setQueryData<Team[]>(['teams', user.id], current => [
      ...(current ?? []).filter(team => team.id !== created.id),
      created,
    ].sort((left, right) => left.name.localeCompare(right.name)));
    activateTeam(created.id);
    return created;
  }, [activateTeam, queryClient, user]);

  const activeTeam = teams.find(team => team.id === activeTeamId) ?? null;
  useEffect(() => {
    setActiveTeamScope(activeTeam?.id ?? null);
  }, [activeTeam?.id]);
  const roleForTeam = useCallback((teamId?: string | null) => {
    if (!teamId) return null;
    return teams.find(team => team.id === teamId)?.role ?? null;
  }, [teams]);
  const canManageTeam = useCallback((teamId?: string | null) => {
    const role = roleForTeam(teamId);
    return role === 'owner' || role === 'admin';
  }, [roleForTeam]);
  const refreshTeams = useCallback(async () => {
    await teamsQuery.refetch();
  }, [teamsQuery]);

  return <TeamContext.Provider value={{
    teams,
    activeTeam,
    activeRole: activeTeam?.role ?? null,
    isLoading: isAuthenticated && teamsQuery.isLoading,
    canManageActiveTeam: canManageTeam(activeTeam?.id),
    selectTeam,
    createTeam,
    roleForTeam,
    canManageTeam,
    refreshTeams,
  }}>{children}</TeamContext.Provider>;
}

export function useTeam() {
  const context = useContext(TeamContext);
  if (!context) throw new Error('useTeam must be used within a TeamProvider');
  return context;
}
