import { FormEvent, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';
import { SettingsSaveButton, SettingsSection, SettingsToggle, settingsFieldClass } from '../../components/settings/SettingsControls';
import { ErrorState } from '../../components/ui/ErrorState';
import { LoadingState } from '../../components/ui/LoadingState';
import { useMeetingDefaults, useUpdateMeetingDefaults } from '../../hooks/useSettings';
import { MeetingDefaults, SummarySection } from '../../types/settings';
import { formatErrorMessage } from '../../utils/errors';

const summarySections: Array<[SummarySection, string]> = [
  ['main_topics', 'Main topics'],
  ['decisions', 'Decisions'],
  ['risks', 'Risks'],
  ['questions', 'Unresolved questions'],
  ['action_items', 'Action items'],
  ['deadlines', 'Deadlines'],
  ['follow_up_recommendations', 'Follow-up recommendations'],
];

export function MeetingDefaultsPage() {
  const query = useMeetingDefaults();
  const update = useUpdateMeetingDefaults();
  const [draft, setDraft] = useState<MeetingDefaults | null>(null);
  useEffect(() => { if (query.data) setDraft(query.data); }, [query.data]);
  const isDirty = useMemo(() => Boolean(draft && query.data && JSON.stringify(draft) !== JSON.stringify(query.data)), [draft, query.data]);

  if (query.isError) return <ErrorState message={formatErrorMessage(query.error)} onRetry={() => query.refetch()} />;
  if (query.isLoading || !draft) return <LoadingState />;

  const toggleSection = (section: SummarySection, checked: boolean) => {
    const next = checked
      ? [...draft.summary_sections, section]
      : draft.summary_sections.filter((item) => item !== section);
    setDraft({ ...draft, summary_sections: next });
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    update.mutate(draft, { onSuccess: (saved) => { setDraft(saved); toast.success('Meeting defaults saved'); }, onError: (error) => toast.error(formatErrorMessage(error)) });
  };

  return (
    <form onSubmit={submit}>
      <SettingsSection title="Meeting type">
        <label className="block max-w-md text-sm font-medium">Default meeting type<select className={settingsFieldClass} value={draft.default_meeting_type} onChange={(event) => setDraft({ ...draft, default_meeting_type: event.target.value as MeetingDefaults['default_meeting_type'] })}><option value="general">General</option><option value="planning">Planning</option><option value="standup">Stand-up</option><option value="interview">Interview</option><option value="client">Client meeting</option></select></label>
      </SettingsSection>
      <SettingsSection title="Generated outputs" description="Choose the artifacts produced for each processed meeting.">
        <div className="divide-y divide-border">
          <SettingsToggle label="Summary" checked={draft.generate_summary} onChange={(generate_summary) => setDraft({ ...draft, generate_summary })} />
          <SettingsToggle label="Action items" checked={draft.generate_action_items} onChange={(generate_action_items) => setDraft({ ...draft, generate_action_items })} />
          <SettingsToggle label="Key decisions" checked={draft.generate_decisions} onChange={(generate_decisions) => setDraft({ ...draft, generate_decisions })} />
          <SettingsToggle label="Insights" checked={draft.generate_insights} onChange={(generate_insights) => setDraft({ ...draft, generate_insights })} />
          <SettingsToggle label="Follow-up email" checked={draft.generate_follow_up_email} onChange={(generate_follow_up_email) => setDraft({ ...draft, generate_follow_up_email })} />
        </div>
      </SettingsSection>
      <SettingsSection title="Review workflow">
        <div className="divide-y divide-border">
          <SettingsToggle label="Require human review" checked={draft.require_human_review} onChange={(require_human_review) => setDraft({ ...draft, require_human_review })} />
          <SettingsToggle label="Require email approval" checked={draft.require_email_approval} onChange={(require_email_approval) => setDraft({ ...draft, require_email_approval })} />
          <SettingsToggle label="Sensitive information redaction" checked={draft.redact_sensitive_information} onChange={(redact_sensitive_information) => setDraft({ ...draft, redact_sensitive_information })} />
        </div>
      </SettingsSection>
      <SettingsSection title="Summary preferences">
        <div className="space-y-5">
          <label className="block max-w-md text-sm font-medium">Summary style<select className={settingsFieldClass} value={draft.summary_style} onChange={(event) => setDraft({ ...draft, summary_style: event.target.value as MeetingDefaults['summary_style'] })}><option value="short">Short</option><option value="standard">Standard</option><option value="detailed">Detailed</option><option value="executive">Executive</option><option value="technical">Technical</option><option value="custom">Custom</option></select></label>
          <fieldset>
            <legend className="text-sm font-medium">Include when present</legend>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {summarySections.map(([id, label]) => <label key={id} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={draft.summary_sections.includes(id)} onChange={(event) => toggleSection(id, event.target.checked)} />{label}</label>)}
            </div>
          </fieldset>
        </div>
      </SettingsSection>
      <SettingsSection title="Custom meeting instructions" description="Applied after the application's system and safety instructions.">
        <textarea className={settingsFieldClass} rows={7} maxLength={4000} value={draft.custom_instructions ?? ''} onChange={(event) => setDraft({ ...draft, custom_instructions: event.target.value || null })} placeholder="Highlight architecture decisions and unresolved technical questions." />
        <p className="mt-1 text-right text-xs text-muted-foreground">{draft.custom_instructions?.length ?? 0} / 4000</p>
      </SettingsSection>
      <div className="flex justify-end pt-6"><SettingsSaveButton isSaving={update.isPending} isDirty={isDirty} /></div>
    </form>
  );
}
