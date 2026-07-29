# Journal des choix de conception

> But de ce document : garder une trace **simple et compréhensible** des décisions
> prises pour remettre l'agent Velmo dans les clous. Chaque entrée suit le même
> format : **Problème → Décision → Pourquoi** (+ l'alternative écartée si utile).

---

## Méthode de travail

**Décision.** Pour chaque défaut : on écrit d'abord un **test** qui prouve le bon
comportement (il est rouge), puis on corrige jusqu'à ce qu'il passe au vert, en
relançant **toute** la suite pour ne rien casser (« test-first » + non-régression).

**Pourquoi.** Le test devient une **preuve** et un **filet** : si une correction
future re-casse un cas, un test rouge le signale immédiatement. C'est ce filet qui
a, par exemple, attrapé le jour où le garde-fou de périmètre s'est mis à refuser
« Bonjour ».

---

## Axe Mémoire — l'agent tient le contexte

### M1 — Réinjecter l'historique dans le modèle

- **Problème :** l'agent *écrivait* bien la conversation en mémoire, mais ne la
  *relisait* jamais : il envoyait une liste vide au modèle. Résultat : il oubliait
  tout au tour suivant.
- **Décision :** passer `self.memory.history()` au modèle, au lieu de `[]`.
- **Pourquoi :** sans l'historique, le modèle ne voit que le dernier message ; avec,
  il garde le fil de la conversation.

### M2 — Garder les tours les plus récents

- **Problème :** la « fenêtre » de mémoire renvoyait les tours les plus **anciens**
  (`_turns[:window]`) au lieu des plus récents.
- **Décision :** prendre la fin de la liste (`_turns[-window:]`).
- **Pourquoi :** dans une conversation, c'est le contexte **récent** qui compte le plus.

### Respecter la mémoire fournie (piège du `__len__`)

- **Problème :** l'agent ignorait la mémoire qu'on lui passait quand elle était vide,
  à cause de `memory or ConversationMemory()` : une mémoire vide est « fausse »
  (`len == 0`), donc l'agent en recréait une autre.
- **Décision :** tester explicitement `memory if memory is not None else ...`.
- **Pourquoi :** on veut savoir si une mémoire a été **fournie**, pas si elle est vide.

---

## Axe Flux — le nouveau besoin métier

### F1 — Parcours après-vente unifié

- **Problème :** retours et remboursements devaient être regroupés, mais l'intention
  `after_sales` n'existait pas dans le code → l'agent plantait.
- **Décision :** créer l'intention `Intent.AFTER_SALES`, reliée à l'outil unique
  `open_after_sales`.
- **Pourquoi :** c'est la traduction directe du nouveau besoin métier.

### F2 — Priorité métier explicite

- **Problème :** « remboursement **pour la commande** 4490 » était classé en « statut
  de commande », car le mot « commande » était rencontré avant « remboursement ».
- **Décision :** classer par **ordre de priorité** explicite (`_PRIORITY`), avec
  l'après-vente en tête.
- **Pourquoi :** une demande de remboursement est une demande d'après-vente, même si
  elle cite un numéro de commande. La priorité rend cette règle **visible** dans le code.
- **Écarté :** réordonner un dictionnaire (ordre implicite, fragile).

### Fallback explicite `Intent.UNKNOWN`

- **Problème :** quand aucun mot-clé ne correspondait, l'agent renvoyait `GREETING`
  par défaut. Du coup, impossible de distinguer un vrai « Bonjour » d'un message
  inconnu — ce qui empêchait de refuser correctement le hors-sujet.
- **Décision :** renvoyer une intention dédiée `UNKNOWN` quand rien n'est reconnu.
- **Pourquoi :** un « fourre-tout » déguisé en vraie valeur cache de l'information ;
  un `UNKNOWN` explicite permet de décider quoi refuser.

---

## Axe Rôle — garde-fous

### R3 (entrée) — Détecter l'abus dans la phrase

- **Problème :** le filtre d'insultes ne se déclenchait que si le message **entier**
  valait exactement l'insulte (`==`).
- **Décision :** détecter le terme **présent dans** la phrase (`in`).
- **Pourquoi :** « tu es un imbécile » doit être bloqué, pas seulement « imbécile » seul.

### R3 (sortie) — Refuser proprement, sans crash

- **Problème :** une entrée abusive levait une exception **non rattrapée** →
  l'application plantait.
- **Décision :** dans `handle()`, rattraper `GuardrailError` et renvoyer une réponse
  de **rejet** (`category="rejet"`, `within_scope=False`).
- **Pourquoi :** un refus doit être **propre** (un message poli), pas un crash. Le
  contrat de `handle()` devient : toujours renvoyer une réponse, jamais lever.

### Sorties contraintes (`Literal`)

- **Problème :** la catégorie de la réponse acceptait **n'importe quelle** chaîne
  (même « banane »).
- **Décision :** contraindre `category` à une **liste fermée** de valeurs valides
  (`Literal[...]`).
- **Pourquoi :** une sortie structurée doit être prévisible ; toute valeur inattendue
  est refusée par Pydantic.

### R1 — Borner le périmètre de rôle

- **Problème :** le contrôle de périmètre existait mais n'était **jamais appelé**, et
  `within_scope` était toujours « vrai ».
- **Décision :** brancher `is_in_scope` dans `handle()` ; si le message n'est ni un
  sujet support ni une intention reconnue, **court-circuiter** avec un refus
  (`category="refusal"`) **sans appeler le modèle**.
- **Pourquoi :** principe « fail fast » — on filtre tôt, on ne gaspille pas un appel
  modèle et on évite tout dérapage. On distingue deux refus : `refusal` (hors sujet)
  et `rejet` (entrée abusive).

---

## Limite connue (assumée)

### Le garde-fou de périmètre peut refuser un suivi conversationnel

- **Constat (vu au rejeu) :** dans `ctx-oubli-1`, le tour *« Et la précédente, la
  4490, où en est-elle ? »* est **refusé** : la phrase ne contient aucun mot-clé de
  périmètre, donc elle est jugée hors-sujet — alors qu'elle prolonge une conversation
  sur des commandes.
- **Pourquoi on l'accepte pour l'instant :** le contrôle est **déterministe** (mots-clés),
  donc prévisible et sans risque de dérapage ni d'appel modèle inutile. La mémoire,
  elle, reste correcte (la 4521 du 1er tour est bien conservée).
- **Piste d'amélioration future :** tenir compte du **contexte** (par ex. autoriser un
  suivi quand une commande est déjà active dans la conversation), ou compléter le
  filtre mots-clés par une détection d'intention plus fine.

---

## Annexe — corrections d'amorçage

Deux blocages empêchaient simplement de **lancer** l'agent (indépendants des défauts
ci-dessus) :

- **Variable d'environnement** : le code lisait `AZURE_AI_ENDPOINT` alors que la
  convention (et le `.env`) est `AZURE_AI_INFERENCE_ENDPOINT`.
- **Prompt système** : le gabarit attendait `{persona}` mais l'appel fournissait
  `role=...`. Aligné sur `persona`.
