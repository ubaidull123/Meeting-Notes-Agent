import { apiClient } from './client';
import {
  Meeting,
  MeetingListItem,
  MeetingCreateRequest,
  MeetingUpdateRequest,
  MeetingStatus,
  MeetingStatusResponse,
  MeetingResultResponse,
  ReviewContentResponse,
  ReviewRequest,
  ReviewResponse,
  EmailDraftResponse,
  EmailReviewRequest,
  EmailSendResponse,
} from '../types/meeting';

export interface ListMeetingsParams {
  page?: number;
  page_size?: number;
  status?: MeetingStatus;
  team_id?: string;
  project_id?: string;
}

export const meetingsApi = {
  listMeetings: async (params: ListMeetingsParams = {}): Promise<MeetingListItem[]> => {
    const response = await apiClient.get<MeetingListItem[]>('/meetings', { params });
    return response.data;
  },

  getMeeting: async (meetingId: string): Promise<Meeting> => {
    const response = await apiClient.get<Meeting>(`/meetings/${meetingId}`);
    return response.data;
  },

  createMeeting: async (data: MeetingCreateRequest): Promise<Meeting> => {
    const response = await apiClient.post<Meeting>('/meetings', data);
    return response.data;
  },

  updateMeeting: async (meetingId: string, data: MeetingUpdateRequest): Promise<Meeting> => {
    const response = await apiClient.patch<Meeting>(`/meetings/${meetingId}`, data);
    return response.data;
  },

  deleteMeeting: async (meetingId: string): Promise<void> => {
    await apiClient.delete(`/meetings/${meetingId}`);
  },

  uploadAudio: async (meetingId: string, file: File): Promise<{ meeting_id: string; file_path: string; file_size: number; status: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/meetings/${meetingId}/audio`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  uploadTranscript: async (meetingId: string, file: File): Promise<{ meeting_id: string; file_path: string; status: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`/meetings/${meetingId}/transcript`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  startProcessing: async (meetingId: string): Promise<{ meeting_id: string; thread_id: string; status: string; message: string }> => {
    const response = await apiClient.post(`/meetings/${meetingId}/process`);
    return response.data;
  },

  cancelProcessing: async (meetingId: string): Promise<MeetingStatusResponse> => {
    const response = await apiClient.post<MeetingStatusResponse>(`/meetings/${meetingId}/cancel`);
    return response.data;
  },

  getStatus: async (meetingId: string): Promise<MeetingStatusResponse> => {
    const response = await apiClient.get<MeetingStatusResponse>(`/meetings/${meetingId}/status`);
    return response.data;
  },

  getReviewContent: async (meetingId: string): Promise<ReviewContentResponse> => {
    const response = await apiClient.get<ReviewContentResponse>(`/meetings/${meetingId}/review`);
    return response.data;
  },

  submitReview: async (meetingId: string, data: ReviewRequest): Promise<ReviewResponse> => {
    const response = await apiClient.post<ReviewResponse>(`/meetings/${meetingId}/review`, data);
    return response.data;
  },

  getEmailDraft: async (meetingId: string): Promise<EmailDraftResponse> => {
    const response = await apiClient.get<EmailDraftResponse>(`/meetings/${meetingId}/email-review`);
    return response.data;
  },

  submitEmailReview: async (meetingId: string, data: EmailReviewRequest): Promise<EmailSendResponse> => {
    const response = await apiClient.post<EmailSendResponse>(`/meetings/${meetingId}/email-review`, data);
    return response.data;
  },

  getResults: async (meetingId: string): Promise<MeetingResultResponse> => {
    const response = await apiClient.get<MeetingResultResponse>(`/meetings/${meetingId}/results`);
    return response.data;
  },
};
