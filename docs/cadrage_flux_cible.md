# Cadrage — Adaptation du flux au nouveau besoin

**Étape 2 du brief — Cadrer l'adaptation du flux**

> Objectif (énoncé) : *définir comment le flux de l'agent doit être adapté au
> nouveau besoin métier.*
> Livrables : (A) flux cible + points d'écart avec l'existant ; (B) plan de
> vérification de non-régression sur les cas fournis.
> **Statut : à valider.**
>
> **Format.** Tableaux et schémas sont rendus en **ASCII** (tracé `+ - | > v`),
> lisibles tels quels en terminal, en diff Git ou dans un éditeur sans rendu
> Markdown. Les mêmes objets existent en version **Mermaid** (archi, classes,
> séquence) dans [schemas_mermaid.md](schemas_mermaid.md).

---

## Clés de lecture (vocabulaire)

Trois notions structurent ce document. En clair :

```text
+------------------+------------------------------------------------------------+------------------------+
| Terme            | Définition simple                                          | Image                  |
+==================+============================================================+========================+
| Flux             | le TRAJET qu'un message parcourt dans l'agent, étape par   | l'itinéraire           |
|                  | étape (entrée > garde-fous > classification > mémoire >    |                        |
|                  | LLM > réponse)                                             |                        |
+------------------+------------------------------------------------------------+------------------------+
| Flux cible       | ce trajet tel qu'il DEVRAIT être une fois corrigé          | la DESTINATION sur le  |
|                  |                                                            | GPS                    |
+------------------+------------------------------------------------------------+------------------------+
| Flux existant    | ce trajet tel qu'il EST aujourd'hui (bugué)                | la POSITION actuelle   |
+------------------+------------------------------------------------------------+------------------------+
| Point d'écart    | la DIFFÉRENCE entre cible et existant = le TRAVAIL à faire | le VIRAGE à prendre    |
+------------------+------------------------------------------------------------+------------------------+
| Régression       | une modif qui CASSE ce qui marchait avant                  | -                      |
+------------------+------------------------------------------------------------+------------------------+
| Non-régression   | un CONTRÔLE AUTOMATIQUE rejoué après chaque modif pour     | le BILAN MÉDICAL       |
|                  | vérifier que le comportement attendu TIENT TOUJOURS        | refait à l'identique   |
+------------------+------------------------------------------------------------+------------------------+
```

> **Logique d'ensemble.** On décrit d'abord **où on veut aller** (§A, flux cible),
> puis **ce qui nous en sépare** (§B, écarts), puis **comment prouver qu'on y est
> arrivé sans rien casser** (§C, non-régression). On trace l'itinéraire avant de
> conduire.

---

## A. Flux cible

> **En clair :** voici comment l'agent **devrait** traiter un message, étape par
> étape, une fois remis dans les clous.

### A.1 Principe directeur — « fail fast » (filtrer tôt, dépenser tard)

Une entrée qu'on va refuser ne doit ni consommer un appel modèle, ni risquer un
dérapage. Les contrôles déterministes (garde-fous) passent **avant** le LLM ; le
LLM est la **dernière** étape, réservée aux entrées légitimes et dans le
périmètre.

```text
    coût / risque
        ^
        |                                                        #### LLM
        |                                          ### routage
        |                            ## classification
        |              # périmètre
        |   . garde-fou
        +-------------------------------------------------------------> étapes
            (déterministe, gratuit)                    (non déterministe, payant)

    On refuse À GAUCHE ce qu'on ne veut pas payer À DROITE.
```

### A.2 Étapes ordonnées (avec court-circuits)

Un **court-circuit** = on s'arrête là et on répond tout de suite, sans aller plus
loin dans le flux.

