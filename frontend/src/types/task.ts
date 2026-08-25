export type TaskStatus = 'todo' | 'in_progress' | 'in_review' | 'done' | 'blocked';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string; // 8-character string
  meeting_id: string;
  team_id: string;
  project_id?: string | null;
  assigned_user_id?: number | null;
  meeting_title: string;
  title: string;
  description?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assignee?: string | null;
  due_date?: string | null;
  labels: string[];
  action_item_index: number;
  github_issue_number?: number | null;
  github_issue_url?: string | null;
  synced_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateRequest {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee?: string | null;
  assigned_user_id?: number | null;
  due_date?: string | null;
  labels?: string[];
  meeting_id: string;
  meeting_title: string;
  action_item_index: number;
}

export interface TaskUpdateRequest {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee?: string | null;
  assigned_user_id?: number | null;
  due_date?: string | null;
  labels?: string[];
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
  page: number;
  page_size: number;
}
