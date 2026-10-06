"""Classification d'intention et routage vers le bon outil métier.

Évolution métier : les demandes de retour et de remboursement sont désormais
regroupées sous un même parcours « après-vente » représenté par Intent.AFTER_SALES.
Les anciennes valeurs RETURN et REFUND sont supprimées.
"""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    GREETING = "greeting"
    ORDER_STATUS = "order_status"
    DELIVERY = "delivery"
    # BUG CORRIGÉ : RETURN et REFUND fusionnés en AFTER_SALES (nouveau parcours métier)
    AFTER_SALES = "after_sales"


# Mots-clés par intention, du plus spécifique au plus générique : la première
# intention reconnue l'emporte. « Remboursement pour la commande 4490 » doit
# partir en après-vente, pas en statut de commande ; une salutation suivie
# d'une demande (« Bonjour, ma commande… ») ne doit pas rester un simple bonjour.
_KEYWORDS_BY_PRIORITY: list[tuple[Intent, tuple[str, ...]]] = [
    (Intent.AFTER_SALES, ("retour", "renvoyer", "rembours", "après-vente")),
    (Intent.DELIVERY, ("livraison", "livré", "colis", "suivi", "où est")),
    (Intent.ORDER_STATUS, ("commande", "statut")),
    (Intent.GREETING, ("bonjour", "salut")),
]

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
    for intent, keywords in _KEYWORDS_BY_PRIORITY:
        if any(keyword in lowered for keyword in keywords):
            return intent
    return Intent.GREETING


def route(intent: Intent) -> str:
    """Renvoie le nom de l'outil correspondant à une intention."""
    return _ROUTES[intent]
