import { CheckCircle2, KeyRound, Loader2, Trash2, XCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import {
  useDeleteCredential,
  useSaveCredential,
  useTestCredential,
} from '../../hooks/useSettings';
import {
  CredentialPublic,
  ProviderCatalog,
  ProviderModel,
  UsageMode,
} from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';
import { settingsFieldClass } from './SettingsControls';

export function UsageModeControl({ value, onChange }: { value: UsageMode; onChange: (value: UsageMode) => void }) {
  return (
    <div className="inline-flex rounded-md border border-border p-1" role="group" aria-label="Usage mode">
      {([
        ['app_credits', 'Application credits'],
        ['byok', 'My API key'],
      ] as const).map(([mode, label]) => (
        <button
          key={mode}
          type="button"
          onClick={() => onChange(mode)}
          className={`rounded px-3 py-1.5 text-sm font-medium ${value === mode ? 'bg-teal-600 text-white' : 'text-muted-foreground hover:bg-muted'}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export function availableProviders(catalog: ProviderCatalog | undefined, capability: 'chat' | 'transcription' | 'email') {
  return Object.entries(catalog ?? {}).filter(([, provider]) => provider.enabled && provider.capabilities.includes(capability));
}

export function ProviderModelControls({
  catalog,
  capability,
  provider,
  model,
  onProviderChange,
  onModelChange,
}: {
  catalog: ProviderCatalog;
  capability: 'chat' | 'transcription';
  provider: string;
  model: string;
  onProviderChange: (provider: string, firstModel: string) => void;
  onModelChange: (model: string) => void;
}) {
  const providers = availableProviders(catalog, capability);
  const models = catalog[provider]?.models?.[capability] ?? [];
  const metadata = models.find((item) => item.id === model);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="text-sm font-medium">
          Provider
          <select
            className={settingsFieldClass}
            value={provider}
            onChange={(event) => {
              const selected = event.target.value;
              const firstModel = catalog[selected]?.models?.[capability]?.[0]?.id ?? '';
              onProviderChange(selected, firstModel);
            }}
          >
            {providers.map(([id, item]) => <option key={id} value={id}>{item.name}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium">
          Default model
          <select className={settingsFieldClass} value={model} onChange={(event) => onModelChange(event.target.value)}>
            {models.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
      </div>
      {metadata && <ModelMetadata model={metadata} />}
    </div>
  );
}

function ModelMetadata({ model }: { model: ProviderModel }) {
  return (
    <div className="grid gap-3 border-l-2 border-teal-500 pl-4 text-sm sm:grid-cols-3">
      <div><span className="text-muted-foreground">Tier</span><p className="font-medium capitalize">{model.tier}</p></div>
      <div><span className="text-muted-foreground">Speed</span><p className="font-medium capitalize">{model.speed}</p></div>
      <div><span className="text-muted-foreground">Quality</span><p className="font-medium capitalize">{model.quality}</p></div>
      <p className="text-muted-foreground sm:col-span-3">{model.recommended_for}</p>
    </div>
  );
}

export function CredentialManager({
  providerIds,
  catalog,
  credentials,
}: {
  providerIds: string[];
  catalog: ProviderCatalog;
  credentials: CredentialPublic[];
}) {
  const providers = useMemo(() => providerIds.filter((id) => catalog[id]?.enabled), [catalog, providerIds]);
  const [provider, setProvider] = useState(providers[0] ?? '');
  const [apiKey, setApiKey] = useState('');
  const save = useSaveCredential();
  const test = useTestCredential();
  const remove = useDeleteCredential();

  useEffect(() => {
    if (!providers.includes(provider)) setProvider(providers[0] ?? '');
  }, [provider, providers]);

  const runTest = (id: string, pendingKey?: string) => {
    test.mutate(
      { provider: id, apiKey: pendingKey || undefined },
      {
        onSuccess: (result) => result.valid ? toast.success(result.message) : toast.error(result.message),
        onError: (error) => toast.error(formatErrorMessage(error)),
      },
    );
  };

  return (
    <div className="space-y-4">
      {credentials.filter((item) => providers.includes(item.provider)).map((credential) => (
        <div key={credential.provider} className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4 last:border-0">
          <div>
            <p className="font-medium">{catalog[credential.provider]?.name ?? credential.provider}</p>
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              {credential.is_valid ? <CheckCircle2 className="h-4 w-4 text-teal-600" /> : <XCircle className="h-4 w-4 text-amber-600" />}
              <span>{credential.is_valid ? 'Connected' : 'Not verified'}</span>
              {credential.api_key_hint && <span>{credential.api_key_hint}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            <button type="button" className="rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted" disabled={test.isPending} onClick={() => runTest(credential.provider)}>Test</button>
            <button type="button" className="rounded-md p-2 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40" title="Remove credential" disabled={remove.isPending} onClick={() => remove.mutate(credential.provider, { onSuccess: () => toast.success('Credential removed'), onError: (error) => toast.error(formatErrorMessage(error)) })}><Trash2 className="h-4 w-4" /></button>
          </div>
        </div>
      ))}

      <div className="grid gap-3 sm:grid-cols-[180px_minmax(0,1fr)_auto] sm:items-end">
        <label className="text-sm font-medium">
          Provider
          <select className={settingsFieldClass} value={provider} onChange={(event) => setProvider(event.target.value)}>
            {providers.map((id) => <option key={id} value={id}>{catalog[id].name}</option>)}
          </select>
        </label>
        <label className="text-sm font-medium">
          New API key
          <input className={settingsFieldClass} type="password" autoComplete="new-password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Paste key" />
        </label>
        <button
          type="button"
          disabled={!provider || !apiKey || save.isPending}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-teal-600 px-4 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50"
          onClick={() => save.mutate({ provider, apiKey }, {
            onSuccess: () => { setApiKey(''); toast.success('Credential saved'); },
            onError: (error) => toast.error(formatErrorMessage(error)),
          })}
        >
          {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <KeyRound className="h-4 w-4" />}
          Save key
        </button>
      </div>
    </div>
  );
}
