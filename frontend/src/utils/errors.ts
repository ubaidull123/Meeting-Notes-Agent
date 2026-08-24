import axios, { AxiosError } from 'axios';

export interface APIErrorResponse {
  error?: string;
  message?: string;
  detail?: string | Array<{ loc?: string[]; msg?: string; type?: string; field?: string }>;
  details?: Array<{ field?: string; message?: string }>;
}

export function formatErrorMessage(error: unknown, fallbackMessage = 'An unexpected error occurred. Please try again.'): string {
  if (!error) return fallbackMessage;

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<APIErrorResponse | string>;
    const status = axiosError.response?.status;
    const data = axiosError.response?.data;

    // Status-specific friendly messages
    if (status === 401) {
      return 'Incorrect email or password, or your session has expired.';
    }
    if (status === 403) {
      return 'You do not have permission to perform this action.';
    }
    if (status === 404) {
      return typeof data === 'object' && data?.message ? data.message : 'The requested resource was not found.';
    }
    if (status === 409) {
      return 'This record already exists (e.g. email already registered).';
    }
    if (status === 413) {
      return 'The selected file is too large. Maximum size is 100MB.';
    }
    if (status === 429) {
      return 'Too many requests. Please slow down and wait a minute.';
    }
    if (status === 503) {
      return 'Database service temporarily unavailable. Please try again shortly.';
    }

    if (typeof data === 'object' && data !== null) {
      if (data.message) {
        return data.message;
      }
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.details) && data.details.length > 0) {
        return data.details.map(d => d.message || d.field).filter(Boolean).join(', ');
      }
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        return data.detail.map(d => d.msg || 'Invalid field').join(', ');
      }
    } else if (typeof data === 'string') {
      return data;
    }

    if (axiosError.message === 'Network Error') {
      return 'Unable to connect to the server. Please check your network connection.';
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}
