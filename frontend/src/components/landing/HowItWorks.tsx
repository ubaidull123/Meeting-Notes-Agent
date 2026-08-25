import React from 'react';
import { FolderKanban, UploadCloud, Cpu, MailCheck } from 'lucide-react';

export const HowItWorks: React.FC = () => {
  const steps = [
    {
      step: '01',
      title: 'Create a team and project',
      description: 'Organize your conversations by team and project to retain continuous context and history.',
      icon: FolderKanban,
    },
    {
      step: '02',
      title: 'Upload a recording or paste a transcript',
      description: 'Upload audio files (MP3, WAV, M4A) or paste text transcripts directly into the app.',
      icon: UploadCloud,
    },
    {
      step: '03',
      title: 'AI generates summaries, decisions, tasks, and insights',
      description: 'The multi-agent pipeline extracts key takeaways, structured action items, and crucial decisions.',
      icon: Cpu,
    },
    {
      step: '04',
      title: 'Review and send follow-up communication',
      description: 'Quality-check action items, assign owners, and send customized follow-up recap emails.',
      icon: MailCheck,
    },
  ];

  return (
    <section id="how-it-works" className="py-16 sm:py-24 border-t border-border/60 bg-muted/20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-14 sm:mb-16">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-teal-600 dark:text-teal-400">
            Workflow
          </h2>
          <p className="mt-2 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            How It Works
          </p>
          <p className="mt-3 text-base text-muted-foreground">
            From raw recorded discussions to actionable project execution in four simple steps.
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((item, index) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="relative rounded-2xl border border-border bg-card p-6 shadow-xs flex flex-col justify-between hover:border-teal-500/40 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-5">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 border border-teal-600/10">
                      <Icon className="h-6 w-6" />
                    </div>
                    <span className="font-mono text-2xl font-bold text-muted-foreground/30">
                      {item.step}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {index + 1}. {item.title}
                  </h3>
                  <p className="mt-2.5 text-sm text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
