# Journal des choix — Velmo

Ce document explique pourquoi j'ai changé ce que j'ai changé. L'idée, c'est que quelqu'un qui relit ma PR comprenne mon raisonnement sans avoir à refaire tout le diagnostic depuis le début.

Avant de toucher au code, j'ai lu les conversations problématiques comme si j'étais un client. Ça m'a permis de classer les défauts en trois familles : la **mémoire** (l'agent oublie), le **rôle** (l'agent répond à des choses qu'il ne devrait pas), et le **flux** (le besoin métier a changé). Le reste, ce sont des petits bugs « support » que j'ai croisés en faisant tourner les tests.

Je le note ici parce que c'est ce qui a guidé tout l'ordre de mon travail : diagnostiquer d'abord, corriger ensuite, vérifier à la fin.

---

## 1. Le flux : regrouper retour et remboursement (Q3)

**Ce que je voyais :** le chef de projet voulait que « retour » et « remboursement » deviennent un seul parcours après-vente. En ouvrant `flow.py`, j'ai trouvé un truc bizarre : les mots-clés pointaient déjà vers `"after_sales"`, mais l'enum `Intent` ne connaissait que `RETURN` et `REFUND`. Du coup `Intent("after_sales")` plantait avec une `ValueError`.

**Ce que j'ai compris :** la migration avait été commencée mais pas finie. C'est ça qui cassait, pas un oubli de ma part.

**Ce que j'ai fait :**
- Dans `flow.py`, j'ai remplacé les deux membres `RETURN` et `REFUND` par un seul, `AFTER_SALES = "after_sales"`, et j'ai aligné la table `_ROUTES` (une seule ligne vers `open_after_sales`).
- Dans `agent.py`, la table `_CATEGORY_BY_INTENT` utilisait encore `RETURN`/`REFUND`. Comme ces membres n'existaient plus, le programme plantait dès le chargement (`AttributeError`). Je l'ai mise à jour aussi.

**Pourquoi ce choix :** le besoin métier ne demande plus deux catégories, donc une seule intention suffit. Et comme les mots-clés visaient déjà `after_sales`, je n'avais qu'à finir proprement ce qui avait été commencé. J'ai fait attention à ne toucher qu'aux deux endroits concernés, pour ne pas casser `greeting`, `order_status` ou `delivery`.

---

## 2. La mémoire : garder le contexte récent (Q4)

**Ce que je voyais :** dans `ctx-oubli-1`, le client donne sa commande 4521 au début, et l'agent l'a oublié quelques messages plus tard.

**Ce que j'ai compris :** il y avait en fait deux problèmes, pas un.
- Dans `memory.py`, `history()` faisait `self._turns[: self.window]`, donc gardait les tours du **début** (les plus vieux) et jetait les récents quand la fenêtre était pleine.
- Et même si la mémoire avait été bonne, `agent.py` appelait le modèle avec un historique **vide** (`[]`). Donc le modèle ne voyait jamais le passé de toute façon.

**Ce que j'ai fait :**
- `memory.py` : `[: self.window]` → `[-self.window :]`. Le petit `-` change tout : on prend depuis la fin de la liste, donc les tours récents.
- `agent.py` : j'ai remplacé `[]` par `self.memory.history()` dans l'appel au modèle.

**Pourquoi ce choix :** dans une conversation, ce que le client vient de dire compte plus que ce qu'il a dit il y a dix messages. Et corriger la mémoire ne sert à rien si on ne l'envoie pas au modèle — il fallait vraiment les deux. J'ai vérifié l'ordre dans `handle()` : je lis l'historique **avant** d'enregistrer le message courant, donc au 2e tour le modèle reçoit bien le 1er.

---

## 3. Les garde-fous : garder l'agent dans son rôle (Q5)

J'ai posé trois barrières, à trois moments différents du trajet d'un message.

**Entrée (`guardrails.py`).** La validation refusait une insulte seulement si le message était **exactement** le mot interdit (`term == lowered`). Une insulte au milieu d'une phrase passait. Je suis passé à `term in lowered` : maintenant le mot est détecté même dans une phrase.

