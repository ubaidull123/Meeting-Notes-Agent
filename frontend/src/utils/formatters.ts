export function formatNumber(num?: number | null): string {
  if (num === undefined || num === null) return '0';
  return new Intl.NumberFormat('en-US').format(num);
}

export function formatFileSize(bytes?: number | null): string {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function truncateText(text?: string | null, maxLength: number = 100): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}
