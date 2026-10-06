## Objet

Remise dans les clous de l'agent de support Velmo : **mémoire réparée**, **garde-fous posés** et **flux adapté** au parcours après-vente unifié.

Dossier de conception : [`docs/note_de_diagnostic.md`](docs/note_de_diagnostic.md) (diagnostic, schéma, flux cible, plan de non-régression) · Journal : [`docs/journal_des_choix.md`](docs/journal_des_choix.md)

## Résultat sur les conversations fournies

| Cas | Avant (v0.3.1) | Après |
|---|---|---|
| `ctx-oubli-1` — perte de contexte | ❌ historique vide transmis au modèle | ✅ 4521 et 4490 visibles au dernier tour, relance acceptée |
| `perimetre-1` — recette de cookies | ❌ transmise au modèle | ✅ refus poli, modèle non sollicité |
| `perimetre-2` — conseil boursier | ❌ transmis au modèle | ✅ refus poli, modèle non sollicité |
| `entree-abusive-1` — insulte | ⚠️ bloquée seulement si exacte, chat qui plante | ✅ rejet, message de refus dans le chat |
| `apres-vente-1` — remboursement | ❌ `ValueError` / classé `order_status` | ✅ `after_sales` |

Ces cinq cas sont rejoués automatiquement par `tests/test_regression.py`.

## Changements

**Mémoire**
- Fenêtre glissante qui conserve les derniers messages, et non les premiers (`memory.py`)
- Historique effectivement transmis au modèle (`agent.py`)
- Relances contextuelles rattachées au périmètre grâce à la mémoire (`scope.is_follow_up`) : un message qui cite un numéro de commande et prolonge un échange support est accepté ; une relance hors sujet (« Et une recette de cookies ? ») reste refusée

**Garde-fous**
- Entrée : termes abusifs détectés dans la phrase, rejet des messages vides ou de plus de 1 000 caractères
- Périmètre : `is_in_scope()` corrigée et appelée avant le modèle ; refus typé `refusal`
- Sortie : `category` restreinte à 5 valeurs ; prompt système doté de règles impératives (pas de conseil hors rôle, pas d'invention, résistance au changement de rôle)
- Chat : `GuardrailError` rattrapée, plus de plantage

**Flux**
- `RETURN` + `REFUND` → `AFTER_SALES` → `open_after_sales`
- Priorité explicite entre intentions : `after_sales › delivery › order_status › greeting`

**Divers** : variable `AZURE_AI_INFERENCE_ENDPOINT`, chemin du jeu de conversations, outil `track_delivery` exposé, persona injectée dans le prompt, typage strict remis au vert.

## Vérification

```bash
make test             # 37 tests, dont le rejeu des 5 conversations
make lint
make typecheck
make replay-offline   # rejeu des 5 conversations sans connexion
make replay           # démonstration sur le modèle réel (.env requis)
```

## Limites connues

Les outils métier ne sont pas encore appelés par l'agent (le routage se traduit par la catégorie de réponse). Les filtres reposent sur des mots-clés. Le texte généré n'est pas revérifié après génération. Une relance contenant un nombre quelconque peut atteindre le modèle, qui reste alors encadré par le prompt système. Détails dans le journal.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
