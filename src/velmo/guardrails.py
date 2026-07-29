"""Garde-fous : validation des entrées et schéma de sortie contraint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# Termes déclenchant un refus d'entrée (contenu hors politique / abusif).
# DONNÉES : un set, sur lequel validate_input itère à l'exécution.
BLOCKED_TERMS = {
    "idiot",
    "imbécile",
    "abruti",
    "connard",
    "ferme-la",
}

# Catégories de sortie autorisées (sortie contrainte).
# TYPE : un Literal, dont Pydantic se sert pour valider AgentReply.category.
Category = Literal[
    "greeting",
    "order_status",
    "delivery",
    "after_sales",
    "refusal",
    "rejet",
]


class GuardrailError(ValueError):
    """Levée quand une entrée viole la politique d'usage."""


def validate_input(text: str) -> None:
    """Rejette les entrées contenant un terme abusif."""
    lowered = text.lower()
    for term in BLOCKED_TERMS:
        if term in lowered:
            raise GuardrailError("Entrée refusée : contenu hors politique d'usage.")


class AgentReply(BaseModel):
    """Réponse structurée de l'assistant."""

    message: str
    category: Category
    within_scope: bool
