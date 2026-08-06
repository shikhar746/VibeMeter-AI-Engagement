import logging
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
logger = logging.getLogger(__name__)

_llm_instance: ChatGroq | None = None


def get_llm() -> ChatGroq:
    """Return the shared LLM instance, creating it on first call."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    _llm_instance = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        api_key=api_key,
    )
    logger.info("Groq LLM initialised (model=llama-3.3-70b-versatile)")
    return _llm_instance


llm = get_llm()
