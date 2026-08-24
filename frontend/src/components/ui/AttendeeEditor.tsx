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
        <label className="text-sm font-medium text-foreground flex items-center gap-1.5">
          <Users className="w-4 h-4 text-teal-600" />
          <span>Meeting Attendees</span>
          <span className="text-xs text-muted-foreground">({attendees.length})</span>
        </label>
        <button
          type="button"
          onClick={handleAdd}
          className="inline-flex items-center gap-1 text-xs font-medium text-teal-600 dark:text-teal-400 hover:text-teal-700 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Attendee</span>
        </button>
      </div>

      <div className="space-y-2">
        {attendees.map((attendee, index) => (
          <div key={index} className="flex items-center gap-2">
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-2">
              <input
                type="text"
                placeholder="Full name (e.g. Alice Johnson)"
                value={attendee.name}
                onChange={(e) => handleUpdate(index, 'name', e.target.value)}
                className="w-full px-3 py-1.5 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-teal-500 placeholder:text-muted-foreground"
              />
              <input
                type="email"
                placeholder="Email address (e.g. alice@company.com)"
                value={attendee.email}
                onChange={(e) => handleUpdate(index, 'email', e.target.value)}
                className="w-full px-3 py-1.5 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-teal-500 placeholder:text-muted-foreground"
              />
            </div>
            <button
              type="button"
              onClick={() => handleRemove(index)}
              disabled={attendees.length <= 1}
              className="p-2 text-muted-foreground hover:text-rose-600 disabled:opacity-30 disabled:cursor-not-allowed rounded-md hover:bg-muted transition-colors"
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
