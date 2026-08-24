import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { buildPipelineSteps, ProcessingTimeline } from './ProcessingTimeline';

describe('ProcessingTimeline', () => {
  it('renders every stage completed without an active spinner for a completed workflow', () => {
    const { container } = render(<ProcessingTimeline status="completed" sourceType="supplied_transcript" progressPercentage={100} />);
    expect(buildPipelineSteps({ status: 'completed', sourceType: 'supplied_transcript' }).every(step => step.state === 'completed')).toBe(true);
    expect(container.querySelector('.animate-spin')).not.toBeInTheDocument();
  });

  it('marks only human review active while awaiting review', () => {
    const steps = buildPipelineSteps({ status: 'awaiting_review', sourceType: 'supplied_transcript' });
    expect(steps.map(step => step.state)).toEqual(['completed', 'completed', 'completed', 'active', 'pending', 'pending']);
  });

  it('marks only email active while awaiting email approval', () => {
    const steps = buildPipelineSteps({ status: 'awaiting_email_review', sourceType: 'supplied_transcript' });
    expect(steps.map(step => step.state)).toEqual(['completed', 'completed', 'completed', 'completed', 'active', 'pending']);
  });

  it('shows a failed transcription stage without animation when audio transcription fails', () => {
    const { container } = render(<ProcessingTimeline status="failed" sourceType="audio" currentStage="transcription" errorMessage="Audio format could not be decoded" />);
    const steps = buildPipelineSteps({ status: 'failed', sourceType: 'audio', currentStage: 'transcription' });
    expect(steps[1].state).toBe('failed');
    expect(steps[5].state).toBe('pending');
    expect(container.querySelector('.animate-spin')).not.toBeInTheDocument();
  });
});
