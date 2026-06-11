"""Rejeu des conversations problématiques pour vérifier la non-régression."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def load_problem_conversations(path: Path | None = None) -> list[dict]:
    """Charge le jeu de conversations problématiques fourni."""
    path = path or DATA_DIR / "conversations_problematiques.json"
    return json.loads(path.read_text(encoding="utf-8"))
