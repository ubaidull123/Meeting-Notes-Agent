"""Task storage for persisting PM tasks locally."""
import json
from pathlib import Path
from datetime import datetime
from meeting_notes_agent.models.task import TaskCollection


# Storage directory (project root / data / tasks)
STORAGE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "tasks"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def save_tasks(task_collection: TaskCollection) -> Path:
    """
    Save task collection to a JSON file.

    Args:
        task_collection: The TaskCollection to persist.

    Returns:
        Path to the saved file.
    """
    filename = f"{task_collection.meeting_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = STORAGE_DIR / filename

    # Convert to dict for JSON serialization
    data = task_collection.model_dump(mode='json')

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def load_tasks(meeting_id: str) -> list[TaskCollection]:
    """
    Load all task collections for a meeting ID.

    Args:
        meeting_id: The meeting ID to search for.

    Returns:
        List of TaskCollection objects.
    """
    collections = []
    for filepath in STORAGE_DIR.glob(f"{meeting_id}_*.json"):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        collections.append(TaskCollection(**data))
    return collections


def get_all_task_files() -> list[Path]:
    """Get all task storage files sorted by modification time (newest first)."""
    return sorted(STORAGE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)