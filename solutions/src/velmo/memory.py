"""Mémoire de conversation : conserve les derniers tours pour garder le contexte."""

from __future__ import annotations

from dataclasses import dataclass, field

Turn = tuple[str, str]  # (role, content)


@dataclass
class ConversationMemory:
    """Fenêtre glissante sur les tours de conversation.

    `window` borne le nombre de tours réinjectés dans le prompt du modèle.
    """

    window: int = 8
    _turns: list[Turn] = field(default_factory=list)

    def record(self, role: str, content: str) -> None:
        """Ajoute un tour à l'historique."""
        self._turns.append((role, content))

    def history(self) -> list[Turn]:
        """Renvoie les tours à réinjecter dans le prompt (bornés par `window`)."""
        return self._turns[-self.window :]

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
