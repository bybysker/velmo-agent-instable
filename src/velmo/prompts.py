"""Construction du prompt système de l'assistant."""

from __future__ import annotations

SYSTEM_PROMPT = (
    "Tu es {persona}, l'assistant de support de Velmo. "
    "Tu réponds uniquement aux questions liées aux commandes, livraisons, "
    "retours et remboursements Velmo. "
    "Tu restes courtois, concis et tu refuses poliment ce qui sort de ce périmètre."
)


def build_system_prompt(persona: str = "Velmo Assistant") -> str:
    """Assemble le prompt système pour la persona donnée."""
    return SYSTEM_PROMPT.format(persona=persona)
