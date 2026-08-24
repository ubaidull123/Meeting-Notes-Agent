import { apiClient } from './client';
import { TokenResponse } from '../types/auth';
import { UserProfileResponse } from '../types/user';

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export const authApi = {
  register: async (payload: RegisterPayload): Promise<UserProfileResponse> => {
    const response = await apiClient.post<UserProfileResponse>('/auth/register', payload);
    return response.data;
  },

  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', payload);
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  getMe: async (): Promise<UserProfileResponse> => {
    const response = await apiClient.get<UserProfileResponse>('/auth/me');
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // Best-effort logout
    }
  },

  changePassword: async (payload: ChangePasswordPayload): Promise<void> => {
    await apiClient.post('/auth/me/password', payload);
  },
};
