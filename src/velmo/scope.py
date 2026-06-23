"""Contrôle de périmètre : l'assistant ne traite que les sujets support Velmo."""

from __future__ import annotations

IN_SCOPE_TOPICS = {  # liste de mots-clés pour déterminer si le message est dans le périmètre métier
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
    # return any(topic in lowered for topic in lowered.split())
    return any(
        topic in lowered for topic in IN_SCOPE_TOPICS
    )  # ligne ajouter pour vérifier si le message contient un mot clé du périmètre métier
