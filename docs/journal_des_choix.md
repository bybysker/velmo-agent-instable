# Journal des choix — Velmo Agent

> Document de traçabilité des décisions prises lors de la remise en production de l'agent Velmo.
> Chaque entrée décrit le problème observé, la cause racine, la décision prise et son impact.

---

## 2026-07-03 — Session de stabilisation

### [MÉMOIRE-1] Fenêtre glissante retournait les anciens tours

**Fichier** : `src/velmo/memory.py` — méthode `history()`

**Problème observé** : L'agent oubliait le contexte 2 messages plus tôt.

**Cause racine** : `self._turns[: self.window]` prenait les `N` **premiers** tours
(les plus anciens), pas les plus récents. Après 8 tours, les nouveaux messages
n'étaient plus jamais transmis au LLM.

**Décision** : Remplacer par `self._turns[-self.window :]` pour garder les `N` derniers.

**Impact** : L'agent se souvient maintenant des derniers `window` tours de la conversation.

---

### [MÉMOIRE-2] Historique non transmis au LLM

**Fichier** : `src/velmo/agent.py` — méthode `handle()`

**Problème observé** : Même avec une mémoire correctement remplie, le LLM ne recevait pas l'historique.

**Cause racine** : L'appel était `self.llm.complete(system, [], user_message)` — la liste `[]`
passée en dur écrasait `self.memory.history()`.

**Décision** : Remplacer `[]` par `self.memory.history()`.

**Impact** : Le LLM reçoit maintenant le contexte complet des tours précédents.

---

### [PÉRIMÈTRE-1] `is_in_scope()` jamais appelée

**Fichier** : `src/velmo/agent.py` — méthode `handle()`

**Problème observé** : L'agent répondait à des questions hors support (recettes, finances…).

**Cause racine** : La fonction `is_in_scope()` était définie dans `scope.py` mais
n'était jamais appelée dans `agent.py`. La vérification était donc inexistante.

**Décision** : Ajouter l'appel `is_in_scope()` avant la classification d'intention.
Si hors périmètre → retourner un `AgentReply` avec `within_scope=False`, `category="refusal"`.

**Impact** : L'agent refuse maintenant proprement les demandes hors périmètre.

---

### [PÉRIMÈTRE-2] Logique `is_in_scope()` défaillante (toujours True)

**Fichier** : `src/velmo/scope.py` — fonction `is_in_scope()`

**Problème observé** : La fonction retournait `True` pour n'importe quel texte.

**Cause racine** : `any(topic in lowered for topic in lowered.split())` comparait les mots
du texte **contre eux-mêmes**. Un mot est toujours une sous-chaîne de lui-même, donc
`any(...)` était toujours `True`.

**Décision** : Remplacer `lowered.split()` par `IN_SCOPE_TOPICS` (l'ensemble des sujets autorisés).

**Impact** : La vérification de périmètre est maintenant correcte et discriminante.

---

### [FLUX-1] Unification du parcours après-vente

**Fichier** : `src/velmo/flow.py` — classe `Intent`

**Problème observé** : Le nouveau besoin métier regroupe retours et remboursements
dans un seul parcours "après-vente". Les tests attendaient `Intent.AFTER_SALES`.

**Cause racine** : Le code avait encore `Intent.RETURN` et `Intent.REFUND` séparés
(ancienne taxonomie). La nouvelle enum n'avait pas été implémentée.

**Décision** : Supprimer `RETURN` et `REFUND`, introduire `AFTER_SALES`. Mettre à jour
`_KEYWORDS`, `_ROUTES` et `_CATEGORY_BY_INTENT` dans `agent.py`.

**Impact** : Les demandes de retour ET de remboursement sont maintenant routées vers
`open_after_sales` via un seul et même parcours.

---

### [GARDE-FOU-1] Détection des termes abusifs uniquement sur message exact

**Fichier** : `src/velmo/guardrails.py` — fonction `validate_input()`

**Problème observé** : Un message comme "tu es vraiment un imbécile" n'était pas détecté.

**Cause racine** : La comparaison était `term == lowered` (égalité stricte). Seul un
message composé **uniquement** du terme (ex. : `"imbécile"` seul) était refusé.

**Décision** : Remplacer `==` par `in` pour détecter le terme **dans** une phrase.

**Impact** : Les insultes dans un contexte de phrase sont maintenant correctement bloquées.

---

### [GARDE-FOU-2] Catégorie de réponse non validée

**Fichier** : `src/velmo/guardrails.py` — classe `AgentReply`

**Problème observé** : `AgentReply(category="banane")` était accepté sans erreur.

**Cause racine** : `category: str` acceptait n'importe quelle valeur.

**Décision** : Remplacer par `category: Literal["greeting", "order_status", "delivery", "after_sales", "refusal"]`.
Pydantic lève alors une `ValidationError` pour toute valeur inconnue.

**Impact** : Le schéma de sortie est maintenant strictement typé et validé.

---

### [PROMPT-1] Bug de formatage du prompt système

**Fichier** : `src/velmo/prompts.py` — fonction `build_system_prompt()`

**Problème observé** : La persona n'apparaissait pas dans le prompt (KeyError silencieux).

**Cause racine** : `SYSTEM_PROMPT.format(role=persona)` utilisait le mot-clé `role`
mais le template contient `{persona}`. Python ignorait silencieusement la valeur.

**Décision** : Corriger en `SYSTEM_PROMPT.format(persona=persona)`.

**Impact** : La persona est maintenant correctement injectée dans le prompt système.

---

### [OUTIL-1] `track_delivery` non enregistré faute de docstring

**Fichier** : `src/velmo/tools.py` — fonction `track_delivery()`

**Problème observé** : `track_delivery` n'apparaissait pas dans `available_tools()`.

**Cause racine** : Le décorateur `@register` n'enregistre une fonction que si elle
possède une docstring (`if not fn.__doc__: return fn`). La docstring manquait.

**Décision** : Ajouter une docstring explicite à `track_delivery`.

**Impact** : Les trois outils métier (lookup_order, track_delivery, open_after_sales)
sont maintenant tous exposés au modèle.

---

### [CONFIG-1] Mauvais nom de variable d'environnement

**Fichier** : `src/velmo/config.py` — fonction `load_settings()`

**Problème observé** : `KeyError: 'AZURE_AI_ENDPOINT'` au démarrage.

**Cause racine** : La variable était lue depuis `AZURE_AI_ENDPOINT` mais la convention
du SDK Azure et `.env.example` utilisent `AZURE_AI_INFERENCE_ENDPOINT`.

**Décision** : Aligner sur `AZURE_AI_INFERENCE_ENDPOINT`.

**Impact** : La configuration se charge correctement depuis l'environnement.

---

### [RÉGRESSION-1] Mauvais nom de fichier de données

**Fichier** : `src/velmo/regression.py` — fonction `load_problem_conversations()`

**Problème observé** : `FileNotFoundError` au lancement des tests de régression.

**Cause racine** : Le code cherchait `conversations.json` mais le fichier réel
s'appelle `conversations_problematiques.json`.

**Décision** : Corriger le nom du fichier dans le chemin par défaut.

**Impact** : Les conversations problématiques se chargent correctement pour les tests.
