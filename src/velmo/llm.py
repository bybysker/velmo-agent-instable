"""Client LLM réel adossé à Azure AI Inference (Kimi-K2.6).

L'import du SDK est différé pour que le coeur applicatif (mémoire, garde-fous,
flux) reste testable sans dépendre du SDK ni d'un endpoint joignable.
"""

from __future__ import annotations

from typing import Any

from .config import load_settings


class AzureLLM:
    """Adapte le modèle de chat Azure à l'interface `LLMClient` de l'agent."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def complete(self, system: str, history: list[tuple[str, str]], user: str) -> str:
        messages = [{"role": "system", "content": system}]
        for role, content in history:
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user})
        return str(self._model.invoke(messages).content)


def get_llm() -> AzureLLM:
    """Construit le client Azure AI Inference à partir de l'environnement."""
    from langchain_azure_ai.chat_models import (  # type: ignore[import-untyped]
        AzureAIOpenAIApiChatModel,
    )

    settings = load_settings()
    model = AzureAIOpenAIApiChatModel(
        endpoint=settings.endpoint,
        credential=settings.api_key,
        model=settings.model,
    )
    return AzureLLM(model)
