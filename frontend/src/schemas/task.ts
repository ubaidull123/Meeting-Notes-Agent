import { z } from 'zod';

export const updateTaskSchema = z.object({
  title: z.string().min(1, 'Task title is required').max(500),
  description: z.string().optional().nullable(),
  status: z.enum(['todo', 'in_progress', 'in_review', 'done', 'blocked']).optional(),
  priority: z.enum(['low', 'medium', 'high', 'urgent']).optional(),
  assignee: z.string().max(255).optional().nullable(),
  due_date: z.string().optional().nullable(),
  labels: z.array(z.string()).optional(),
});

export type UpdateTaskFormData = z.infer<typeof updateTaskSchema>;
