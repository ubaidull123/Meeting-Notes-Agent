import os
from pathlib import Path

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv


PROJECT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


def get_openai_api_key() -> str:
    """Load and validate the current project key without caching its value."""
    environment = os.environ.get("ENVIRONMENT", "development").lower()
    # Local developers commonly update .env while the reload server remains
    # alive. Hosted and test environments must keep their injected variables.
    load_dotenv(PROJECT_ENV_FILE, override=environment in {"development", "local"})
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for meeting processing")
    if api_key.lower().startswith(("sk-dummy", "your_", "replace_", "test_")):
        raise RuntimeError(
            "OPENAI_API_KEY is still a placeholder. Update the project .env file "
            "with a valid key before starting meeting processing."
        )
    return api_key


def get_openai_llm():
    """Return a fresh chat client using the latest project configuration."""
    api_key = get_openai_api_key()
    return ChatOpenAI(
        model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        temperature=0,
        api_key=api_key,
        timeout=float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "60")),
        max_retries=0,
    )
