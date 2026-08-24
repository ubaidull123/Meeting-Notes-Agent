import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';

interface PaginationProps {
  currentPage: number;
  pageSize: number;
  totalItems?: number;
  hasMore?: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  pageSize,
  totalItems,
  hasMore = false,
  onPageChange,
  className,
}) => {
  const totalPages = totalItems ? Math.ceil(totalItems / pageSize) : null;
  const canGoPrev = currentPage > 1;
  const canGoNext = totalPages ? currentPage < totalPages : hasMore;

  return (
    <div className={cn('flex items-center justify-between gap-4 py-3 text-sm text-muted-foreground', className)}>
      <div>
        {totalItems !== undefined ? (
          <span>
            Showing <strong className="text-foreground">{Math.min(totalItems, (currentPage - 1) * pageSize + 1)}</strong> to{' '}
            <strong className="text-foreground">{Math.min(totalItems, currentPage * pageSize)}</strong> of{' '}
            <strong className="text-foreground">{totalItems}</strong> entries
          </span>
        ) : (
          <span>Page {currentPage}</span>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!canGoPrev}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium border rounded-md bg-card hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline">Previous</span>
        </button>

        {totalPages && (
          <span className="px-2 text-xs font-medium text-foreground">
            {currentPage} / {totalPages}
          </span>
        )}

        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!canGoNext}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium border rounded-md bg-card hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