```text
+-------+------------------------------------+------------------------------------------------+--------------------------+
| Ordre | Étape                              | Rôle                                           | Court-circuit ?          |
+=======+====================================+================================================+==========================+
| 1     | Garde-fou entrée (validate_input)  | Rejette les entrées abusives                   | OUI -> refus propre,     |
|       |                                    |                                                | STOP                     |
+-------+------------------------------------+------------------------------------------------+--------------------------+
| 2     | Contrôle de périmètre              | Rejette le hors-sujet, de façon déterministe   | OUI -> refus poli, STOP  |
|       | (is_in_scope)                      |                                                |                          |
+-------+------------------------------------+------------------------------------------------+--------------------------+
| 3     | Classification d'intention         | Détermine l'intention métier (dont after_sales | non                      |
|       | (classify)                         | unifié)                                        |                          |
+-------+------------------------------------+------------------------------------------------+--------------------------+
| 4     | Routage (route + tools)            | Sélectionne l'outil métier adéquat             | non                      |
+-------+------------------------------------+------------------------------------------------+--------------------------+
| 5     | Mémoire (history)                  | Réinjecte les tours précédents dans le prompt  | non                      |
+-------+------------------------------------+------------------------------------------------+--------------------------+
| 6     | Appel LLM (complete)               | Génère la réponse, avec contexte + outils      | non                      |
+-------+------------------------------------+------------------------------------------------+--------------------------+
| 7     | Réponse (AgentReply)               | message + category + within_scope COHÉRENTS    | -                        |
+-------+------------------------------------+------------------------------------------------+--------------------------+
```

### A.3 Sémantique cible des réponses

> **Pourquoi cette section :** « refuser proprement » suppose de décider à quoi
> ressemble un refus. On fixe donc, pour chaque type d'entrée, ce que doivent
> valoir les champs de la réponse.

```text
+------------------------+---------------+--------------+-------------------------+----------------------------------+
| Type d'entrée          | Court-circuit | within_scope | category                | message                          |
+========================+===============+==============+=========================+==================================+
| Abusive                | étape 1       | False        | rejet                   | refus garde-fou poli             |
+------------------------+---------------+--------------+-------------------------+----------------------------------+
| Hors-périmètre         | étape 2       | False        | hors_perimetre          | refus standard Velmo             |
+------------------------+---------------+--------------+-------------------------+----------------------------------+
| Salutation             | jusqu'au LLM  | True         | greeting                | réponse LLM                      |
+------------------------+---------------+--------------+-------------------------+----------------------------------+
| Commande / livraison   | jusqu'au LLM  | True         | order_status / delivery | réponse LLM (+ outil)            |
+------------------------+---------------+--------------+-------------------------+----------------------------------+
| Retour / remboursement | jusqu'au LLM  | True         | after_sales             | réponse LLM (+ open_after_sales) |
+------------------------+---------------+--------------+-------------------------+----------------------------------+
```

### A.4 Nouveau besoin métier — parcours après-vente **unifié**

Retour **et** remboursement convergent vers **une seule** intention `after_sales`
et **un seul** outil `open_after_sales`. Concrètement, l'enum doit exposer un
membre `AFTER_SALES`, vers lequel pointent les mots-clés *retour, renvoyer,
remboursement, rembourser*.

```text
   AVANT (deux parcours)                    CIBLE (un seul parcours)

   "retour"      -> Intent.RETURN           "retour"        \
                       |                    "renvoyer"       \
                       v                                      >-- Intent.AFTER_SALES
                  outil retour              "remboursement"  /            |
                                            "rembourser"    /             v
   "remboursement" -> Intent.REFUND                            open_after_sales()
                       |                                                  |
                       v                                                  v
                  outil remboursement                        category = "after_sales"
```

### A.5 Schéma cible (ASCII)

