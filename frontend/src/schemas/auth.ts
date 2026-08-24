import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  full_name: z.string().min(1, 'Full name is required').max(255, 'Full name is too long'),
  email: z.string().min(1, 'Email is required').email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters long')
    .max(128, 'Password is too long'),
  confirm_password: z.string().min(1, 'Please confirm your password'),
}).refine((data) => data.password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

export type RegisterFormData = z.infer<typeof registerSchema>;

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z
    .string()
    .min(8, 'New password must be at least 8 characters long')
    .max(128, 'New password is too long'),
  confirm_new_password: z.string().min(1, 'Please confirm your new password'),
}).refine((data) => data.new_password === data.confirm_new_password, {
  message: "Passwords don't match",
  path: ['confirm_new_password'],
});

export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

export const updateProfileSchema = z.object({
  full_name: z.string().min(1, 'Full name is required').max(255, 'Full name is too long'),
});

export type UpdateProfileFormData = z.infer<typeof updateProfileSchema>;
