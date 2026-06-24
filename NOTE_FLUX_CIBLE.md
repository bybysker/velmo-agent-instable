# Note de conception - Flux cible Velmo

Question 2 : à partir du nouveau besoin métier, définir comment le flux de
l'agent doit être adapté.

## Le nouveau besoin métier

Le chef de projet demande de regrouper retour et remboursement dans une seule
catégorie : after-sales (après-vente).

- Avant : 2 catégories séparées (return, refund).
- Après : 1 seule catégorie (after-sales).

Je reste en conception. Je DÉCRIS le flux voulu et la vérification ; je ne corrige
pas encore le code (ça, c'est la question 3).

## 1. Le flux cible (le cheminement voulu)

Quand le client demande un retour, un renvoi ou un remboursement :
- l'agent reconnaît UNE seule intention : after-sales,
- et il route vers UN seul parcours : open_after_sales.

Les autres parcours (accueil, statut de commande, suivi de colis) ne changent pas.

## 2. Points d'écart avec l'existant

| | Avant (existant) | Après (flux cible) |
|---|---|---|
| Intentions | 2 séparées : RETURN, REFUND | 1 seule : AFTER_SALES |
| Mots-clés | retour, remboursement | retour, renvoi, remboursement |
| Parcours | 2 routes distinctes | 1 route : open_after_sales |

État actuel du code : la migration est COMMENCÉE mais pas FINIE. Les mots-clés
pointent déjà vers after_sales, mais l'intention AFTER_SALES n'existe pas encore
dans l'enum. C'est l'asymétrie principale à corriger.

En une phrase : le point d'écart, c'est de créer l'intention after-sales et de
faire pointer retour / renvoi / remboursement dessus, puis d'aligner le routage.

## 3. Plan de non-régression

L'agent est en production : je ne change pas sans vérifier que je ne casse rien.

1. Rejouer les conversations fournies (data/conversations_problematiques.json) :
   - apres-vente-1 (remboursement) -> doit maintenant partir vers after-sales,
   - les cas commande / livraison -> doivent rester corrects (inchangés),
   - les cas mémoire / rôle -> comportement inchangé.
2. Relancer la suite de tests (uv run pytest) :
   - les tests du flux after-sales passent au vert,
   - aucun test déjà vert ne devient rouge.
3. Critère de réussite : zéro régression sur les cas fournis.

## 4. Livrables

- Cette note de conception (flux cible + points d'écart + non-régression).
- Le schéma flux cible (docs/schema-flux-cible-velmo.svg) : il montre le AVANT /
  APRÈS et ce qui ne doit pas bouger.

## Ce que je ne fais pas encore

Je ne touche pas au code dans cette étape. Je décris le flux voulu et le plan de
vérification. L'adaptation du code vient après, une fois cette conception validée.