```text
                              +--------------+
                              |    CLIENT    |
                              +------+-------+
                                     | message
                                     v
        +--------------------------------------------------------+
        |  chat.py - boucle CLI                                  |
        |  capte GuardrailError -> refus propre                  |
        +----------------------------+---------------------------+
                                     |
                                     v
        < 1. validate_input : entrée abusive ? >--- oui --->+-----------------------+
                                     |                      | AgentReply "rejet"    |
                                     | non                  | within_scope = False  |
                                     |                      +-----------+-----------+
                                     v                                  |
        < 2. is_in_scope : dans le périmètre ? >--- non --->+-----------------------+
                                     |                      | AgentReply            |
                                     | oui                  | "hors_perimetre"      |
                                     |                      | within_scope = False  |
                                     |                      +-----------+-----------+
                                     v                                  |
        +--------------------------------------------------------+      |
        |  3. classify -> Intent   (AFTER_SALES unifié)          |      |
        +----------------------------+---------------------------+      |
                                     v                                  |
        +--------------------------------------------------------+      |
        |  4. route -> outil                                     |      |
        |     lookup_order / track_delivery / open_after_sales   |      |
        +----------------------------+---------------------------+      |
                                     v                                  |
        +--------------------------------------------------------+      |
        |  5. memory.history() -> derniers tours  _turns[-w:]    |      |
        +----------------------------+---------------------------+      |
                                     v                                  |
        +--------------------------------------------------------+      |
        |  6. llm.complete(system, history, user)                |      |
        +----------------------------+---------------------------+      |
                                     v                                  |
        +--------------------------------------------------------+      |
        |  record("user", ...) / record("assistant", ...)        |      |
        +----------------------------+---------------------------+      |
                                     v                                  |
        +--------------------------------------------------------+      |
        |  7. AgentReply : category + within_scope cohérents     |      |
        +----------------------------+---------------------------+      |
                                     |                                  |
                                     +----------------------------------+
                                     |
                                     v
                              +--------------+
                              |    CLIENT    |
                              +--------------+
```

---

## B. Points d'écart avec l'existant

> **En clair :** la liste des **différences** entre le flux cible (§A) et l'agent
> d'aujourd'hui. Chaque ligne est un **virage à prendre** — donc une tâche de la
> future phase de correction. La colonne « Réf. » renvoie aux défauts numérotés
> de la note de diagnostic.
>
> *Exemple de lecture (1ʳᵉ ligne) : aujourd'hui le garde-fou abusif fait planter
> l'app ; la cible veut un refus poli ; l'écart à combler est « rattraper
> l'exception ».*

```text
+--------------------------------+----------------------------------+------------------------------------------+--------+
| Étape cible                    | État actuel (existant)           | Écart à combler (le travail)             | Réf.   |
+================================+==================================+==========================================+========+
| 1. Garde-fou entrée -> refus   | détecte l'abus mais CRASHE       | rattraper GuardrailError et renvoyer un  | R3     |
| propre                         | (exception non rattrapée)        | AgentReply de refus                      |        |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 2. Contrôle de périmètre       | is_in_scope JAMAIS APPELÉ ;      | brancher le contrôle dans handle, court- | R1     |
| déterministe                   | within_scope codé en dur         | circuiter si hors-scope                  |        |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 2. (logique du contrôle)       | is_in_scope renvoyait toujours   | boucler sur IN_SCOPE_TOPICS (corrigé)    | R2 OK  |
|                                | True                             |                                          |        |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 3. Classification (après-vente | Intent("after_sales") CRASHE     | ajouter Intent.AFTER_SALES               | F1     |
| unifié)                        | (membre manquant)                |                                          |        |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 3. (robustesse mots-clés)      | "commande" masque                | prioriser / désambiguïser les mots-clés  | F2     |
|                                | "remboursement"                  |                                          |        |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 4. Routage vers outil          | route() / tools JAMAIS INVOQUÉS  | câbler le routage dans handle            | F3     |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 5. Mémoire réinjectée          | [] passé au LLM                  | passer self.memory.history()             | M1     |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 5. (fenêtre récente)           | _turns[:window] (anciens)        | _turns[-window:] (récents)               | M2     |
+--------------------------------+----------------------------------+------------------------------------------+--------+
| 7. Réponse cohérente           | within_scope=True en dur         | refléter le vrai résultat                | R1     |
+--------------------------------+----------------------------------+------------------------------------------+--------+
```

---

## C. Plan de vérification de non-régression

> **En clair :** on définit, **pour chacun des 5 cas fournis**, un **contrôle
> automatique** qui prouve que l'agent se comporte comme attendu. On les écrit
> **avant** de corriger : ils sont d'abord **rouges** (l'agent dérape), on
> corrige, on s'arrête quand ils passent **verts** — sans casser les autres.
> C'est le **filet de sécurité** de la phase de correction.

