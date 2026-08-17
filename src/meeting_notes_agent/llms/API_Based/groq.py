from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv(override=True)

def get_groq_llm():
    """
    Returns a Groq LLM instance for use in the meeting notes agent.
    """
    return ChatGroq(model="" )

def get_groq_whisper_llm():
    """
    Returns a Groq Whisper LLM instance for use in the meeting notes agent.
    """
    return ChatGroq(model="whisper")

if __name__ == "__main__":
    llm = get_groq_llm()
    print(llm.invoke("Hello, how are you?"))
    whisper_llm = get_groq_whisper_llm()
    print(whisper_llm)

    