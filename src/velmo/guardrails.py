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

# Catégories de réponse autorisées.
AllowedCategory = Literal[
    "greeting",
    "order_status",
    "delivery",
    "after_sales",
    "refusal",
]


class GuardrailError(ValueError):
    """Levée quand une entrée viole la politique d'usage."""


def validate_input(text: str) -> None:
    """Rejette les entrées contenant un terme abusif.

    BUG CORRIGÉ : l'ancienne vérification utilisait `term == lowered` (égalité
    stricte), donc seul un message composé uniquement du terme était refusé.
    On utilise maintenant `term in lowered` pour détecter le terme dans une phrase.
    """
    lowered = text.lower()
    for term in BLOCKED_TERMS:
        if term in lowered:
            raise GuardrailError("Entrée refusée : contenu hors politique d'usage.")


class AgentReply(BaseModel):
    """Réponse structurée de l'assistant.

    BUG CORRIGÉ : `category` est maintenant un Literal restreint aux valeurs
    autorisées. Avant, n'importe quelle str était acceptée sans validation.
    """

    message: str
    category: AllowedCategory
    within_scope: bool
