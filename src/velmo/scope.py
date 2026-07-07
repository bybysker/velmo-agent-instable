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
    "après-vente",
    "after_sales",
    "statut",
}


def is_in_scope(text: str) -> bool:
    """Renvoie True si le message relève bien du support commandes/livraisons Velmo.

    BUG CORRIGÉ : l'ancienne implémentation comparait les mots du texte contre
    eux-mêmes (any(topic in lowered for topic in lowered.split())), ce qui
    retournait toujours True.
    On compare maintenant chaque mot contre IN_SCOPE_TOPICS.
    """
    lowered = text.lower()
    return any(topic in lowered for topic in IN_SCOPE_TOPICS)
