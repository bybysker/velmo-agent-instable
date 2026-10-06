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

---

## 2026-10-05 — Rejeu des conversations et compléments

Constat de départ : les 21 tests unitaires passaient, mais le **rejeu de bout en bout** des cinq
conversations fournies révélait encore deux échecs (`ctx-oubli-1` au tour 3, `apres-vente-1`).
Les tests vérifiaient les composants isolément, pas le comportement attendu par conversation.

### [RÉGRESSION-2] Rejeu réel des conversations fournies

**Fichiers** : `src/velmo/regression.py` (`replay()`), `tests/test_regression.py`

**Problème observé** : `regression.py` chargeait le fichier sans jamais rejouer les conversations.

**Décision** : `replay(case, agent)` renvoie chaque message client à l'agent et collecte un résultat
par message (`AgentReply` ou `GuardrailError`). Les tours `assistant` du jeu de données ne sont pas
réinjectés : ils proviennent de l'ancienne version et l'agent rejoué produit les siens.
Chaque cas reçoit un contrôle explicite, et un test échoue si un cas est ajouté sans contrôle.

**Alternative écartée** : réinjecter les réponses `assistant` historiques en mémoire, ce qui aurait
testé la mémoire avec des réponses que l'agent corrigé ne produit plus.

---

### [FLUX-2] Priorité explicite entre intentions

**Fichier** : `src/velmo/flow.py` — `_KEYWORDS_BY_PRIORITY`

**Problème observé** : « Je veux un remboursement pour la commande 4490 » était classée `order_status`.

**Cause racine** : la priorité dépendait de l'ordre d'insertion du dictionnaire `_KEYWORDS`, où
« commande » précède « remboursement ». De même, « Bonjour, ma commande… » restait `greeting`.

**Décision** : liste ordonnée `(Intent, mots-clés)` du plus spécifique au plus générique :
`after_sales › delivery › order_status › greeting`. La racine « rembours » couvre
remboursement / rembourser / remboursé.

**Impact** : `apres-vente-1` est bien routée vers le parcours après-vente unifié.

---

### [MÉMOIRE-3] Relances contextuelles refusées par le filtre de périmètre

**Fichiers** : `src/velmo/scope.py` (`is_follow_up()`), `src/velmo/agent.py`

**Problème observé** : « Et la précédente, la 4490, où en est-elle ? » était refusée hors périmètre.

**Cause racine** : le correctif [PÉRIMÈTRE-1] filtre sur des mots-clés, sans contexte. Une relance
naturelle n'en contient pas ; refusée, elle n'entre pas non plus en mémoire.

**Décision** : le périmètre accepte un message si `is_in_scope()` **ou** `is_follow_up(message, historique)`.
La mémoire est lue *avant* le contrôle de périmètre.
Une relance est acceptée si **deux conditions** sont réunies :
1. le message cite un numéro d'au moins 4 chiffres (`\d{4,}`), signal d'une demande sur une commande ;
2. l'historique contient au moins un message relevant du périmètre (`is_in_scope`).

