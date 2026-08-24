"""API v1 routes package."""
from meeting_notes_agent.api.v1 import auth, users, meetings, tasks, admin, settings

__all__ = ["auth", "users", "meetings", "tasks", "admin", "settings"]
