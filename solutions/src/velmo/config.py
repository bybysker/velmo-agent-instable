"""Chargement de la configuration depuis l'environnement."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Paramètres de connexion au service Azure AI Inference."""

    endpoint: str
    api_key: str
    model: str


def load_settings() -> Settings:
    """Lit les variables d'environnement et renvoie les paramètres du service."""
    return Settings(
        endpoint=os.environ["AZURE_AI_INFERENCE_ENDPOINT"],
        api_key=os.environ["AZURE_AI_INFERENCE_API_KEY"],
        model=os.environ.get("AZURE_AI_INFERENCE_MODEL", "Kimi-K2.6"),
    )
