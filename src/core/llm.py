"""
LLM client factory for the AI Resume Screener.

Supports multiple LLM providers via the LLM_PROVIDER environment variable:
  - "groq" (default) — uses langchain-groq with ChatGroq
  - "google" — uses native google-genai SDK with a thin adapter

Both providers expose the same interface (.with_structured_output()) so
nodes.py requires zero changes when switching providers.
"""
import json
import os
from typing import Any, Literal, Type

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq
from pydantic import BaseModel

load_dotenv()

LLMProvider = Literal["groq", "google"]

# ------ Per-provider model defaults (override via env vars) ------
_GROQ_DEFAULT_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")
_GOOGLE_DEFAULT_MODEL = os.getenv("GOOGLE_MODEL",  "gemini-2.0-flash")


# ------ Google Gen AI native adapter ------

class GoogleGenAIChat:
    """
    Thin adapter around the native google-genai SDK that mimics the
    LangChain BaseChatModel interface used by nodes.py.

    Only implements the two methods that nodes.py relies on:
      - with_structured_output(schema) → Runnable
      - invoke(input)                  → schema instance

    This avoids the langchain-google-genai dependency while giving direct
    access to the native Gen AI SDK (future-proof, lighter footprint).
    """

    def __init__(self, model: str, temperature: float, api_key: str) -> None:
        try:
            from google import genai
            from google.genai import types as genai_types
        except ImportError as e:
            raise ImportError(
                "google-genai is not installed. Run: pip install google-genai"
            ) from e

        self._model = model
        self._temperature = temperature
        self._client = genai.Client(api_key=api_key)
        self._genai_types = genai_types

    def _messages_to_prompt(self, input: Any) -> str:
        """
        Convert LangChain ChatPromptValue or message list to a plain string
        the google-genai SDK can consume.
        """
        # LangChain passes a ChatPromptValue
        # extract messages from it
        if hasattr(input, "messages"):
            messages = input.messages
        elif isinstance(input, list):
            messages = input
        else:
            return str(input)

        parts = []
        for msg in messages:
            role = getattr(msg, "type", "")
            content = getattr(msg, "content", str(msg))
            if role == "system":
                parts.append(f"[SYSTEM]\n{content}")
            elif role == "human":
                parts.append(f"[USER]\n{content}")
            else:
                parts.append(content)
        return "\n\n".join(parts)

    def with_structured_output(self, schema: Type[BaseModel]) -> "RunnableLambda":
        """
        Returns a Runnable with both sync and async execution paths.
        LangChain uses `afunc` automatically when the node is awaited.
        """
        def _invoke(input: Any) -> BaseModel:
            prompt = self._messages_to_prompt(input)
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=self._genai_types.GenerateContentConfig(
                    temperature=self._temperature,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return schema.model_validate(json.loads(response.text))

        async def _ainvoke(input: Any) -> BaseModel:
            prompt = self._messages_to_prompt(input)
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=self._genai_types.GenerateContentConfig(
                    temperature=self._temperature,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            return schema.model_validate(json.loads(response.text))

        return RunnableLambda(func=_invoke, afunc=_ainvoke)

    def invoke(self, input: Any) -> str:
        """Plain invocation without structured output (used for simple calls)."""
        prompt = self._messages_to_prompt(input)
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=self._genai_types.GenerateContentConfig(
                temperature=self._temperature,
            ),
        )
        return response.text


# ------ Private builder functions ------

def _build_groq(temperature: float) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Please check your .env file."
        )
    return ChatGroq(
        api_key=api_key,
        model=_GROQ_DEFAULT_MODEL,
        temperature=temperature,
    )


def _build_google(temperature: float) -> GoogleGenAIChat:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. Please check your .env file."
        )
    return GoogleGenAIChat(
        model=_GOOGLE_DEFAULT_MODEL,
        temperature=temperature,
        api_key=api_key,
    )


# ------ Public factory ------

def get_llm(temperature: float = 0.0) -> BaseChatModel | GoogleGenAIChat:
    """
    LLM factory — returns the configured provider's chat model.

    Provider is selected via the LLM_PROVIDER environment variable:
      "groq" (default) → ChatGroq (langchain-groq)
      "google" → GoogleGenAIChat (native google-genai adapter)

    Both return objects expose .with_structured_output() — nodes.py is
    unaffected by which provider is active.

    Args:
        temperature: Sampling temperature. 
                     0.0 for strict extraction,
                     0.1-0.2 for analytical and narrative tasks.

    Returns:
        A configured chat model instance for the active provider.

    Raises:
        ValueError: If the required API key is not set.
        ValueError: If LLM_PROVIDER is set to an unsupported value.
    """
    provider: LLMProvider = os.getenv("LLM_PROVIDER", "groq").lower()  # type: ignore[assignment]

    if provider == "groq":
        return _build_groq(temperature)
    elif provider == "google":
        return _build_google(temperature)
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: '{provider}'. "
            "Valid options are: 'groq', 'google'."
        )
