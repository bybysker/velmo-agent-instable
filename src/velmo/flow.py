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
    RETURN = "return"
    REFUND = "refund"
    AFTER_SALES = "after_sales"   #ajouté pour regrouper les intentions de retour et de remboursement


# Intentions par ordre de priorité métier : la première dont un mot-clé
# apparaît dans le message l'emporte (after_sales prime sur order_status).
_PRIORITY: list[tuple[Intent, list[str]]] = [ 
    (Intent.AFTER_SALES, ["retour", "renvoyer", "remboursement", "rembourser"]),
    (Intent.DELIVERY, ["livraison", "colis", "où est"]),
    (Intent.ORDER_STATUS, ["commande", "statut"]),
    (Intent.GREETING, ["bonjour", "salut"]),
]

# Intention -> nom de l'outil à invoquer.
_ROUTES: dict[Intent, str] = {
    Intent.GREETING: "greet",
    Intent.ORDER_STATUS: "lookup_order",
    Intent.DELIVERY: "track_delivery",
    Intent.AFTER_SALES: "open_after_sales",
}


def classify(text: str) -> Intent:
    """Devine l'intention métier en testant les intentions par ordre de priorité."""
    lowered = text.lower()
    for intent, keywords in _PRIORITY:  
        if any(keyword in lowered for keyword in keywords): # adaptation pour regrouper les intentions de retour et de remboursement sous after_sales
            return intent
    return Intent.GREETING


def route(intent: Intent) -> str:
    """Renvoie le nom de l'outil correspondant à une intention."""
    return _ROUTES[intent]
