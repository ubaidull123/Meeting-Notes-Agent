import React from 'react';
import {
  FileText,
  CheckSquare2,
  FolderTree,
  UserCheck,
  MailCheck,
  KeyRound,
} from 'lucide-react';

export const FeaturesSection: React.FC = () => {
  const features = [
    {
      title: 'AI Meeting Summaries',
      description: 'Generates comprehensive executive summaries, key decisions, and discussion highlights.',
      icon: FileText,
    },
    {
      title: 'Action Item Extraction',
      description: 'Automatically detects tasks, owners, priority levels, and suggested completion dates.',
      icon: CheckSquare2,
    },
    {
      title: 'Team & Project Context',
      description: 'Maintains project-centric records so discussions and follow-ups stay aligned with ongoing goals.',
      icon: FolderTree,
    },
    {
      title: 'Human Review Workflow',
      description: 'Enables teams to verify, adjust, and approve AI outputs before distributing recap notes.',
      icon: UserCheck,
    },
    {
      title: 'Follow-up Email Generation',
      description: 'Creates structured, editable email drafts ready to send to meeting attendees in one click.',
      icon: MailCheck,
    },
    {
      title: 'Multiple AI Providers / BYOK',
      description: 'Use platform credits or bring your own API keys for OpenAI, Anthropic, Gemini, or Groq.',
      icon: KeyRound,
    },
  ];

  return (
    <section id="features" className="py-16 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-14 sm:mb-16">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-teal-600 dark:text-teal-400">
            Core Capabilities
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Everything you need for meeting clarity
          </p>
          <p className="mt-3 text-base text-muted-foreground">
            A purposeful toolkit engineered to eliminate lost meeting context and missed deadlines.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feat) => {
            const Icon = feat.icon;
            return (
              <div
                key={feat.title}
                className="group rounded-2xl border border-border bg-card p-6 shadow-xs hover:border-teal-500/40 hover:shadow-md transition-all duration-200"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 group-hover:scale-105 transition-transform duration-200">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">
                  {feat.title}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                  {feat.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
