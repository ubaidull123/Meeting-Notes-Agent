import { Bot, Captions, Coins, FileCheck2 } from 'lucide-react';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { useUsageSettings, useUsageSummary } from '../../hooks/useSettings';
import { formatErrorMessage } from '../../utils/errors';

export function UsageSettingsPage() {
  const summary = useUsageSummary();
  const usage = useUsageSettings();
  if (summary.isError || usage.isError) return <ErrorState message={formatErrorMessage(summary.error ?? usage.error)} onRetry={() => { void summary.refetch(); void usage.refetch(); }} />;
  if (summary.isLoading || usage.isLoading || !summary.data) return <LoadingState />;
  const stats = [
    { label: 'Current balance', value: summary.data.balance, detail: 'Application credits', icon: Coins },
    { label: 'This month', value: summary.data.credits_consumed, detail: `${summary.data.meetings_processed} meetings`, icon: FileCheck2 },
    { label: 'LLM usage', value: summary.data.llm_credits, detail: `${summary.data.llm_requests} requests`, icon: Bot },
    { label: 'Transcription', value: summary.data.transcription_credits, detail: `${summary.data.transcription_requests} requests`, icon: Captions },
  ];
  return <div className="space-y-6">
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{stats.map(({ label, value, detail, icon: Icon }) => <section key={label} className="rounded-md border border-border p-4"><Icon className="h-5 w-5 text-teal-600"/><p className="mt-3 text-2xl font-semibold">{value}</p><p className="text-sm font-medium">{label}</p><p className="text-xs text-muted-foreground">{detail}</p></section>)}</div>
    <section><h2 className="text-sm font-semibold">Recent activity</h2><p className="mt-1 text-sm text-muted-foreground">Application credits and personal API activity are reported separately.</p>
      <div className="mt-4 overflow-x-auto rounded-md border border-border"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-muted/60 text-xs text-muted-foreground"><tr>{['Meeting','Service','Provider / model','Usage mode','Credits','Date'].map((heading) => <th key={heading} className="px-3 py-2 font-medium">{heading}</th>)}</tr></thead><tbody className="divide-y divide-border">{(usage.data ?? []).map((row) => <tr key={row.id}><td className="px-3 py-3 font-medium">{row.meeting_title ?? 'Deleted meeting'}</td><td className="px-3 py-3 capitalize">{row.service_type}</td><td className="px-3 py-3"><span className="block">{row.provider}</span><span className="text-xs text-muted-foreground">{row.model}</span></td><td className="px-3 py-3">{row.usage_mode === 'byok' ? 'Personal API' : 'Application credits'}</td><td className="px-3 py-3">{row.usage_mode === 'byok' ? '0' : row.credits_cost}</td><td className="px-3 py-3 text-muted-foreground">{new Date(row.created_at).toLocaleString()}</td></tr>)}{!usage.data?.length && <tr><td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">No usage activity yet.</td></tr>}</tbody></table></div>
    </section>
  </div>;
}
