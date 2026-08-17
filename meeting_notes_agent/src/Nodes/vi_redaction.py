
from src.llms.API_Based.openai import get_openai_llm
from src.data.input.meeting_data import MeetingInput, MeetingData
def redact_sensitive_info(meeting_data: MeetingData) -> MeetingData:
    """
    Redacts sensitive information from the given text based on a list of sensitive terms.

    Args:
        text (str): The input text to be redacted.
        sensitive_terms (list[str]): A list of sensitive terms to be redacted.

    Returns:
        str: The redacted text with sensitive terms replaced by '[REDACTED]'.
    """
    