**Sortie (`guardrails.py`).** Le champ `category` était un `str` libre, donc n'importe quelle valeur passait, même « banane ». Je l'ai contraint avec `Literal[...]` sur les cinq catégories connues. Comme ça la réponse ne peut pas inventer une catégorie ; si elle essaie, Pydantic lève une erreur de validation.

**Périmètre (`scope.py` + `agent.py`).** Il y avait deux soucis. D'abord `is_in_scope` bouclait sur `lowered.split()`, c'est-à-dire les mots du message lui-même — donc un mot est toujours dans sa propre phrase, et ça renvoyait toujours `True` (même une recette de cookies était jugée « dans le périmètre »). Je compare maintenant à `IN_SCOPE_TOPICS`, la vraie liste autorisée. Ensuite, dans `agent.py`, ce contrôle était importé mais **jamais appelé**, et `within_scope=True` était écrit en dur. J'ai ajouté l'appel : si le message est hors périmètre, je renvoie un refus propre (`category="refusal"`, `within_scope=False`) sans même appeler le modèle.

**Pourquoi ces choix :** un agent, ce n'est pas juste un modèle qui répond — il doit rester dans sa mission. Corriger `scope.py` sans appeler la fonction dans l'agent n'aurait servi à rien, c'est pour ça que les deux vont ensemble. Et refuser **avant** d'appeler le modèle, c'est plus sûr et ça évite de payer un appel API pour rien.

---

## 4. Les bugs « support » trouvés en chemin (Q6)

Ceux-là, je ne les cherchais pas : ce sont les tests rouges qui me les ont montrés.

**`prompts.py` — le bug qui bloquait tout.** Le template disait `{persona}`, mais le code appelait `.format(role=persona)`. Mauvais nom → `KeyError: 'persona'`, qui faisait planter l'agent avant même d'arriver à la mémoire. C'est pour ça que mon test mémoire restait rouge alors que ma correction Q4 était bonne. J'ai aligné le nom : `.format(persona=persona)`. Je l'ai corrigé en premier parce qu'il masquait les autres.

**`config.py`.** Le code lisait la variable d'environnement `AZURE_AI_ENDPOINT`, mais le bon nom (celui d'Azure et de mes tests) est `AZURE_AI_INFERENCE_ENDPOINT`. Corrigé.

**`tools.py`.** L'outil `track_delivery` n'était jamais exposé à l'agent. En lisant le décorateur `register`, j'ai compris pourquoi : `if not fn.__doc__: return fn` — un outil sans docstring n'est pas enregistré. Les deux autres outils avaient leur docstring, pas celui-là. J'en ai ajouté une. Ce n'est pas qu'un détail de forme : pour un agent, la docstring est la description que le modèle lit pour décider quand appeler l'outil.

**`regression.py`.** Le module de rejeu cherchait `conversations.json`, mais le fichier fourni s'appelle `conversations_problematiques.json`. Tant que ce n'était pas corrigé, le rejeu plantait avec `FileNotFoundError`. J'ai mis le bon nom.

---

## 5. Comment j'ai vérifié que je n'avais rien cassé

Pour moi la non-régression, ce n'est pas juste vérifier le cas que je viens de corriger — c'est vérifier que les autres parcours marchent toujours.

J'ai rejoué les cinq conversations fournies (`ctx-oubli-1`, `perimetre-1`, `perimetre-2`, `entree-abusive-1`, `apres-vente-1`), qui couvrent les quatre familles. Et j'ai relancé toute la suite :

```
uv run pytest
```

Résultat : **21 tests passent**. C'est ma preuve. Au début du projet j'étais à 11 verts / 10 rouges, et j'ai vu les rouges tomber un par un au fur et à mesure des corrections.

---

## Ce que je retiens

Ce projet m'a fait comprendre qu'un agent IA, ce n'est pas seulement le modèle. C'est une chaîne complète : garde-fous, périmètre, flux, mémoire, modèle, puis validation de la sortie. Si un seul maillon est mal branché — comme `is_in_scope` qui n'était jamais appelé — l'agent peut oublier, déraper ou router au mauvais endroit, même si le reste est correct.
