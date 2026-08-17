from meeting_notes_agent.llms.API_Based.openai import get_openai_llm
from meeting_notes_agent.llms.prompts.extract_decisions_prompt import EXTRACTION

llm = get_openai_llm()

def extract_meeting_data(transcript: str) -> dict:
    """
    Extracts meeting data from the transcript using an LLM.

    Args:
        transcript (str): The transcript text.
    Returns:
        dict: A dictionary containing extracted meeting data.
    """
    system_prompt = EXTRACTION 

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = llm.invoke(messages)
    return {"extracted_data": result.content}
    