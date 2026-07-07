"""Orchestrateur de l'assistant Velmo : garde-fous, périmètre, mémoire, modèle."""

from __future__ import annotations

from typing import Protocol

from .flow import Intent, classify
from .guardrails import AgentReply, validate_input
from .memory import ConversationMemory
from .prompts import build_system_prompt
from .scope import is_in_scope

_CATEGORY_BY_INTENT = {
    Intent.GREETING: "greeting",
    Intent.ORDER_STATUS: "order_status",
    Intent.DELIVERY: "delivery",
    # BUG CORRIGÉ : RETURN et REFUND n'existent plus ; on mappe AFTER_SALES.
    Intent.AFTER_SALES: "after_sales",
}

REFUSAL_MESSAGE = (
    "Désolé, je ne peux traiter que les demandes liées à vos commandes, "
    "livraisons et retours Velmo."
)


class LLMClient(Protocol):
    """Interface minimale d'un client de complétion."""

    def complete(self, system: str, history: list[tuple[str, str]], user: str) -> str: ...


class VelmoAgent:
    """Assistant de support : applique les garde-fous puis interroge le modèle."""

    def __init__(
        self,
        llm: LLMClient,
        memory: ConversationMemory | None = None,
        persona: str = "Velmo Assistant",
    ) -> None:
        self.llm = llm
        self.memory = memory or ConversationMemory()
        self.persona = persona

    def handle(self, user_message: str) -> AgentReply:
        """Traite un message utilisateur et renvoie une réponse structurée."""
        # 1. Garde-fou d'entrée (abusif → lève GuardrailError)
        validate_input(user_message)

        # 2. BUG CORRIGÉ : vérification du périmètre
        # Avant : is_in_scope() n'était jamais appelé → aucun filtrage
        # Après : on refuse proprement les demandes hors support Velmo
        if not is_in_scope(user_message):
            return AgentReply(
                message=REFUSAL_MESSAGE,
                category="refusal",
                within_scope=False,
            )

        # 3. Classification d'intention
        intent = classify(user_message)
        system = build_system_prompt(self.persona)

        # 4. BUG CORRIGÉ : on passe l'historique réel au LLM
        # Avant : self.llm.complete(system, [], user_message) → historique vide !
        # Après : self.memory.history() injecte les tours précédents
        answer = self.llm.complete(system, self.memory.history(), user_message)

        # 5. Enregistrement du tour en mémoire (après l'appel, avant le prochain)
        self.memory.record("user", user_message)
        self.memory.record("assistant", answer)

        return AgentReply(
            message=answer,
            category=_CATEGORY_BY_INTENT.get(intent, "greeting"),
            within_scope=True,
        )