**Alternatives écartées** :
- *Historique seul* (toute relance acceptée dès qu'on a parlé de commande) : « Et une recette de
  cookies ? » passait. Trop permissif, cela rouvre les sorties de rôle.
- *Marqueurs de relance* (« et », « elle », « la précédente ») : trop fréquents dans n'importe
  quelle phrase pour être discriminants.

**Piège évité** : une première version parcourait l'historique avec `history.pop()`. Or l'agent
transmet *cette même liste* au modèle juste après : la vérification amputait l'historique envoyé
au LLM et recréait le défaut de mémoire. La fonction lit désormais sans modifier, et un test
(`test_follow_up_does_not_modify_history`) le garantit.

**Garde-fou associé** : les tests imposent qu'une relance hors sujet (« Et une recette de cookies ? »)
reste refusée même en plein contexte support, et qu'aucune relance ne soit acceptée sans historique.

**Limite assumée** : une relance sans numéro (« Et l'autre, elle arrive quand ? ») est refusée ;
le client est invité à préciser. On préfère un refus prudent à une sortie de rôle.

---

### [PÉRIMÈTRE-3] Mots-clés de périmètre en racines

**Fichier** : `src/velmo/scope.py` — `IN_SCOPE_TOPICS`

**Décision** : la recherche se faisant en sous-chaîne, les formes plurielles étaient redondantes
et « remboursé », « livré » ou « suivi » n'étaient pas reconnus. Passage à des racines
(`commande`, `rembours`, `factur`, `livré`, `suivi`…). Retrait de `after_sales`, identifiant
interne qu'un client n'écrit pas.

---

### [GARDE-FOU-3] Messages vides et démesurés

**Fichier** : `src/velmo/guardrails.py` — `validate_input()`

**Décision** : rejet d'un message vide (ou composé d'espaces) et d'un message de plus de
`MAX_INPUT_CHARS = 1000` caractères, longueur qui n'est plus celle d'une demande de support
et qui favorise les injections de consignes.

---

### [GARDE-FOU-4] Refus propre dans le chat

**Fichier** : `src/velmo/chat.py`

**Problème observé** : une entrée abusive faisait planter la session (`GuardrailError` non rattrapée).

**Décision** : l'agent continue de **lever** `GuardrailError` (le rejet reste un signal distinct d'un
refus de périmètre, testable) ; c'est l'interface qui la rattrape et affiche
`GUARDRAIL_REFUSAL_MESSAGE`. Le message de refus ne répète pas le terme bloqué.

---

### [GARDE-FOU-5] Contraintes de sortie dans le prompt système

**Fichier** : `src/velmo/prompts.py`

**Décision** : ajout de règles impératives : aucun conseil financier, juridique, médical ou
personnel ; aucune invention de statut, délai ou montant ; résistance aux demandes de changement
de rôle ; usage de l'historique pour retrouver les numéros de commande cités.

---

### [DÉMO-1] Commande de démonstration et typage

**Fichiers** : `src/velmo/regression.py` (`main()`), `Makefile`, `src/velmo/agent.py`, `src/velmo/llm.py`

**Décision** : `make replay` rejoue les cinq conversations fournies sur le modèle réel, pour la
démonstration ; `make replay-offline` fait de même avec un modèle factice qui affiche le nombre de
messages d'historique transmis, ce qui rend la tenue du contexte visible sans connexion Azure.
Le typage strict (`make typecheck`) est remis au vert ; en particulier, la table
intention → catégorie est typée `AllowedCategory`, si bien qu'une catégorie inconnue est
détectée dès l'analyse statique et plus seulement à l'exécution.

---

## Limites connues (hors périmètre de cette PR)

- **Outils non invoqués** : l'agent classe l'intention mais n'appelle jamais `route()` ni les outils
  de `tools.py`. Le routage se traduit aujourd'hui par la catégorie de réponse ; brancher le
  *tool calling* du modèle est un chantier distinct.
- **Filtres par mots-clés** : la détection en sous-chaîne peut produire des faux positifs
  (« idiot » dans « idiotie ») et se contourne par fautes ou séparateurs. Un classifieur
  (LLM ou modèle dédié) serait plus robuste, au prix de latence et de coût.
- **Contraintes de sortie déclaratives** : le texte produit par le modèle n'est pas revérifié
  après génération ; seule la catégorie est typée.
- **Relance avec un nombre quelconque** : après une question de commande, « Quel placement pour
  10000 euros ? » remplit les deux conditions de `is_follow_up` et atteint le modèle. C'est alors
  le prompt système (aucun conseil financier) qui doit refuser : défense en profondeur, pas
  garantie. Restreindre au format réel des numéros de commande Velmo fermerait cette brèche.
- **Catégorie d'une relance** : « Et la précédente, la 4490 ? » est acceptée mais classée
  `greeting`, faute de mot-clé d'intention ; hériter de l'intention du tour précédent serait plus juste.
