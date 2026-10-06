"""Contrôle de périmètre : l'assistant ne traite que les sujets support Velmo."""

from __future__ import annotations

import re

# Racines recherchées en sous-chaîne : « commande » couvre « commandes »,
# « rembours » couvre « remboursement », « rembourser », « remboursé »…
IN_SCOPE_TOPICS = {
    "commande",
    "livraison",
    "livré",
    "colis",
    "suivi",
    "retour",
    "renvoyer",
    "rembours",
    "factur",
    "après-vente",
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


def is_follow_up(text: str, history: list[tuple[str, str]]) -> bool:
    """Renvoie True si un message sans mot-clé métier prolonge une conversation support.

    Exemple : après « ma commande 4521 est en retard », le client écrit
    « Et la précédente, la 4490, où en est-elle ? ». Aucun mot de
    IN_SCOPE_TOPICS, mais la demande est légitime dans ce contexte.

    `history` contient les tours (role, content) déjà échangés et acceptés.
    Attention : une règle trop permissive rouvre la porte aux sorties de rôle
    (« Et une recette de cookies ? » juste après une question de commande).
    """
    # Une relance doit citer un numéro de commande (4 chiffres ou plus) et
    # prolonger une conversation qui portait déjà sur le support Velmo.
    # `history` est seulement lu : l'agent transmet ensuite cette même liste au modèle.
    if not history or not re.search(r"\d{4,}", text):
        return False
    return any(is_in_scope(content) for _, content in history)
