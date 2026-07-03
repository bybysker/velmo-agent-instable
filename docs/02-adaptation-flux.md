# Partie 2 — Cadrer l'adaptation du flux au nouveau besoin

---

## Contexte

> *"Les demandes de retour et de remboursement sont désormais regroupées sous un même parcours « après-vente » (`after_sales`)."*

Avant, deux parcours séparés. Après, une seule porte d'entrée.

---

## 1. Décrire le flux cible et ses points d'écart avec l'existant

### Flux cible

```
Message utilisateur
        │
        ▼
┌──────────────────────┐
│  Détection intention │
└──────────┬───────────┘
           │
     ┌─────┴──────────────────────────┐
     │              │                 │
 Commande       Livraison       Retour / Remboursement
     │              │                 │
     ▼              ▼                 ▼
lookup_order  track_delivery   open_after_sales  ← PARCOURS UNIFIÉ
```

### Points d'écart avec l'existant

> Source : `flow.py` — `class Intent`, `_KEYWORDS`, `_ROUTES`

| Composant | Avant | Après |
|-----------|-------|-------|
| Intentions | `RETURN`, `REFUND` (deux valeurs) | `AFTER_SALES` (une seule) |
| Mots-clés | `"retour" → return`, `"remboursement" → refund` | `"retour" → after_sales`, `"remboursement" → after_sales` |
| Outil appelé | `open_return` et `open_refund` | `open_after_sales` uniquement |

> **Anomalie actuelle :** les mots-clés pointent déjà vers `after_sales` dans le code, mais l'intention n'existe pas encore dans l'enum.

---

## 2. Définir la vérification de non-régression

On rejoue les 5 conversations fournies après chaque modification :

| Cas | Ce qu'on vérifie |
|-----|-----------------|
| `ctx-oubli-1` | L'agent se souvient de la commande `4521` au 3e tour |
| `perimetre-1` | Refus poli pour la recette de cookies |
| `perimetre-2` | Refus poli pour le conseil boursier |
| `entree-abusive-1` | Message "imbécile" rejeté proprement |
| `apres-vente-1` | Remboursement routé vers `open_after_sales` |

**Critère de succès :** aucun cas qui passait ne doit échouer après la modification.  
**Outil :** `regression.py`
