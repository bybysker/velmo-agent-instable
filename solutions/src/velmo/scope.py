"""Contrôle de périmètre : l'assistant ne traite que les sujets support Velmo."""

from __future__ import annotations

IN_SCOPE_TOPICS = {
    "commande",
    "commandes",
    "livraison",
    "livraisons",
    "colis",
    "retour",
    "retours",
    "remboursement",
    "remboursements",
    "facture",
    "factures",
}


def is_in_scope(text: str) -> bool:
    """Renvoie True si le message relève bien du support commandes/livraisons Velmo."""
    lowered = text.lower()
    return any(topic in lowered for topic in IN_SCOPE_TOPICS)
