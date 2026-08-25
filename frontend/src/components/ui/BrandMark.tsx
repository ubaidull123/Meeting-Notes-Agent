import { cn } from '../../utils/cn';

interface BrandMarkProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizes = {
  sm: 'h-7 w-7 rounded-lg',
  md: 'h-8 w-8 rounded-lg',
  lg: 'h-9 w-9 rounded-xl',
};

export function BrandMark({ className, size = 'md' }: BrandMarkProps) {
  return (
    <img
      src="/logo.jpg"
      alt=""
      aria-hidden="true"
      className={cn(
        'shrink-0 object-cover shadow-sm ring-1 ring-border/80',
        sizes[size],
        className
      )}
    />
  );
}
