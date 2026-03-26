"""
LLM client factory for the AI Resume Screener.

Uses LangChain's ChatGroq — consistent with the proven approach in
notebooks/02_structured_extraction.ipynb which used .with_structured_output()
rather than the instructor library. This pattern is simpler, requires no
extra patching, and is the standard LangGraph-compatible approach.
"""
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Default models — can be overridden via environment variables or configs/config.yaml
DEFAULT_LLM_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FALLBACK_LLM_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "llama3-8b-8192")


def get_llm(model: str = DEFAULT_LLM_MODEL, temperature: float = 0.0) -> ChatGroq:
    """
    Returns a ChatGroq LLM instance.

    Uses the LangChain ChatGroq integration so that .with_structured_output()
    can be called directly on the returned object — the proven pattern from
    notebooks/02_structured_extraction.ipynb.

    Args:
        model: The Groq model ID to use.
        temperature: Sampling temperature. Use 0.0 for strict extraction,
                     0.1-0.2 for analytical and narrative tasks.

    Returns:
        A configured ChatGroq instance.

    Raises:
        ValueError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is not set. Please check your .env file."
        )
    return ChatGroq(api_key=api_key, model=model, temperature=temperature)
