import { z } from 'zod';

export const adjustCreditsSchema = z.object({
  amount: z.number({ invalid_type_error: 'Amount must be a number' }),
  reason: z.string().min(1, 'Reason is required').max(500, 'Reason is too long'),
});

export type AdjustCreditsFormData = z.infer<typeof adjustCreditsSchema>;

export const adjustQuotaSchema = z.object({
  monthly_limit: z
    .number({ invalid_type_error: 'Monthly limit must be a number' })
    .min(1, 'Limit must be at least 1')
    .max(1000, 'Limit cannot exceed 1000'),
});

export type AdjustQuotaFormData = z.infer<typeof adjustQuotaSchema>;

export const adminUserUpdateSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(255).optional(),
  role: z.enum(['USER', 'ADMIN']).optional(),
  is_active: z.boolean().optional(),
});

export type AdminUserUpdateFormData = z.infer<typeof adminUserUpdateSchema>;
