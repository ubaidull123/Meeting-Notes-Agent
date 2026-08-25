import React, { useState } from 'react';
import {
  FileText,
  ListTodo,
  CheckCircle2,
  Mail,
  Clock,
  Sparkles,
  User,
  Calendar,
  Layers,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';

export const ProductPreview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'summary' | 'tasks' | 'decisions' | 'review'>('summary');

  return (
    <section className="py-12 sm:py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-teal-600 dark:text-teal-400">
            Interactive Product Preview
          </h2>
          <p className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
            Structured outputs from raw conversations
          </p>
          <p className="mt-3 text-sm sm:text-base text-muted-foreground">
            Explore how Meeting Notes Agent organizes recordings and transcripts into verifiable deliverables.
          </p>
        </div>

        {/* UI Mock Container */}
        <div className="mx-auto max-w-5xl rounded-2xl border border-border bg-card shadow-xl overflow-hidden transition-all">
          {/* Mock Window Top Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/40 px-4 py-3 sm:px-6">
            <div className="flex items-center gap-3">
              <div className="flex gap-1.5" aria-hidden="true">
                <span className="h-3 w-3 rounded-full bg-rose-500/80 inline-block" />
                <span className="h-3 w-3 rounded-full bg-amber-500/80 inline-block" />
                <span className="h-3 w-3 rounded-full bg-emerald-500/80 inline-block" />
              </div>
              <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground ml-2 font-mono">
                <Layers className="h-3.5 w-3.5" />
                <span>app.meetingnotesagent.com / meetings / demo-q3-sync</span>
              </div>
            </div>

            {/* Status Pills */}
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-teal-100 dark:bg-teal-950/60 px-2.5 py-0.5 text-xs font-semibold text-teal-800 dark:text-teal-300">
                <Sparkles className="h-3 w-3" />
                AI Processed
              </span>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-950/60 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                <CheckCircle2 className="h-3 w-3" />
                Completed
              </span>
            </div>
          </div>

          {/* Mock Meeting Header */}
          <div className="p-5 sm:p-6 border-b border-border bg-background">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs font-medium text-teal-700 dark:text-teal-400 mb-1.5">
                  <span>Project: Core Engineering</span>
                  <span>•</span>
                  <span>Sprint Planning & Architecture</span>
                </div>
                <h3 className="text-xl sm:text-2xl font-bold text-foreground">
                  Q3 Roadmap & Architecture Review
                </h3>
                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" /> Aug 24, 2026
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" /> 42 min recording
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <User className="h-3.5 w-3.5" /> 4 Attendees
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs px-3 py-1.5 rounded-lg border border-border bg-muted/50 font-medium text-muted-foreground">
                  Model: GPT-4o / Claude 3.5
                </span>
              </div>
            </div>

            {/* Preview Tabs */}
            <div className="mt-6 flex border-b border-border gap-2 overflow-x-auto" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'summary'}
                onClick={() => setActiveTab('summary')}
                className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'summary'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <FileText className="h-4 w-4" />
                Summary & Insights
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'tasks'}
                onClick={() => setActiveTab('tasks')}
                className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'tasks'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <ListTodo className="h-4 w-4" />
                Action Items (3)
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'decisions'}
                onClick={() => setActiveTab('decisions')}
                className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'decisions'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <CheckCircle2 className="h-4 w-4" />
                Decisions (2)
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'review'}
                onClick={() => setActiveTab('review')}
                className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === 'review'
                    ? 'border-teal-600 text-teal-700 dark:text-teal-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Mail className="h-4 w-4" />
                Follow-up Email Review
              </button>
            </div>
          </div>

          {/* Mock Tab Body Content */}
          <div className="p-5 sm:p-6 bg-muted/10 min-h-[300px]">
            {activeTab === 'summary' && (
              <div className="space-y-4">
                <div className="rounded-xl border border-border bg-card p-4 sm:p-5 shadow-xs">
                  <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-teal-600" />
                    Executive Summary
                  </h4>
                  <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                    The team finalized the Q3 architecture transition plan. The team agreed to adopt
                    LangGraph-based orchestration for async meeting extraction pipelines, maintain BYOK support
                    for privacy-conscious teams, and target latency below 100ms for API response times.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Key Topics Discussed
                    </h5>
                    <ul className="mt-2 space-y-1.5 text-sm text-foreground">
                      <li className="flex items-start gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-teal-500 mt-2 shrink-0" />
                        <span>LangGraph asynchronous pipeline resilience</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-teal-500 mt-2 shrink-0" />
                        <span>PostgreSQL state persistence & audit logging</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-teal-500 mt-2 shrink-0" />
                        <span>Attendee follow-up email approval gate</span>
                      </li>
                    </ul>
                  </div>

                  <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Pipeline Confidence
                    </h5>
                    <div className="mt-3 space-y-2">
                      <div className="flex justify-between text-xs font-medium">
                        <span>Transcription Accuracy</span>
                        <span className="text-teal-700 dark:text-teal-400">99.2%</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-teal-600 rounded-full w-[99%]" />
                      </div>
                      <div className="flex justify-between text-xs font-medium pt-1">
                        <span>Task Extraction Precision</span>
                        <span className="text-teal-700 dark:text-teal-400">100%</span>
                      </div>
                      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-teal-600 rounded-full w-full" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'tasks' && (
              <div className="rounded-xl border border-border bg-card overflow-hidden shadow-xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-border bg-muted/40 text-xs font-semibold text-muted-foreground uppercase">
                      <tr>
                        <th className="px-4 py-3">Task Description</th>
                        <th className="px-4 py-3">Assignee</th>
                        <th className="px-4 py-3">Priority</th>
                        <th className="px-4 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      <tr className="hover:bg-muted/20">
                        <td className="px-4 py-3 font-medium text-foreground">
                          Implement state schema for LangGraph agent pipeline
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">Sarah Chen</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-rose-100 dark:bg-rose-950/60 px-2 py-0.5 text-xs font-medium text-rose-700 dark:text-rose-400">
                            High
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-amber-100 dark:bg-amber-950/60 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
                            In Progress
                          </span>
                        </td>
                      </tr>
                      <tr className="hover:bg-muted/20">
                        <td className="px-4 py-3 font-medium text-foreground">
                          Add BYOK API credential validator for Anthropic and Gemini
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">Alex Rivera</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-amber-100 dark:bg-amber-950/60 px-2 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
                            Medium
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                            Todo
                          </span>
                        </td>
                      </tr>
                      <tr className="hover:bg-muted/20">
                        <td className="px-4 py-3 font-medium text-foreground">
                          Generate editable email review preview dialog
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">Michael Brown</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-teal-100 dark:bg-teal-950/60 px-2 py-0.5 text-xs font-medium text-teal-700 dark:text-teal-400">
                            Normal
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex rounded-full bg-emerald-100 dark:bg-emerald-950/60 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-400">
                            Done
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'decisions' && (
              <div className="space-y-3">
                <div className="rounded-xl border border-border bg-card p-4 shadow-xs flex items-start gap-3.5">
                  <div className="h-8 w-8 rounded-lg bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 flex items-center justify-center shrink-0">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h5 className="text-sm font-semibold text-foreground">
                      Decision: Adopt LangGraph for Multi-Stage Processing
                    </h5>
                    <p className="mt-1 text-sm text-muted-foreground">
                      The team decided to migrate pipeline execution to LangGraph state machines to ensure resilience,
                      step retries, and checkpointing for large audio transcriptions.
                    </p>
                  </div>
                </div>

                <div className="rounded-xl border border-border bg-card p-4 shadow-xs flex items-start gap-3.5">
                  <div className="h-8 w-8 rounded-lg bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 flex items-center justify-center shrink-0">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h5 className="text-sm font-semibold text-foreground">
                      Decision: Enforce Human Review Gate Before Automated Email Dispatch
                    </h5>
                    <p className="mt-1 text-sm text-muted-foreground">
                      All generated attendee follow-up emails will require explicit user approval or edit before sending via Resend or SMTP.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'review' && (
              <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-teal-600" />
                    <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                      Attendee Follow-up Email Draft
                    </span>
                  </div>
                  <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 dark:bg-amber-950/60 px-2.5 py-1 text-xs font-medium text-amber-800 dark:text-amber-300">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Awaiting Human Approval
                  </span>
                </div>

                <div className="space-y-2 text-xs font-mono text-muted-foreground bg-muted/40 p-3 rounded-lg">
                  <div><strong className="text-foreground">To:</strong> team-engineering@example.com</div>
                  <div><strong className="text-foreground">Subject:</strong> [Meeting Recap] Q3 Roadmap & Architecture Review - Action Items</div>
                </div>

                <div className="text-sm text-foreground space-y-2 bg-background p-4 rounded-lg border border-border">
                  <p>Hi Team,</p>
                  <p>Thanks for participating in today’s Q3 roadmap sync. Here is our summarized recap and immediate next steps:</p>
                  <ul className="list-disc pl-5 space-y-1 text-xs sm:text-sm text-muted-foreground">
                    <li>LangGraph state machine architecture approved for pipeline orchestration.</li>
                    <li>3 core action items assigned to Sarah, Alex, and Michael.</li>
                  </ul>
                  <p className="pt-2 text-xs text-muted-foreground">Best regards,<br />Meeting Notes Agent</p>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button type="button" className="px-3 py-1.5 text-xs font-medium rounded-lg border border-border hover:bg-muted text-foreground">
                    Edit Email Draft
                  </button>
                  <button type="button" className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-teal-600 text-white hover:bg-teal-700 flex items-center gap-1.5">
                    Approve & Send
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
