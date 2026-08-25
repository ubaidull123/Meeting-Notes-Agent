import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { meetingsApi } from './api/meetings';
import { MeetingReviewPage, shouldPollMeetingStatus } from './reviewMeetingPage';
import { Meeting } from './types/meeting';

const roleState = vi.hoisted(() => ({ canManage: true }));

vi.mock('./api/meetings', () => ({
  meetingsApi: {
    getMeeting: vi.fn(),
    getStatus: vi.fn(),
    getReviewContent: vi.fn(),
    getEmailDraft: vi.fn(),
    startProcessing: vi.fn(),
    cancelProcessing: vi.fn(),
    updateMeeting: vi.fn(),
    deleteMeeting: vi.fn(),
    submitReview: vi.fn(),
    submitEmailReview: vi.fn(),
  },
}));

vi.mock('./api/teams', () => ({
  projectsApi: { listMembers: vi.fn().mockResolvedValue([]) },
  teamsApi: { listMembers: vi.fn().mockResolvedValue([]) },
}));

vi.mock('./context/TeamContext', () => ({
  useTeam: () => ({
    activeTeam: { id: 'team-1', role: 'owner' },
    canManageTeam: () => roleState.canManage,
  }),
}));

vi.mock('./context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      email: 'owner@example.com',
      full_name: 'Team Owner',
      role: 'USER',
      platform_role: 'user',
      is_active: true,
    },
  }),
}));

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const meeting = {
  id: 'meeting-1',
  user_id: 1,
  team_id: 'team-1',
  project_id: 'project-1',
  created_by: 1,
  title: 'Planning review',
  meeting_date: '2026-08-20',
  project_name: 'Launch',
  agenda: [],
  attendees: [{ name: 'Alex', email: 'alex@example.com' }],
  status: 'awaiting_email_review',
  decisions: [],
  action_items: [],
  redacted_decisions: [],
  redacted_action_items: [],
  email_sent: false,
  tokens_used: 42,
  created_at: '2026-08-20T09:00:00Z',
  updated_at: '2026-08-20T09:05:00Z',
} satisfies Meeting;

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/meetings/meeting-1']}>
        <Routes>
          <Route path="/meetings/:meetingId" element={<MeetingReviewPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('MeetingReviewPage', () => {
  beforeEach(() => {
    roleState.canManage = true;
    vi.mocked(meetingsApi.getMeeting).mockResolvedValue(meeting);
    vi.mocked(meetingsApi.getStatus).mockResolvedValue({
      meeting_id: meeting.id,
      status: 'awaiting_email_review',
      current_stage: 'awaiting_email_review',
      progress_percentage: 80,
    });
    vi.mocked(meetingsApi.getEmailDraft).mockResolvedValue({
      meeting_id: meeting.id,
      meeting_title: meeting.title,
      email_draft: 'Hello team,\n\nHere are the approved next steps.',
      delivery_error: null,
      redacted_summary: 'Approved summary',
      redacted_decisions: [],
      redacted_action_items: [],
    });
    vi.mocked(meetingsApi.cancelProcessing).mockResolvedValue({
      meeting_id: meeting.id,
      status: 'cancelled',
      current_stage: 'cancelled',
      progress_percentage: 0,
    });
  });

  it('polls only while the backend workflow is actively running', () => {
    expect(shouldPollMeetingStatus('queued')).toBe(true);
    expect(shouldPollMeetingStatus('processing')).toBe(true);
    expect(shouldPollMeetingStatus('awaiting_review')).toBe(false);
    expect(shouldPollMeetingStatus('awaiting_email_review')).toBe(false);
    expect(shouldPollMeetingStatus('completed')).toBe(false);
    expect(shouldPollMeetingStatus('failed')).toBe(false);
    expect(shouldPollMeetingStatus('cancelled')).toBe(false);
  });

  it('opens the email approval checkpoint from the meeting page', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole('button', { name: /review email/i }));

    expect(await screen.findByRole('heading', { name: /email draft review/i })).toBeInTheDocument();
    expect(screen.getByText(/approved next steps/i)).toBeInTheDocument();
  });

  it('submits only the recipients selected for this meeting', async () => {
    const user = userEvent.setup();
    vi.mocked(meetingsApi.getEmailDraft).mockResolvedValue({
      meeting_id: meeting.id,
      meeting_title: meeting.title,
      email_draft: 'Hello team,\n\nHere are the approved next steps.',
      delivery_error: null,
      redacted_summary: 'Approved summary',
      redacted_decisions: [],
      redacted_action_items: [],
      participants: [
        { user_id: 1, name: 'Team Owner', email: 'owner@example.com', selected: true },
        { user_id: 2, name: 'Ali Khan', email: 'ali@example.com', title: 'Backend Developer', selected: false },
      ],
    });
    vi.mocked(meetingsApi.submitEmailReview).mockResolvedValue({
      meeting_id: meeting.id,
      sent: true,
      response: { status: 'sent' },
      message: 'Email sent.',
    });
    renderPage();

    await user.click(await screen.findByRole('button', { name: /review email/i }));
    await user.click(await screen.findByRole('checkbox', { name: /ali khan/i }));
    await user.click(screen.getByRole('button', { name: /send email/i }));

    await waitFor(() => expect(meetingsApi.submitEmailReview).toHaveBeenCalledWith(
      meeting.id,
      expect.objectContaining({ recipient_user_ids: [1, 2] }),
    ));
  });

  it('does not expose meeting-management controls to a normal member', async () => {
    roleState.canManage = false;
    renderPage();

    expect(await screen.findByText('Planning review')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^edit meeting$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /review email/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /stop processing/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /transcript/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /activity/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/AI & transcription configuration/i)).not.toBeInTheDocument();
  });

  it('confirms and submits a stop-processing request', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole('button', { name: /stop processing/i }));
    await user.click(screen.getByRole('button', { name: /yes, stop processing/i }));

    await waitFor(() => expect(meetingsApi.cancelProcessing).toHaveBeenCalledWith(meeting.id));
  });

  it('updates the meeting title through the backend API', async () => {
    const user = userEvent.setup();
    vi.mocked(meetingsApi.updateMeeting).mockImplementation(async (_id, update) => ({ ...meeting, ...update, attendees: update.attendees ?? meeting.attendees }));
    renderPage();

    await user.click(await screen.findByRole('button', { name: /^edit meeting$/i }));
    const title = screen.getByRole('textbox', { name: /meeting title/i });
    await user.clear(title);
    await user.type(title, 'Launch planning');
    await user.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => expect(meetingsApi.updateMeeting).toHaveBeenCalledWith(meeting.id, expect.objectContaining({ title: 'Launch planning' })));
  });

  it('keeps email review open and shows a delivery configuration error', async () => {
    const user = userEvent.setup();
    vi.mocked(meetingsApi.getEmailDraft).mockResolvedValue({
      meeting_id: meeting.id,
      meeting_title: meeting.title,
      email_draft: 'Hello team,\n\nHere are the approved next steps.',
      delivery_error: 'The mail.meetingagent.com domain is not verified.',
      redacted_summary: 'Approved summary',
      redacted_decisions: [],
      redacted_action_items: [],
    });
    vi.mocked(meetingsApi.submitEmailReview).mockResolvedValue({
      meeting_id: meeting.id,
      sent: false,
      response: { status: 'failed' },
      message: 'The mail.meetingagent.com domain is not verified.',
    });
    renderPage();

    await user.click(await screen.findByRole('button', { name: /review email/i }));
    expect(await screen.findByText(/email was not sent/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /send email/i }));

    await waitFor(() => expect(meetingsApi.submitEmailReview).toHaveBeenCalled());
    expect(screen.getByRole('heading', { name: /email draft review/i })).toBeInTheDocument();
  });
});
