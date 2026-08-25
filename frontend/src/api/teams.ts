import { apiClient } from './client';
import {
  Project,
  ProjectCreateRequest,
  ProjectMember,
  ProjectUpdateRequest,
  Team,
  TeamCreateRequest,
  TeamMember,
  TeamMemberAddRequest,
  TeamRole,
  TeamUpdateRequest,
} from '../types/team';

export const teamsApi = {
  listTeams: async (): Promise<Team[]> => (await apiClient.get<Team[]>('/teams')).data,
  createTeam: async (data: TeamCreateRequest): Promise<Team> => (await apiClient.post<Team>('/teams', data)).data,
  updateTeam: async (teamId: string, data: TeamUpdateRequest): Promise<Team> => (await apiClient.patch<Team>(`/teams/${teamId}`, data)).data,
  listMembers: async (teamId: string): Promise<TeamMember[]> => (await apiClient.get<TeamMember[]>(`/teams/${teamId}/members`)).data,
  addMember: async (teamId: string, data: TeamMemberAddRequest): Promise<TeamMember> => (await apiClient.post<TeamMember>(`/teams/${teamId}/members`, data)).data,
  updateMemberRole: async (teamId: string, userId: number, role: TeamRole): Promise<TeamMember> => (await apiClient.patch<TeamMember>(`/teams/${teamId}/members/${userId}`, { role })).data,
  removeMember: async (teamId: string, userId: number): Promise<void> => { await apiClient.delete(`/teams/${teamId}/members/${userId}`); },
  revokeInvitation: async (teamId: string, invitationId: string): Promise<void> => { await apiClient.delete(`/teams/${teamId}/invitations/${invitationId}`); },
};

export const projectsApi = {
  listProjects: async (teamId: string): Promise<Project[]> => (await apiClient.get<Project[]>(`/teams/${teamId}/projects`)).data,
  createProject: async (teamId: string, data: ProjectCreateRequest): Promise<Project> => (await apiClient.post<Project>(`/teams/${teamId}/projects`, data)).data,
  getProject: async (projectId: string): Promise<Project> => (await apiClient.get<Project>(`/projects/${projectId}`)).data,
  updateProject: async (projectId: string, data: ProjectUpdateRequest): Promise<Project> => (await apiClient.patch<Project>(`/projects/${projectId}`, data)).data,
  deleteProject: async (projectId: string): Promise<void> => { await apiClient.delete(`/projects/${projectId}`); },
  listMembers: async (projectId: string): Promise<ProjectMember[]> => (await apiClient.get<ProjectMember[]>(`/projects/${projectId}/members`)).data,
  addMember: async (projectId: string, userId: number): Promise<ProjectMember> => (await apiClient.post<ProjectMember>(`/projects/${projectId}/members`, { user_id: userId })).data,
  removeMember: async (projectId: string, userId: number): Promise<void> => { await apiClient.delete(`/projects/${projectId}/members/${userId}`); },
};
