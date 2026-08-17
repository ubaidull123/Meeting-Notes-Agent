from src.llms.API_Based.openai import get_openai_llm

llm = get_openai_llm()

def extract_meeting_data(transcript: str) -> dict:
    """
    Extracts meeting data from the transcript using an LLM.

    Args:
        transcript (str): The transcript text.
    Returns:
        dict: A dictionary containing extracted meeting data.
    """
    system_prompt = (
        "You are a meeting notes extractor. Given a cleaned meeting transcript, "
        "extract the following structured information:\n\n"
        "1. Meeting Title: A concise title for the meeting.\n"
        "2. Date and Time: The date and time of the meeting.\n"
        "3. Participants: A list of participants in the meeting.\n"
        "4. Agenda: The agenda items discussed in the meeting.\n"
        "5. Key Points: The main discussion points and decisions made.\n"
        "6. Action Items: Specific tasks assigned with owner and due date if mentioned.\n\n"
        "Return ONLY the extracted information in JSON format."
    )

    messages = [
        ("system", system_prompt),
        ("human", transcript),
    ]

    result = llm.invoke(messages)
    return {"extracted_data": result.content}
    