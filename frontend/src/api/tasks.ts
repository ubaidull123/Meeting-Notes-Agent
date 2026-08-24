import { apiClient } from './client';
import { Task, TaskListResponse, TaskUpdateRequest, TaskStatus } from '../types/task';

export interface ListTasksParams {
  page?: number;
  page_size?: number;
  meeting_id?: string;
  status?: TaskStatus;
  team_id?: string;
  project_id?: string;
}

export const tasksApi = {
  listTasks: async (params: ListTasksParams = {}): Promise<TaskListResponse> => {
    const response = await apiClient.get<TaskListResponse>('/tasks', { params });
    return response.data;
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  updateTask: async (taskId: string, data: TaskUpdateRequest): Promise<Task> => {
    const response = await apiClient.patch<Task>(`/tasks/${taskId}`, data);
    return response.data;
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/tasks/${taskId}`);
  },

  markComplete: async (taskId: string): Promise<Task> => {
    const response = await apiClient.post<Task>(`/tasks/${taskId}/complete`);
    return response.data;
  },
};
