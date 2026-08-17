from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)  


def get_openai_llm():
    """
    Returns an OpenAI LLM instance for use in the meeting notes agent.
    """
    return ChatOpenAI(model="gpt-5.6-luna")

def get_openai_whisper_llm():
    """
    Returns an OpenAI Whisper LLM instance for use in the meeting notes agent.
    """
    return ChatOpenAI(model="whisper-large-v3")


if __name__ == "__main__":
    llm = get_openai_llm()
    print(llm.invoke("Hello, how are you?"))
    whisper_llm = get_openai_whisper_llm()
    print(whisper_llm)
