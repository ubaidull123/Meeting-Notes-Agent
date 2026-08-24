"""Optional LangSmith tracing configuration for the meeting workflow."""
import os

from dotenv import load_dotenv


def configure_langsmith() -> bool:
    """Enable LangSmith only when a key has been configured."""
    load_dotenv()
    os.environ.setdefault("LANGSMITH_PROJECT", "meeting-notes-agent")
    if not os.getenv("LANGSMITH_API_KEY"):
        return False
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    return os.getenv("LANGSMITH_TRACING", "").lower() == "true"
