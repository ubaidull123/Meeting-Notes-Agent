import { apiClient } from './client';
import {
  AISettings,
  CreditTransaction,
  CredentialPublic,
  EmailSettings,
  MeetingOverride,
  MeetingDefaults,
  NotificationSettings,
  PrivacySettings,
  ProfileSettings,
  ProviderCatalog,
  TranscriptionSettings,
  UsageRecord,
  UsageSummary,
} from '../types/settings';

export const settingsApi = {
  getProfile: async (): Promise<ProfileSettings> => {
    const response = await apiClient.get<ProfileSettings>('/settings/profile');
    return response.data;
  },
  updateProfile: async (data: ProfileSettings): Promise<ProfileSettings> => {
    const response = await apiClient.put<ProfileSettings>('/settings/profile', data);
    return response.data;
  },
  getProviders: async (): Promise<ProviderCatalog> => {
    const response = await apiClient.get<ProviderCatalog>('/settings/providers');
    return response.data;
  },
  getAI: async (): Promise<AISettings> => {
    const response = await apiClient.get<AISettings>('/settings/ai');
    return response.data;
  },
  updateAI: async (data: AISettings): Promise<AISettings> => {
    const payload = {
      llm_usage_mode: data.llm_usage_mode,
      llm_provider: data.llm_provider,
      llm_model: data.llm_model,
      transcription_usage_mode: data.transcription_usage_mode,
      transcription_provider: data.transcription_provider,
      transcription_model: data.transcription_model,
      temperature: data.temperature,
      max_output_tokens: data.max_output_tokens,
      response_language: data.response_language,
    };
    const response = await apiClient.put<AISettings>('/settings/ai', payload);
    return response.data;
  },
  getTranscription: async (): Promise<TranscriptionSettings> => {
    const response = await apiClient.get<TranscriptionSettings>('/settings/transcription');
    return response.data;
  },
  updateTranscription: async (data: TranscriptionSettings): Promise<TranscriptionSettings> => {
    const response = await apiClient.put<TranscriptionSettings>('/settings/transcription', {
      usage_mode: data.usage_mode,
      provider: data.provider,
      model: data.model,
      language: data.language,
    });
    return response.data;
  },
  getMeetingDefaults: async (): Promise<MeetingDefaults> => {
    const response = await apiClient.get<MeetingDefaults>('/settings/meetings');
    return response.data;
  },
  updateMeetingDefaults: async (data: MeetingDefaults): Promise<MeetingDefaults> => {
    const response = await apiClient.put<MeetingDefaults>('/settings/meetings', data);
    return response.data;
  },
  getNotifications: async (): Promise<NotificationSettings> => {
    const response = await apiClient.get<NotificationSettings>('/settings/notifications');
    return response.data;
  },
  updateNotifications: async (data: NotificationSettings): Promise<NotificationSettings> => {
    const payload = {
      processing_finished: data.processing_finished,
      processing_failed: data.processing_failed,
      review_required: data.review_required,
      email_approval_required: data.email_approval_required,
      credits_low: data.credits_low,
    };
    const response = await apiClient.put<NotificationSettings>('/settings/notifications', payload);
    return response.data;
  },
  getPrivacy: async (): Promise<PrivacySettings> => {
    const response = await apiClient.get<PrivacySettings>('/settings/privacy');
    return response.data;
  },
  updatePrivacy: async (data: PrivacySettings): Promise<PrivacySettings> => {
    const payload = { recording_retention: data.recording_retention, keep_transcript: data.keep_transcript };
    const response = await apiClient.put<PrivacySettings>('/settings/privacy', payload);
    return response.data;
  },
  getCredentials: async (): Promise<CredentialPublic[]> => {
    const response = await apiClient.get<CredentialPublic[]>('/settings/credentials');
    return response.data;
  },
  saveCredential: async (provider: string, api_key: string, config?: Record<string, string>): Promise<CredentialPublic> => {
    const response = await apiClient.post<CredentialPublic>('/settings/credentials', { provider, api_key, config });
    return response.data;
  },
  deleteCredential: async (provider: string): Promise<void> => {
    await apiClient.delete(`/settings/credentials/${provider}`);
  },
  testCredential: async (provider: string, api_key?: string | null, config?: Record<string, string>): Promise<{ valid: boolean; provider: string; message: string }> => {
    const response = await apiClient.post('/settings/credentials/test', { provider, api_key, config });
    return response.data;
  },
  getEmail: async (): Promise<EmailSettings> => {
    const response = await apiClient.get<EmailSettings>('/settings/email');
    return response.data;
  },
  updateEmail: async (data: EmailSettings): Promise<EmailSettings> => {
    const response = await apiClient.put<EmailSettings>('/settings/email', data);
    return response.data;
  },
  getCredits: async (): Promise<{ balance: number }> => {
    const response = await apiClient.get<{ balance: number }>('/settings/credits');
    return response.data;
  },
  getTransactions: async (): Promise<CreditTransaction[]> => {
    const response = await apiClient.get<CreditTransaction[]>('/settings/credits/transactions');
    return response.data;
  },
  getUsage: async (): Promise<UsageRecord[]> => {
    const response = await apiClient.get<UsageRecord[]>('/settings/usage');
    return response.data;
  },
  getUsageSummary: async (): Promise<UsageSummary> => {
    const response = await apiClient.get<UsageSummary>('/settings/usage/summary');
    return response.data;
  },
  getOverride: async (meetingId: string): Promise<MeetingOverride> => {
    const response = await apiClient.get<MeetingOverride>(`/settings/meetings/${meetingId}/override`);
    return response.data;
  },
  setOverride: async (meetingId: string, data: MeetingOverride): Promise<MeetingOverride> => {
    const response = await apiClient.put<MeetingOverride>(`/settings/meetings/${meetingId}/override`, data);
    return response.data;
  },
  clearOverride: async (meetingId: string): Promise<void> => {
    await apiClient.delete(`/settings/meetings/${meetingId}/override`);
  },
};
