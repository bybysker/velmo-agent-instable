"""Mémoire de conversation : conserve les derniers tours pour garder le contexte."""

from __future__ import annotations

from dataclasses import dataclass, field

Turn = tuple[str, str]  # (role, content)


@dataclass
class ConversationMemory:
    """Fenêtre glissante sur les tours de conversation.

    `window` borne le nombre de tours réinjectés dans le prompt du modèle.
    Les tours les plus récents sont toujours conservés.
    """

    window: int = 8
    _turns: list[Turn] = field(default_factory=list)

    def record(self, role: str, content: str) -> None:
        """Ajoute un tour à l'historique."""
        self._turns.append((role, content))

    def history(self) -> list[Turn]:
        """Renvoie les tours les plus récents à réinjecter dans le prompt (bornés par `window`)."""
        # BUG CORRIGÉ : on prend les N derniers tours, pas les N premiers.
        # Avant : self._turns[: self.window]  → gardait les plus ANCIENS
        # Après : self._turns[-self.window :]  → garde les plus RÉCENTS
        return self._turns[-self.window :]

    def clear(self) -> None:
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
