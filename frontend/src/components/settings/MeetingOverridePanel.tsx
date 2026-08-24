import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { SlidersHorizontal, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { settingsApi } from '../../api/settings';
import { formatErrorMessage } from '../../utils/errors';
import { MeetingOverride, UsageMode } from '../../types/settings';

const field = 'w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-teal-500/30';
const button = 'inline-flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-60';

export function MeetingOverridePanel({ meetingId }: { meetingId: string }) {
  const qc = useQueryClient();
  const providers = useQuery({ queryKey: ['settings-providers'], queryFn: settingsApi.getProviders });
  const current = useQuery({ queryKey: ['meeting-override', meetingId], queryFn: () => settingsApi.getOverride(meetingId) });
  const ai = useQuery({ queryKey: ['settings-ai'], queryFn: settingsApi.getAI });
  const [draft, setDraft] = useState<MeetingOverride>({});

  useEffect(() => {
    if (current.data) setDraft(current.data);
  }, [current.data]);

  const save = useMutation({
    mutationFn: () => settingsApi.setOverride(meetingId, draft),
    onSuccess: data => {
      setDraft(data);
      toast.success('Meeting override saved');
      qc.invalidateQueries({ queryKey: ['meeting-override', meetingId] });
    },
    onError: error => toast.error(formatErrorMessage(error)),
  });
  const clear = useMutation({
    mutationFn: () => settingsApi.clearOverride(meetingId),
    onSuccess: () => {
      setDraft({});
      toast.success('Meeting override cleared');
      qc.invalidateQueries({ queryKey: ['meeting-override', meetingId] });
    },
    onError: error => toast.error(formatErrorMessage(error)),
  });

  if (providers.isLoading || ai.isLoading || current.isLoading) {
    return <div className="rounded-xl border border-border bg-card p-5 text-sm text-muted-foreground">Loading override settings...</div>;
  }

  const llmProvider = draft.llm_provider || ai.data?.llm_provider || 'openai';
  const transcriptionProvider = draft.transcription_provider || ai.data?.transcription_provider || 'openai';
  const chatModels = providers.data?.[llmProvider]?.models.chat ?? [];
  const transcriptionModels = providers.data?.[transcriptionProvider]?.models.transcription ?? [];
  const providerOptions = Object.entries(providers.data ?? {}).filter(([, p]) => p.enabled && p.capabilities.includes('chat'));
  const transcriptionProviderOptions = Object.entries(providers.data ?? {}).filter(([, p]) => p.enabled && p.capabilities.includes('transcription'));

  const setProvider = (key: 'llm_provider' | 'transcription_provider', value: string) => {
    const cap = key === 'llm_provider' ? 'chat' : 'transcription';
    const firstModel = providers.data?.[value]?.models[cap]?.[0]?.id || null;
    setDraft({ ...draft, [key]: value, [key === 'llm_provider' ? 'llm_model' : 'transcription_model']: firstModel });
  };

  return <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
    <div className="mb-4 flex items-center gap-2">
      <SlidersHorizontal size={17} className="text-teal-700" />
      <h3 className="font-semibold">Meeting AI override</h3>
    </div>
    <div className="grid gap-4 lg:grid-cols-2">
      <label className="text-sm font-medium">LLM mode<select className={'mt-1 ' + field} value={draft.llm_usage_mode || ''} onChange={e => setDraft({ ...draft, llm_usage_mode: (e.target.value || null) as UsageMode | null })}><option value="">Use default</option><option value="app_credits">App credits</option><option value="byok">Personal API</option></select></label>
      <label className="text-sm font-medium">LLM provider<select className={'mt-1 ' + field} value={llmProvider} onChange={e => setProvider('llm_provider', e.target.value)}>{providerOptions.map(([id, p]) => <option key={id} value={id}>{p.name}</option>)}</select></label>
      <label className="text-sm font-medium">LLM model<select className={'mt-1 ' + field} value={draft.llm_model || ai.data?.llm_model || ''} onChange={e => setDraft({ ...draft, llm_model: e.target.value })}>{chatModels.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}</select></label>
      <label className="text-sm font-medium">Transcription mode<select className={'mt-1 ' + field} value={draft.transcription_usage_mode || ''} onChange={e => setDraft({ ...draft, transcription_usage_mode: (e.target.value || null) as UsageMode | null })}><option value="">Use default</option><option value="app_credits">App credits</option><option value="byok">Personal API</option></select></label>
      <label className="text-sm font-medium">Transcription provider<select className={'mt-1 ' + field} value={transcriptionProvider} onChange={e => setProvider('transcription_provider', e.target.value)}>{transcriptionProviderOptions.map(([id, p]) => <option key={id} value={id}>{p.name}</option>)}</select></label>
      <label className="text-sm font-medium">Transcription model<select className={'mt-1 ' + field} value={draft.transcription_model || ai.data?.transcription_model || ''} onChange={e => setDraft({ ...draft, transcription_model: e.target.value })}>{transcriptionModels.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}</select></label>
    </div>
    <div className="mt-4 flex flex-wrap gap-2">
      <button className={button} type="button" disabled={save.isPending} onClick={() => save.mutate()}>{save.isPending && <Loader2 className="animate-spin" size={16} />}Save override</button>
      <button className="rounded-lg border border-border px-4 py-2 text-sm font-semibold hover:bg-muted" type="button" disabled={clear.isPending} onClick={() => clear.mutate()}>Use defaults</button>
    </div>
  </section>;
}

