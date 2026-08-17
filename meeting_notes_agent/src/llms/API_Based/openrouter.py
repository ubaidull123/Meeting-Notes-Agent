from langchain_openrouter import ChatOpenRouter
from dotenv import load_dotenv

load_dotenv(override=True)

def get_openrouter_llm():
    """
    Returns an OpenRouter LLM instance for use in the meeting notes agent.
    """
    return ChatOpenRouter(model="gpt-5.6-luna")

def get_openrouter_whisper_llm():
    """
    Returns an OpenRouter Whisper LLM instance for use in the meeting notes agent.
    """
    return ChatOpenRouter(model="whisper-large-v3")

if __name__ == "__main__":
    llm = get_openrouter_llm()
    print(llm.invoke("Hello, how are you?"))
    whisper_llm = get_openrouter_whisper_llm()
    print(whisper_llm)