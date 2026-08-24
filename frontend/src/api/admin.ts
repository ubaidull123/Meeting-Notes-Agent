import { apiClient } from './client';
import {
  AdminStats,
  AdminUserListItem,
  AdminUserDetail,
  AdminUserUpdate,
  AdminMeetingListItem,
  AdminMeetingStatusResponse,
} from '../types/admin';
import { UserCredits, UserQuota } from '../types/user';

export interface AdminListUsersParams {
  page?: number;
  page_size?: number;
  search?: string;
  role?: string;
  is_active?: boolean;
}

export interface AdminListMeetingsParams {
  page?: number;
  page_size?: number;
  status?: string;
  user_id?: number;
  date_from?: string;
  date_to?: string;
}

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const response = await apiClient.get<AdminStats>('/admin/stats');
    return response.data;
  },

  listUsers: async (params: AdminListUsersParams = {}): Promise<AdminUserListItem[]> => {
    const response = await apiClient.get<AdminUserListItem[]>('/admin/users', { params });
    return response.data;
  },

  getUser: async (userId: number): Promise<AdminUserDetail> => {
    const response = await apiClient.get<AdminUserDetail>(`/admin/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId: number, data: AdminUserUpdate): Promise<AdminUserDetail> => {
    const response = await apiClient.patch<AdminUserDetail>(`/admin/users/${userId}`, data);
    return response.data;
  },

  deleteUser: async (userId: number): Promise<void> => {
    await apiClient.delete(`/admin/users/${userId}`);
  },

  adjustCredits: async (userId: number, amount: number, reason: string): Promise<UserCredits> => {
    const response = await apiClient.post<UserCredits>(`/admin/users/${userId}/credits`, null, {
      params: { amount, reason },
    });
    return response.data;
  },

  adjustQuota: async (userId: number, monthlyLimit: number): Promise<UserQuota> => {
    const response = await apiClient.post<UserQuota>(`/admin/users/${userId}/quota`, null, {
      params: { monthly_limit: monthlyLimit },
    });
    return response.data;
  },

  listMeetings: async (params: AdminListMeetingsParams = {}): Promise<AdminMeetingListItem[]> => {
    const response = await apiClient.get<AdminMeetingListItem[]>('/admin/meetings', { params });
    return response.data;
  },

  getMeetingStatus: async (meetingId: string): Promise<AdminMeetingStatusResponse> => {
    const response = await apiClient.get<AdminMeetingStatusResponse>(`/admin/meetings/${meetingId}`);
    return response.data;
  },

  cancelMeeting: async (meetingId: string): Promise<void> => {
    await apiClient.post(`/admin/meetings/${meetingId}/cancel`);
  },

  retryMeeting: async (meetingId: string): Promise<void> => {
    await apiClient.post(`/admin/meetings/${meetingId}/retry`);
  },
};
