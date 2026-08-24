import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { settingsApi } from '../api/settings';
import { AISettings, MeetingDefaults, NotificationSettings, PrivacySettings, ProfileSettings, TranscriptionSettings } from '../types/settings';

export const settingsKeys = {
  all: ['settings'] as const,
  profile: ['settings', 'profile'] as const,
  providers: ['settings', 'providers'] as const,
  ai: ['settings', 'ai'] as const,
  transcription: ['settings', 'transcription'] as const,
  meetings: ['settings', 'meetings'] as const,
  notifications: ['settings', 'notifications'] as const,
  privacy: ['settings', 'privacy'] as const,
  email: ['settings', 'email'] as const,
  usage: ['settings', 'usage'] as const,
  usageSummary: ['settings', 'usage', 'summary'] as const,
  credentials: ['settings', 'credentials'] as const,
};

export function useProfileSettings() {
  return useQuery({ queryKey: settingsKeys.profile, queryFn: settingsApi.getProfile });
}

export function useProviderCatalog() {
  return useQuery({ queryKey: settingsKeys.providers, queryFn: settingsApi.getProviders });
}

export function useAISettings() {
  return useQuery({ queryKey: settingsKeys.ai, queryFn: settingsApi.getAI });
}

export function useUpdateAISettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AISettings) => settingsApi.updateAI(data),
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.ai, data),
  });
}

export function useTranscriptionSettings() {
  return useQuery({ queryKey: settingsKeys.transcription, queryFn: settingsApi.getTranscription });
}

export function useUpdateTranscriptionSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TranscriptionSettings) => settingsApi.updateTranscription(data),
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.transcription, data),
  });
}

export function useSaveCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ provider, apiKey, config }: { provider: string; apiKey: string; config?: Record<string, string> }) =>
      settingsApi.saveCredential(provider, apiKey, config),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: settingsKeys.all }),
  });
}

export function useTestCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ provider, apiKey, config }: { provider: string; apiKey?: string; config?: Record<string, string> }) =>
      settingsApi.testCredential(provider, apiKey, config),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: settingsKeys.all }),
  });
}

export function useDeleteCredential() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.deleteCredential,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: settingsKeys.all }),
  });
}

export function useMeetingDefaults() {
  return useQuery({ queryKey: settingsKeys.meetings, queryFn: settingsApi.getMeetingDefaults });
}

export function useUpdateMeetingDefaults() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MeetingDefaults) => settingsApi.updateMeetingDefaults(data),
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.meetings, data),
  });
}

export function useNotificationSettings() {
  return useQuery({ queryKey: settingsKeys.notifications, queryFn: settingsApi.getNotifications });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NotificationSettings) => settingsApi.updateNotifications(data),
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.notifications, data),
  });
}

export function usePrivacySettings() {
  return useQuery({ queryKey: settingsKeys.privacy, queryFn: settingsApi.getPrivacy });
}

export function useUpdatePrivacySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PrivacySettings) => settingsApi.updatePrivacy(data),
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.privacy, data),
  });
}

export function useUsageSettings() {
  return useQuery({ queryKey: settingsKeys.usage, queryFn: settingsApi.getUsage });
}

export function useUsageSummary() {
  return useQuery({ queryKey: settingsKeys.usageSummary, queryFn: settingsApi.getUsageSummary });
}

export function useEmailSettings() {
  return useQuery({ queryKey: settingsKeys.email, queryFn: settingsApi.getEmail });
}

export function useUpdateEmailSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.updateEmail,
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.email, data),
  });
}

export function useCredentials() {
  return useQuery({ queryKey: settingsKeys.credentials, queryFn: settingsApi.getCredentials });
}

export function useUpdateProfileSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProfileSettings) => settingsApi.updateProfile(data),
    onSuccess: (data) => queryClient.setQueryData(settingsKeys.profile, data),
  });
}
