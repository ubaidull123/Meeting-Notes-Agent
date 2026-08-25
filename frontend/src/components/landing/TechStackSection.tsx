import React from 'react';
import { Terminal, Code2, Database, Network, Cpu, Layers } from 'lucide-react';

export const TechStackSection: React.FC = () => {
  const stack = [
    {
      name: 'FastAPI',
      category: 'Python Backend',
      description: 'High-performance async API framework with OpenAPI documentation and Pydantic validation.',
      icon: Terminal,
    },
    {
      name: 'React + Vite',
      category: 'Frontend SPA',
      description: 'Modern component-driven UI with instant HMR and Tailwind CSS design tokens.',
      icon: Code2,
    },
    {
      name: 'TypeScript',
      category: 'Type Safety',
      description: 'Strict end-to-end type contracts across state management, API clients, and UI.',
      icon: Layers,
    },
    {
      name: 'PostgreSQL',
      category: 'Database & State',
      description: 'Relational data modeling, ACID transactions, and persistent audit logs.',
      icon: Database,
    },
    {
      name: 'LangGraph',
      category: 'Agent Orchestration',
      description: 'Stateful multi-agent execution graphs with checkpointing and error recovery.',
      icon: Network,
    },
    {
      name: 'LLM APIs',
      category: 'AI Engine',
      description: 'Unified provider interfaces supporting OpenAI, Anthropic, Google Gemini, and Groq.',
      icon: Cpu,
    },
  ];

  return (
    <section id="tech-stack" className="py-16 sm:py-20 border-t border-border/60 bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-teal-600 dark:text-teal-400">
            Architecture & Portfolio
          </h2>
          <p className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            Built with modern, production-grade engineering
          </p>
          <p className="mt-3 text-sm text-muted-foreground">
            Designed as an extensible, resilient multi-agent platform for enterprise and developer workflows.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {stack.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.name}
                className="rounded-xl border border-border bg-card p-5 shadow-xs flex items-start gap-3.5 hover:border-teal-500/30 transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 shrink-0">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-foreground">{item.name}</h3>
                    <span className="text-[11px] font-medium text-teal-700 dark:text-teal-400 bg-teal-100 dark:bg-teal-950/80 px-2 py-0.5 rounded-full">
                      {item.category}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
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
