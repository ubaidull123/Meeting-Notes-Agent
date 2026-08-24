from meeting_notes_agent.models.task import Task, TaskCollection, TaskStatus, TaskPriority
from meeting_notes_agent.state_schema import MeetingState
from meeting_notes_agent.storage.task_storage import save_tasks


def create_pm_tasks(state: MeetingState) -> dict:
    """
    Convert meeting action items into Task objects and persist them.

    Args:
        state (MeetingState): Current state containing action items and meeting metadata.

    Returns:
        dict: Partial state update with pm_tasks and task_collection.
    """
    # Use original action items for task creation (preserves assignee names), redacted for storage if needed
    action_items = state.action_items if state.action_items else state.redacted_action_items

    if not action_items:
        return {"pm_tasks": [], "task_collection": None}

    tasks = []
    for idx, action_item in enumerate(action_items):
        task = Task(
            title=action_item[:100],  # Truncate long titles
            description=action_item,
            meeting_id=state.meeting_id,
            meeting_title=state.meeting_title or "Untitled Meeting",
            action_item_index=idx,
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            labels=["meeting-action-item"],
        )
        tasks.append(task)

    # Create task collection
    task_collection = TaskCollection(
        meeting_id=state.meeting_id,
        meeting_title=state.meeting_title or "Untitled Meeting",
        tasks=tasks,
    )

    # Persist tasks
    save_tasks(task_collection)

    return {
        "pm_tasks": tasks,
        "task_collection": task_collection,
    }