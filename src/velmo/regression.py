"""Rejeu des conversations problématiques pour vérifier la non-régression.

En ligne de commande, rejoue les conversations fournies pour la démonstration :

    uv run python -m velmo.regression            # sur le modèle Azure réel (.env requis)
    uv run python -m velmo.regression --offline  # sans modèle, pour vérifier le flux
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .agent import LLMClient, VelmoAgent
from .guardrails import GUARDRAIL_REFUSAL_MESSAGE, AgentReply, GuardrailError

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_problem_conversations(path: Path | None = None) -> list[dict[str, Any]]:
    """Charge le jeu de conversations problématiques fourni.

    BUG CORRIGÉ : le nom de fichier était "conversations.json" alors que le
    fichier réel s'appelle "conversations_problematiques.json".
    """
    path = path or DATA_DIR / "conversations_problematiques.json"
    cases: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return cases


def replay(case: dict[str, Any], agent: VelmoAgent) -> list[AgentReply | GuardrailError]:
    """Rejoue les messages client d'une conversation et renvoie un résultat par message.

    Seuls les tours `user` sont renvoyés à l'agent : les tours `assistant` du jeu
    de données sont ceux de l'ancienne version et sont régénérés par l'agent rejoué.
    Une entrée rejetée par les garde-fous produit la `GuardrailError` levée.
    """
    outcomes: list[AgentReply | GuardrailError] = []
    for turn in case["turns"]:
        if turn["role"] != "user":
            continue
        try:
            outcomes.append(agent.handle(turn["content"]))
        except GuardrailError as error:
            outcomes.append(error)
    return outcomes


class _OfflineLLM:
    """Modèle factice : montre ce que l'agent transmettrait au vrai modèle."""

    def complete(self, system: str, history: list[tuple[str, str]], user: str) -> str:
        return f"[réponse du modèle — {len(history)} messages d'historique transmis]"


def main(argv: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    llm: LLMClient
    if "--offline" in argv:
        llm = _OfflineLLM()
    else:
        from dotenv import load_dotenv

        from .llm import get_llm

        load_dotenv()
        llm = get_llm()

    for case in load_problem_conversations():
        print(f"\n=== {case['id']} — {case['label']}")
        print(f"    Attendu : {case['attendu']}")
        messages = [turn["content"] for turn in case["turns"] if turn["role"] == "user"]
        for message, outcome in zip(messages, replay(case, VelmoAgent(llm=llm))):
            print(f"\n  Client : {message}")
            if isinstance(outcome, GuardrailError):
                print(f"  Velmo  : {GUARDRAIL_REFUSAL_MESSAGE}  [garde-fou d'entrée]")
            else:
                print(f"  Velmo  : {outcome.message}  [{outcome.category}]")


if __name__ == "__main__":
    main(sys.argv[1:])
