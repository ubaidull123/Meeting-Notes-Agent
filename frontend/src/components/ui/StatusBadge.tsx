import React from 'react';
import { MeetingStatus } from '../../types/meeting';
import { TaskStatus } from '../../types/task';
import { cn } from '../../utils/cn';
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
  UploadCloud,
  Mail,
  UserCheck,
  XCircle,
  HelpCircle,
} from 'lucide-react';

interface StatusBadgeProps {
  status: MeetingStatus | TaskStatus | string;
  className?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className, size = 'md' }) => {
  const normalizedStatus = (status || '').toLowerCase();

  const getStatusConfig = () => {
    switch (normalizedStatus) {
      // Meeting statuses
      case 'draft':
        return {
          label: 'Draft',
          icon: FileText,
          bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
        };
      case 'uploaded':
        return {
          label: 'Uploaded',
          icon: UploadCloud,
          bg: 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border-blue-200 dark:border-blue-800',
        };
      case 'queued':
        return {
          label: 'Queued',
          icon: Clock,
          bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border-amber-200 dark:border-amber-800',
        };
      case 'processing':
        return {
          label: 'Processing',
          icon: Loader2,
          animate: true,
          bg: 'bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-300 border-teal-200 dark:border-teal-800',
        };
      case 'awaiting_review':
        return {
          label: 'Awaiting Review',
          icon: UserCheck,
          bg: 'bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300 border-purple-200 dark:border-purple-800',
        };
      case 'revision_requested':
        return {
          label: 'Revision Requested',
          icon: AlertCircle,
          bg: 'bg-orange-50 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300 border-orange-200 dark:border-orange-800',
        };
      case 'awaiting_email_review':
        return {
          label: 'Email Review',
          icon: Mail,
          bg: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
        };
      case 'completed':
      case 'done':
        return {
          label: normalizedStatus === 'done' ? 'Done' : 'Completed',
          icon: CheckCircle2,
          bg: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
        };
      case 'rejected':
        return {
          label: 'Review Rejected',
          icon: XCircle,
          bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
        };
      case 'failed':
      case 'blocked':
        return {
          label: normalizedStatus === 'blocked' ? 'Blocked' : 'Failed',
          icon: XCircle,
          bg: 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border-rose-200 dark:border-rose-800',
        };
      case 'cancelled':
        return {
          label: 'Cancelled',
          icon: XCircle,
          bg: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 border-gray-200 dark:border-gray-700',
        };

      // Task statuses
      case 'todo':
        return {
          label: 'To Do',
          icon: Clock,
          bg: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
        };
      case 'in_progress':
        return {
          label: 'In Progress',
          icon: Loader2,
          animate: true,
          bg: 'bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 border-sky-200 dark:border-sky-800',
        };
      case 'in_review':
        return {
          label: 'In Review',
          icon: UserCheck,
          bg: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border-amber-200 dark:border-amber-800',
        };

      default:
        return {
          label: status || 'Unknown',
          icon: HelpCircle,
          bg: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium border rounded-full',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs',
        config.bg,
        className
      )}
    >
      <Icon className={cn('w-3.5 h-3.5', config.animate && 'animate-spin')} />
      <span>{config.label}</span>
    </span>
  );
};
