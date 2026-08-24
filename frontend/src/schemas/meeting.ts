import { z } from 'zod';

export const attendeeSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  email: z.string().min(1, 'Email is required').email('Invalid email address'),
});

export type AttendeeFormData = z.infer<typeof attendeeSchema>;

export const createMeetingSchema = z.object({
  title: z.string().min(1, 'Meeting title is required').max(500, 'Title is too long'),
  meeting_date: z.string().min(1, 'Meeting date is required'),
  meeting_time: z.string().optional(),
  project_name: z.string().max(255).optional(),
  notes: z.string().optional(),
  agenda: z.array(z.string()).default([]),
  attendees: z.array(attendeeSchema).min(1, 'At least one attendee is required'),
  inputType: z.enum(['transcript_text', 'audio_file', 'transcript_file']),
  transcript_text: z.string().optional(),
}).superRefine((data, ctx) => {
  if (data.inputType === 'transcript_text' && (!data.transcript_text || data.transcript_text.trim().length === 0)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Please paste or enter meeting transcript text',
      path: ['transcript_text'],
    });
  }
});

export type CreateMeetingFormData = z.infer<typeof createMeetingSchema>;

export const updateMeetingSchema = z.object({
  title: z.string().min(1, 'Meeting title is required').max(500),
  meeting_date: z.string().optional(),
  meeting_time: z.string().optional(),
  project_name: z.string().max(255).optional(),
  notes: z.string().optional(),
  agenda: z.array(z.string()).optional(),
  attendees: z.array(attendeeSchema).min(1, 'At least one attendee is required').optional(),
});

export type UpdateMeetingFormData = z.infer<typeof updateMeetingSchema>;

export const reviewSchema = z.object({
  decision: z.enum(['approve', 'reject', 'revise']),
  instructions: z.string().optional(),
}).superRefine((data, ctx) => {
  if (data.decision === 'revise' && (!data.instructions || data.instructions.trim().length === 0)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Please provide revision instructions for the AI workflow',
      path: ['instructions'],
    });
  }
});

export type ReviewFormData = z.infer<typeof reviewSchema>;
