export type TeamRole = 'owner' | 'admin' | 'member';

export interface Team {
  id: string;
  name: string;
  description?: string | null;
  role: TeamRole;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface TeamCreateRequest {
  name: string;
  description?: string | null;
}

export interface TeamUpdateRequest {
  name?: string;
  description?: string | null;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: number;
  role: TeamRole;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  team_id: string;
  name: string;
  description?: string | null;
  context?: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateRequest {
  name: string;
  description?: string | null;
  context?: string | null;
  member_ids?: number[];
}

export interface ProjectUpdateRequest {
  name?: string;
  description?: string | null;
  context?: string | null;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}
