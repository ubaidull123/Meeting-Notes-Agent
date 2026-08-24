import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBg?: string;
  trend?: {
    value: string;
    positive?: boolean;
  };
  onClick?: () => void;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-teal-600 dark:text-teal-400',
  iconBg = 'bg-teal-50 dark:bg-teal-950/50 border-teal-100 dark:border-teal-900',
  trend,
  onClick,
  className,
}) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        'p-5 rounded-xl border bg-card text-card-foreground shadow-sm transition-all',
        onClick && 'cursor-pointer hover:border-teal-500/50 hover:shadow-md',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {title}
        </span>
        <div className={cn('p-2.5 rounded-lg border', iconBg)}>
          <Icon className={cn('w-4 h-4', iconColor)} />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-semibold tracking-tight text-foreground">{value}</span>
        {trend && (
          <span
            className={cn(
              'text-xs font-medium px-1.5 py-0.5 rounded',
              trend.positive
                ? 'text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 dark:text-emerald-400'
                : 'text-rose-700 bg-rose-50 dark:bg-rose-950/60 dark:text-rose-400'
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  );
};
