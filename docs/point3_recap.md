# Point 3 — Adapter le flux au nouveau besoin métier — Récap

> **Note de partage.** Synthèse de ce qui a été fait au point 3.
> Critère d'évaluation visé : *« Le flux correspond au nouveau besoin métier. »*

## 1. Nouveau besoin métier

Les demandes de **retour** et de **remboursement** doivent être traitées par un
**parcours après-vente unifié** (une seule intention `AFTER_SALES`, un seul outil
`open_after_sales`).

## 2. Méthode

**Test-first / non-régression** : on s'appuie sur les 5 cas fournis. Pour chaque
défaut, on écrit (ou on a) un test qui prouve le comportement attendu, on le voit
**rouge**, on corrige, on le repasse **vert** — sans casser les autres.

Base de départ mesurée : **6 tests en échec / 15 passés**.
Après le point 3 : **4 en échec / 19 passés** (les 4 restants relèvent des points
suivants : mémoire & rôle).

## 3. Ce qui a été fait

```text
+---------+-------------------------+-------------------------------------+-----------------+--------------------------------------------------+
| Réf     | Défaut (existant)       | Correction (cible)                  | Fichier         | Test de verrouillage                             |
+=========+=========================+=====================================+=================+==================================================+
| F1      | `Intent("after_sales")` | Ajout `Intent.AFTER_SALES` ;        | `flow.py`       | `test_route_after_sales_to_tool`                 |
|         | plantait (membre        | `_ROUTES` -> `open_after_sales`     |                 |                                                  |
|         | manquant) ; routes      |                                     |                 |                                                  |
|         | basées sur              |                                     |                 |                                                  |
|         | `RETURN`/`REFUND`       |                                     |                 |                                                  |
+---------+-------------------------+-------------------------------------+-----------------+--------------------------------------------------+
| F2      | "commande" masquait     | Classification par priorité métier  | `flow.py`       | `test_classify_after_sales_even_with_order_word` |
|         | "remboursement" ->      | explicite (`_PRIORITY`, after_sales |                 | (ajouté)                                         |
|         | remboursement classé en | en tête)                            |                 |                                                  |
|         | `order_status`          |                                     |                 |                                                  |
+---------+-------------------------+-------------------------------------+-----------------+--------------------------------------------------+
| OUTIL   | `track_delivery` non    | Ajout d'une docstring               | `tools.py`      | `test_track_delivery_is_exposed`                 |
|         | exposé (docstring       |                                     |                 |                                                  |
|         | manquante -> non        |                                     |                 |                                                  |
|         | enregistré)             |                                     |                 |                                                  |
+---------+-------------------------+-------------------------------------+-----------------+--------------------------------------------------+
| AGENT   | `_CATEGORY_BY_INTENT`   | Ajout `Intent.AFTER_SALES:          | `agent.py`      | `test_agent_routes_refund_to_after_sales`        |
|         | sans `AFTER_SALES` ->   | "after_sales"`                      |                 | (ajouté)                                         |
|         | remboursement étiqueté  |                                     |                 |                                                  |
|         | `greeting`              |                                     |                 |                                                  |
+---------+-------------------------+-------------------------------------+-----------------+--------------------------------------------------+
| HARNAIS | `regression.py` lisait  | Lecture de                          | `regression.py` | `test_problem_conversations_load`                |
|         | `conversations.json`    | `conversations_problematiques.json` |                 |                                                  |
|         | (inexistant)            |                                     |                 |                                                  |
+---------+-------------------------+-------------------------------------+-----------------+--------------------------------------------------+
```

### Vérification de bout en bout

> *« Je veux un remboursement pour la commande 4490. »*
> → `classify` = **AFTER_SALES** → `route` = **open_after_sales** → `category` = **after_sales**

## 4. Ce qui reste à faire (hors périmètre du point 3)

Les 4 tests encore rouges relèvent des **points suivants** :

```text
+-----------------------------------------------+------------------------------------------------+---------------+
| Test rouge                                    | Axe                                            | Point         |
+===============================================+================================================+===============+
| `test_agent_keeps_conversation_context`       | Mémoire (M1 : historique non réinjecté)        | Point mémoire |
+-----------------------------------------------+------------------------------------------------+---------------+
| `test_agent_refuses_out_of_scope`             | Rôle (R1 : scope non branché)                  | Point rôle    |
+-----------------------------------------------+------------------------------------------------+---------------+
| `test_validate_input_rejects_abusive_message` | Rôle (R3 : match exact au lieu de sous-chaîne) | Point rôle    |
+-----------------------------------------------+------------------------------------------------+---------------+
| `test_reply_rejects_unknown_category`         | Rôle (category non contrainte)                 | Point rôle    |
+-----------------------------------------------+------------------------------------------------+---------------+
```

*Note : `memory.py` (M2, fenêtre glissante) et `scope.py` (R2, logique de scope)
ont déjà été corrigés en amont mais seront committés avec leurs axes respectifs.*

## 5. Points d'attention

- **`.env.example`** contient actuellement une **vraie clé API** : à remettre en
  **placeholders** avant tout commit/push (le secret ne doit vivre que dans
  `.env`, ignoré par Git).
- **Nettoyage optionnel** : les membres `Intent.RETURN` / `Intent.REFUND` (enum)
  et leurs entrées dans `_CATEGORY_BY_INTENT` sont désormais **morts** (jamais
  renvoyés par `classify`). Peuvent être supprimés pour une source de vérité unique.

## 6. Périmètre du commit « Point 3 »

Fichiers du **flux uniquement** :
`flow.py`, `tools.py`, `agent.py`, `regression.py`, `tests/test_flow.py`,
`tests/test_agent.py`.
Laissés de côté (autres axes / amorçage / secret) : `memory.py`, `scope.py`,
`config.py`, `prompts.py`, `Makefile`, `.env.example`.
