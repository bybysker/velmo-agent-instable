"""Garde-fous : validation des entrées et schéma de sortie contraint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# Termes déclenchant un refus d'entrée (contenu hors politique / abusif).
BLOCKED_TERMS = {
    "idiot",
    "imbécile",
    "abruti",
    "connard",
    "ferme-la",
}


class GuardrailError(ValueError):
    """Levée quand une entrée viole la politique d'usage."""


def validate_input(text: str) -> None:
    """Rejette les entrées contenant un terme abusif."""
    lowered = text.lower()
    for term in BLOCKED_TERMS:
        if term in lowered:
            raise GuardrailError("Entrée refusée : contenu hors politique d'usage.")


Category = Literal["greeting", "order_status", "delivery", "after_sales", "refusal"]


class AgentReply(BaseModel):
    """Réponse structurée de l'assistant."""

    message: str
    category: Category
    within_scope: bool
