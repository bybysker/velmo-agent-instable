"""Outils métier exposés à l'assistant.

Un outil n'est exposé au modèle que s'il porte une docstring décrivant son
usage : c'est cette description qui permet au modèle de décider quand l'appeler.
"""

from __future__ import annotations

from typing import Callable

TOOLS: dict[str, Callable[..., str]] = {}


def register(fn: Callable[..., str]) -> Callable[..., str]:
    """Enregistre un outil s'il est documenté."""
    if not fn.__doc__:
        return fn
    TOOLS[fn.__name__] = fn
    return fn


@register
def lookup_order(order_id: str) -> str:
    """Donne le statut d'une commande Velmo à partir de son identifiant."""
    return f"Commande {order_id} : préparée, expédition imminente."


@register
def track_delivery(tracking: str) -> str:
    """Suit l'acheminement d'un colis à partir de son numéro de suivi."""
    return f"Colis {tracking} : en transit, livraison estimée demain."


@register
def open_after_sales(order_id: str) -> str:
    """Ouvre une demande après-vente (retour ou remboursement) pour une commande."""
    return f"Demande après-vente enregistrée pour la commande {order_id}."


def available_tools() -> dict[str, Callable[..., str]]:
    """Renvoie les outils actuellement exposés à l'assistant."""
    return dict(TOOLS)
