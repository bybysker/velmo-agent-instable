"""Classification d'intention et routage vers le bon outil métier.

Le périmètre métier a évolué : les demandes de retour et de remboursement
sont désormais regroupées sous un même parcours « après-vente » (after_sales).
"""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    ORDER_STATUS = "order_status"
    DELIVERY = "delivery"
    AFTER_SALES = "after_sales"


# Mots-clés -> libellé d'intention (taxonomie métier courante).
_KEYWORDS: dict[str, str] = {
    "bonjour": "greeting",
    "salut": "greeting",
    "commande": "order_status",
    "statut": "order_status",
    "livraison": "delivery",
    "colis": "delivery",
    "où est": "delivery",
    "retour": "after_sales",
    "renvoyer": "after_sales",
    "remboursement": "after_sales",
    "rembourser": "after_sales",
}

# Intention -> nom de l'outil à invoquer.
_ROUTES: dict[Intent, str] = {
    Intent.GREETING: "greet",
    Intent.ORDER_STATUS: "lookup_order",
    Intent.DELIVERY: "track_delivery",
    Intent.AFTER_SALES: "open_after_sales",
}


def classify(text: str) -> Intent:
    """Devine l'intention métier d'un message à partir de mots-clés."""
    lowered = text.lower()
    for keyword, label in _KEYWORDS.items():
        if keyword in lowered:
            return Intent(label)
    return Intent.GREETING


def route(intent: Intent) -> str:
    """Renvoie le nom de l'outil correspondant à une intention."""
    return _ROUTES[intent]