```text
   écrire les tests      corriger le code       rejouer les tests
   (rouges)         ->   (un écart §B)     ->   (verts ?)  --- non ---+
        ^                                            |               |
        |                                            | oui           |
        +--------------------------------------------|---------------+
                                                     v
                                              écart suivant
```

### C.1 Pré-requis — réparer le harnais

`regression.py` charge `conversations.json` (inexistant) au lieu de
`conversations_problematiques.json`, et ne fait que charger sans rejouer.
**À corriger** : bon nom de fichier + une fonction qui **rejoue** chaque
conversation dans l'agent et compare au comportement attendu.

### C.2 Cas fournis → vérifications

Pour chaque cas, on **traduit** le champ `attendu` du JSON en une assertion
**déterministe** (qui ne dépend pas du texte exact généré par le LLM).

```text
+-------------------+--------------------------+--------------------------------+--------------------------------------------------+
| Cas               | Entrée(s)                | Attendu (énoncé)               | Vérification de non-régression                   |
+===================+==========================+================================+==================================================+
| ctx-oubli-1       | 3 tours : 4521 > 4490 >  | se souvient de la 4521 du tour | après les 3 tours, memory.history() contient le  |
|                   | 4521                     | 1                              | 1er tour ET l'historique réinjecté au LLM est    |
|                   |                          |                                | NON VIDE (mémoire effectivement transmise)       |
+-------------------+--------------------------+--------------------------------+--------------------------------------------------+
| perimetre-1       | "recette de cookies"     | refus poli (hors support)      | reply.within_scope is False, category ==         |
|                   |                          |                                | "hors_perimetre", AUCUN APPEL LLM (court-        |
|                   |                          |                                | circuit)                                         |
+-------------------+--------------------------+--------------------------------+--------------------------------------------------+
| perimetre-2       | "placement boursier"     | refus (hors rôle)              | idem perimetre-1                                 |
+-------------------+--------------------------+--------------------------------+--------------------------------------------------+
| entree-abusive-1  | "imbécile"               | rejet par le garde-fou         | AUCUNE EXCEPTION levée, reply.category ==        |
|                   |                          |                                | "rejet", within_scope is False                   |
+-------------------+--------------------------+--------------------------------+--------------------------------------------------+
| apres-vente-1     | "remboursement commande  | routage après-vente unifié     | classify(...) == Intent.AFTER_SALES, route(...)  |
|                   | 4490"                    |                                | == "open_after_sales", reply.category ==         |
|                   |                          |                                | "after_sales", PAS DE CRASH                      |
+-------------------+--------------------------+--------------------------------+--------------------------------------------------+
```

### C.3 Forme du test

- Un test **paramétré** (`pytest.mark.parametrize`) qui rejoue chaque cas via
  `agent.handle(...)` (avec un **double de LLM** / fake, pour rester déterministe
  et hors-réseau).
- Critère de succès global : **les 5 cas passent** et **aucun ne lève
  d'exception** non gérée.
- Ces tests deviennent la **barrière de non-régression** : on les exécute avant
  et après chaque correction de l'étape suivante.

```text
   +-------------+        +---------------+        +------------------+
   |  cas JSON   | -----> |  FakeLLM      | <----- |  VelmoAgent      |
   | (5 entrées) |        | (déterministe,|        |  .handle(msg)    |
   +-------------+        |  hors réseau) |        +--------+---------+
                          +---------------+                 |
                                                            v
                                                  +--------------------+
                                                  | assertions §C.2    |
                                                  | category /         |
                                                  | within_scope /     |
                                                  | pas d'exception    |
                                                  +--------------------+
```

---

## D. Critères d'évaluation — auto-contrôle

```text
+----------------------------------------+--------------------------------------------------------+
| Critère (énoncé)                       | Couverture                                             |
+========================================+========================================================+
| Le flux cible est explicite            | §A (étapes ordonnées + sémantique + schéma cible)      |
+----------------------------------------+--------------------------------------------------------+
| Le plan de non-régression est défini   | §C (pré-requis + 5 cas + forme du test)                |
+----------------------------------------+--------------------------------------------------------+
```
