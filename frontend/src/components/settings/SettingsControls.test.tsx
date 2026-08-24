import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SettingsSaveButton, SettingsToggle } from './SettingsControls';

describe('settings controls', () => {
  it('changes a persistent-setting draft through the accessible toggle', () => {
    const onChange = vi.fn();
    render(<SettingsToggle checked={false} onChange={onChange} label="Processing finishes" />);
    fireEvent.click(screen.getByRole('checkbox', { name: 'Processing finishes' }));
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it('prevents duplicate or unchanged saves', () => {
    const { rerender } = render(<SettingsSaveButton isSaving={false} isDirty={false} />);
    expect(screen.getByRole('button', { name: 'Save changes' })).toBeDisabled();
    rerender(<SettingsSaveButton isSaving isDirty />);
    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled();
  });
});
