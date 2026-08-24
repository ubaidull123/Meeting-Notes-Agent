import React, { useRef, useState } from 'react';
import { UploadCloud, File as FileIcon, X, AlertCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import { formatFileSize } from '../../utils/formatters';

interface FileUploadProps {
  accept: string;
  maxSizeMB?: number;
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
  label: string;
  description: string;
  allowedExtensions: string[];
  className?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  accept,
  maxSizeMB = 100,
  selectedFile,
  onFileSelect,
  label,
  description,
  allowedExtensions,
  className,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    setError(null);
    const extension = `.${file.name.split('.').pop()?.toLowerCase()}`;

    if (!allowedExtensions.includes(extension)) {
      setError(`Invalid file format. Allowed: ${allowedExtensions.join(', ')}`);
      return false;
    }

    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError(`File size exceeds maximum limit of ${maxSizeMB}MB`);
      return false;
    }

    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (validateFile(file)) {
        onFileSelect(file);
      } else {
        onFileSelect(null);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (validateFile(file)) {
        onFileSelect(file);
      } else {
        onFileSelect(null);
      }
    }
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={cn('space-y-2', className)}>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileChange}
        className="hidden"
      />

      {!selectedFile ? (
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={cn(
            'flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl cursor-pointer transition-colors text-center',
            isDragOver
              ? 'border-teal-500 bg-teal-50/50 dark:bg-teal-950/30'
              : 'border-border hover:border-teal-500/50 hover:bg-muted/40'
          )}
        >
          <div className="p-3 rounded-full bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 mb-2">
            <UploadCloud className="w-5 h-5" />
          </div>
          <span className="text-sm font-medium text-foreground">{label}</span>
          <span className="text-xs text-muted-foreground mt-1">{description}</span>
          <span className="text-[11px] text-muted-foreground/80 mt-2">
            Supports: {allowedExtensions.join(', ')} (Max: {maxSizeMB}MB)
          </span>
        </div>
      ) : (
        <div className="flex items-center justify-between p-3.5 border rounded-xl bg-card">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400 shrink-0">
              <FileIcon className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-foreground truncate">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            className="p-1.5 text-muted-foreground hover:text-rose-600 rounded-md hover:bg-muted transition-colors"
            title="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-1.5 text-xs text-rose-600 dark:text-rose-400">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
