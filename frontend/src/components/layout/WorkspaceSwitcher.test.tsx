import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useTeam } from '../../context/TeamContext';
import { Team } from '../../types/team';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';

vi.mock('../../context/TeamContext', () => ({
  useTeam: vi.fn(),
}));

const selectTeam = vi.fn();
const createTeam = vi.fn();

const team = (id: string, name: string): Team => ({
  id,
  name,
  role: 'owner',
  created_by: 1,
  created_at: '2026-08-25T00:00:00Z',
  updated_at: '2026-08-25T00:00:00Z',
});

function mockTeams(teams: Team[], activeTeam: Team | null = teams[0] ?? null) {
  vi.mocked(useTeam).mockReturnValue({
    teams,
    activeTeam,
    activeRole: activeTeam?.role ?? null,
    isLoading: false,
    canManageActiveTeam: activeTeam?.role === 'owner' || activeTeam?.role === 'admin',
    selectTeam,
    createTeam,
    roleForTeam: vi.fn(),
    canManageTeam: vi.fn(),
    refreshTeams: vi.fn(),
  });
}

describe('WorkspaceSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('keeps the empty state compact and contains actions in an opaque popover', async () => {
    mockTeams([], null);
    const user = userEvent.setup();
    render(<WorkspaceSwitcher collapsed={false} />);

    await user.click(screen.getByRole('button', { name: /choose workspace/i }));

    const menu = screen.getByRole('menu');
    expect(menu).toHaveClass('absolute', 'bg-popover', 'inset-x-0', 'top-full', 'w-full');
    expect(screen.getByText('Switch workspace')).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: /create workspace/i })).toBeInTheDocument();
  });

  it('opens the existing create workspace dialog from the popover', async () => {
    mockTeams([team('one', 'Workspace One')]);
    const user = userEvent.setup();
    render(<WorkspaceSwitcher collapsed={false} />);

    await user.click(screen.getByRole('button', { name: /workspace one/i }));
    await user.click(screen.getByRole('menuitem', { name: /create workspace/i }));

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: /create workspace/i })).toBeInTheDocument();
  });

  it('selects another workspace and closes the popover', async () => {
    const workspaceOne = team('one', 'Workspace One');
    const workspaceTwo = team('two', 'Workspace Two');
    mockTeams([workspaceOne, workspaceTwo], workspaceOne);
    const user = userEvent.setup();
    render(<WorkspaceSwitcher collapsed={false} />);

    await user.click(screen.getByRole('button', { name: /workspace one/i }));
    await user.click(screen.getByRole('menuitem', { name: /workspace two/i }));

    expect(selectTeam).toHaveBeenCalledWith('two');
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('closes the popover with Escape', async () => {
    mockTeams([team('one', 'Workspace One')]);
    const user = userEvent.setup();
    render(<WorkspaceSwitcher collapsed={false} />);

    await user.click(screen.getByRole('button', { name: /workspace one/i }));
    await user.keyboard('{Escape}');

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});
