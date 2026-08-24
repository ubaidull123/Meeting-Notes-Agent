import { apiClient } from './client';
import { UserProfileResponse, UserUpdateSelf } from '../types/user';
import { ChangePasswordPayload } from './auth';

export const usersApi = {
  getProfile: async (): Promise<UserProfileResponse> => {
    const response = await apiClient.get<UserProfileResponse>('/users/me');
    return response.data;
  },

  updateProfile: async (payload: UserUpdateSelf): Promise<UserProfileResponse> => {
    const response = await apiClient.patch<UserProfileResponse>('/users/me', payload);
    return response.data;
  },

  changePassword: async (payload: ChangePasswordPayload): Promise<void> => {
    await apiClient.post('/users/me/password', payload);
  },
};
