import React from 'react';
import { Plus, Trash2, Users } from 'lucide-react';

export interface AttendeeItem {
  name: string;
  email: string;
}

interface AttendeeEditorProps {
  attendees: AttendeeItem[];
  onChange: (attendees: AttendeeItem[]) => void;
  error?: string;
}

export const AttendeeEditor: React.FC<AttendeeEditorProps> = ({ attendees, onChange, error }) => {
  const handleAdd = () => {
    onChange([...attendees, { name: '', email: '' }]);
  };

  const handleRemove = (index: number) => {
    if (attendees.length <= 1) return;
    onChange(attendees.filter((_, i) => i !== index));
  };

  const handleUpdate = (index: number, field: keyof AttendeeItem, value: string) => {
    const updated = attendees.map((item, i) => {
      if (i === index) {
        return { ...item, [field]: value };
      }
      return item;
    });
    onChange(updated);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <Users className="h-4 w-4 text-primary" />
          <span>Meeting attendees</span>
          <span className="text-xs text-muted-foreground">({attendees.length})</span>
        </label>
        <button
          type="button"
          onClick={handleAdd}
          className="inline-flex items-center gap-1 text-xs font-semibold text-primary transition-colors hover:underline"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add attendee</span>
        </button>
      </div>

      <div className="space-y-2">
        {attendees.map((attendee, index) => (
          <div key={index} className="flex items-start gap-2 rounded-lg border border-border/70 bg-muted/20 p-2.5">
            <div className="grid flex-1 grid-cols-1 gap-2 sm:grid-cols-2">
              <input
                type="text"
                placeholder="Full name (e.g. Alice Johnson)"
                value={attendee.name}
                onChange={(e) => handleUpdate(index, 'name', e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-ring/20 placeholder:text-muted-foreground"
              />
              <input
                type="email"
                placeholder="Email address (e.g. alice@company.com)"
                value={attendee.email}
                onChange={(e) => handleUpdate(index, 'email', e.target.value)}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-ring/20 placeholder:text-muted-foreground"
              />
            </div>
            <button
              type="button"
              onClick={() => handleRemove(index)}
              disabled={attendees.length <= 1}
              className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-30"
              title="Remove attendee"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {error && <p className="text-xs text-rose-500 mt-1">{error}</p>}
    </div>
  );
};
