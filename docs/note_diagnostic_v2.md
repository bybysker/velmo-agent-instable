# Note de diagnostic — Agent Velmo

**Étape 1 du brief — Diagnostiquer oublis et sorties de rôle**

> Objectif (énoncé) : *à partir des conversations problématiques fournies, définir
> le périmètre du problème en distinguant les **défauts de mémoire** des
> **sorties de rôle**.*
> Livrable : note de diagnostic + schéma de l'agent (flux + mémoire + garde-fous).
> **Statut : à valider.**

---

## 0. Méthode

Chaque conversation problématique de `data/conversations_problematiques.json` a été
**rejouée sur l'agent réel**, puis analysée selon la démarche :
**symptôme observé → hypothèse → vérification dans le code**.

---

## 1. Périmètre du problème (mémoire vs rôle)

Le périmètre se partage en **deux familles de défauts indépendantes**, plus un
écart de flux métier traité à part.

```text
+--------------------------+-------------------------------+--------------------------------+--------------------------------+
| Famille                  | Nature du défaut              | Où ça se joue                  | Cas concernés                  |
+==========================+===============================+================================+================================+
| A. MÉMOIRE               | Le contexte des tours         | Mémoire <-> appel modèle       | `ctx-oubli-1`                  |
|                          | précédents n'est pas transmis |                                |                                |
|                          | au modèle                     |                                |                                |
+--------------------------+-------------------------------+--------------------------------+--------------------------------+
| B. RÔLE (GARDE-FOUS)     | Les entrées hors-périmètre /  | Garde-fous entrée + contrôle   | `perimetre-1`, `perimetre-2`,  |
|                          | abusives ne sont pas filtrées | de périmètre                   | `entree-abusive-1`             |
|                          | proprement                    |                                |                                |
+--------------------------+-------------------------------+--------------------------------+--------------------------------+
| C. FLUX MÉTIER (connexe) | Le routage ne correspond pas  | Classification d'intention     | `apres-vente-1`                |
|                          | au nouveau parcours après-    |                                |                                |
|                          | vente                         |                                |                                |
+--------------------------+-------------------------------+--------------------------------+--------------------------------+
```

> **Distinction clé.** Un **défaut de mémoire** = problème de *transmission du
> contexte* (l'agent *pourrait* bien répondre, mais on ne lui donne pas
> l'historique). Une **sortie de rôle** = problème de *garde-fou* (l'agent
> accepte/traite ce qu'il devrait refuser). Ce sont deux causes, deux endroits,
> deux corrections séparées.

---

## 2. Caractérisation des OUBLIS (axe mémoire)

### 2.1 Oublis observés

Conversation `ctx-oubli-1` rejouée :

```text
+------+----------------------------------------------------+----------------------------------------------------+-----------+
| Tour | Message client                                     | Réponse de l'agent                                 | Mémoire ? |
+======+====================================================+====================================================+===========+
| 1    | "ma commande 4521 est en retard"                   | accuse réception, demande l'e-mail                 | -         |
+------+----------------------------------------------------+----------------------------------------------------+-----------+
| 2    | "et la précédente, la 4490 ?"                      | répond sur la 4490, AUCUN LIEN avec la 4521        | [KO]      |
+------+----------------------------------------------------+----------------------------------------------------+-----------+
| 3    | "finalement, ma première commande, la 4521, est    | répond COMME S'IL DÉCOUVRAIT la 4521 ; a oublié le | [KO]      |
|      | arrivée ?"                                         | "en retard" du tour 1                              |           |
+------+----------------------------------------------------+----------------------------------------------------+-----------+
```

**Symptôme caractérisé :** l'agent est **sans état (stateless)** du point de vue
du modèle. Chaque message est traité **isolément** ; aucune information des tours
précédents n'est réutilisée. Le seul élément qui « persiste » (le numéro 4521)
n'est présent que parce que **le client le réécrit** lui-même.

### 2.2 Mécanisme de mémoire manquant / défaillant

Le composant mémoire **existe** (`ConversationMemory`, `memory.py`) et il est
même alimenté. Le défaut n'est donc pas l'absence de mémoire, mais son
**câblage** :

```text
+-----+----------------------------+------------------------------------------------------------------------+----------------+
| Réf | Défaut                     | Mécanisme                                                              | Localisation   |
+=====+============================+========================================================================+================+
| M1  | Mémoire JAMAIS RELUE       | La conversation est écrite (`record`) mais on passe une liste vide     | `agent.py:52`  |
|     |                            | `[]` au modèle au lieu de `self.memory.history()` -> le modèle ne voit |                |
|     |                            | jamais l'historique                                                    |                |
+-----+----------------------------+------------------------------------------------------------------------+----------------+
| M2  | Fenêtre glissante INVERSÉE | `history()` renvoie `self._turns[:window]` (les tours les plus         | `memory.py:26` |
|     |                            | ANCIENS) au lieu de `self._turns[-window:]` (les plus RÉCENTS)         |                |
+-----+----------------------------+------------------------------------------------------------------------+----------------+
```

> Image : on prend des notes après chaque échange (`record`), mais on **ne rouvre
> jamais le carnet** au moment de répondre (`[]`). M1 est la cause active de
> l'oubli observé ; M2 est un défaut **latent** qui se révélerait après M1, sur
> les conversations longues.

---

## 3. Caractérisation des SORTIES DE RÔLE (axe garde-fous)

### 3.1 Sorties de rôle observées

```text
+--------------------+-----------------------------+-------------------------------+-----------------------------------------+
| Cas                | Entrée client               | Comportement attendu          | Comportement observé                    |
+====================+=============================+===============================+=========================================+
| `perimetre-1`      | "recette de cookies ?"      | refus poli (hors support)     | refuse - MAIS VIA LE PROMPT SEUL, pas   |
|                    |                             |                               | un garde-fou                            |
+--------------------+-----------------------------+-------------------------------+-----------------------------------------+
| `perimetre-2`      | "quel placement boursier ?" | refus (hors rôle)             | refuse - IDEM, NON GARANTI              |
+--------------------+-----------------------------+-------------------------------+-----------------------------------------+
| `entree-abusive-1` | "imbécile"                  | rejet propre par le garde-fou | L'APPLICATION PLANTE (exception non     |
|                    |                             |                               | gérée)                                  |
+--------------------+-----------------------------+-------------------------------+-----------------------------------------+
```

**Symptôme caractérisé :** le maintien dans le rôle n'est **pas contrôlé par le
code**. Pour le hors-sujet, le refus dépend du bon vouloir du modèle face au
prompt (fragile, contournable). Pour l'entrée abusive, le garde-fou *se
déclenche* mais provoque un **crash** au lieu d'un refus courtois.

### 3.2 Mécanisme de garde-fous manquant / défaillant

```text
+-----+-----------------------------------+------------------------------------------------+---------------------------------+
| Réf | Défaut                            | Mécanisme                                      | Localisation                    |
+=====+===================================+================================================+=================================+
| R1  | Contrôle de périmètre NON BRANCHÉ | `is_in_scope` est importé mais jamais appelé   | `agent.py:51-59`                |
|     |                                   | dans `handle()` ; `within_scope=True` est codé |                                 |
|     |                                   | en dur (le champ "ment")                       |                                 |
+-----+-----------------------------------+------------------------------------------------+---------------------------------+
| R2  | `is_in_scope` DÉFAILLANTE         | La fonction bouclait sur les mots du message   | `scope.py:23`                   |
|     |                                   | au lieu de `IN_SCOPE_TOPICS` -> renvoyait      |                                 |
|     |                                   | toujours `True` (corrigé en cours de           |                                 |
|     |                                   | diagnostic)                                    |                                 |
+-----+-----------------------------------+------------------------------------------------+---------------------------------+
| R3  | Garde-fou abusif NON RATTRAPÉ     | `validate_input` lève `GuardrailError`, mais   | `agent.py:48` + `chat.py:16-23` |
|     |                                   | aucun `try/except` ne l'intercepte (ni         |                                 |
|     |                                   | `handle`, ni la boucle chat qui ne gère que    |                                 |
|     |                                   | `KeyboardInterrupt`) -> crash                  |                                 |
+-----+-----------------------------------+------------------------------------------------+---------------------------------+
```

> Le refus du hors-sujet ne doit pas reposer **uniquement** sur le prompt : il
> faut un garde-fou déterministe (R1 + R2). Et un garde-fou qui se déclenche doit
> produire un **refus**, pas une exception non gérée (R3).

---

## 4. Constat connexe — FLUX MÉTIER (`apres-vente-1`)

Hors dichotomie mémoire/rôle, mais relevé car bloquant. Le métier a unifié
**retour + remboursement** en un parcours **après-vente**. L'implémentation est
incohérente :

```text
+-----+-------------------------+---------------------------------------------------------------+----------------------------+
| Réf | Défaut                  | Mécanisme                                                     | Localisation               |
+=====+=========================+===============================================================+============================+
| F1  | Refactor INCOMPLET      | `_KEYWORDS` mappe vers `"after_sales"`, mais l'enum `Intent`  | `flow.py:12-17` vs `29-32` |
|     |                         | n'a pas de membre `AFTER_SALES` -> `Intent("after_sales")`    |                            |
|     |                         | lève `ValueError` (crash sur "je veux un remboursement")      |                            |
+-----+-------------------------+---------------------------------------------------------------+----------------------------+
| F2  | Mots-clés PREMIER-MATCH | "commande" testé avant "remboursement" -> "remboursement pour | `flow.py:21-51`            |
|     |                         | la commande 4490" mal classé en `order_status`                |                            |
+-----+-------------------------+---------------------------------------------------------------+----------------------------+
| F3  | Routage NON CÂBLÉ       | `handle()` appelle `classify()` mais jamais `route()` ni les  | `agent.py:46-60`           |
|     |                         | outils ; aucun outil métier n'est réellement invoqué          |                            |
+-----+-------------------------+---------------------------------------------------------------+----------------------------+
```

---

## 5. Schéma de l'agent (flux + mémoire + garde-fous)

État **actuel**. Les ⛔ pointent les défauts ; les ✅ ce qui fonctionne.

```mermaid
flowchart TD
    U([Client]) -->|message| CHAT["chat.py — boucle CLI<br/>n'attrape que KeyboardInterrupt"]
    CHAT --> H["agent.handle(message)"]

    subgraph GF["GARDE-FOUS"]
        G1["validate_input<br/>détecte l'abus ✅<br/>mais exception non rattrapée ⛔ R3"]
        SCOPE["is_in_scope<br/>jamais appelé ⛔ R1<br/>logique réparée ✅ R2"]
    end

    subgraph FL["FLUX (intentions)"]
        CLS["classify<br/>Intent('after_sales') ⛔ F1<br/>premier mot-clé gagne ⛔ F2"]
        ROUTE["route() + tools.py<br/>jamais invoqués ⛔ F3"]
    end

    subgraph MEM["MÉMOIRE (ConversationMemory)"]
        REC["record() — écriture ✅"]
        HIST["history() → _turns[:window] ⛔ M2"]
    end

    H --> G1 --> CLS --> SCOPE --> SYS["build_system_prompt(persona)"]
    SYS --> LLM["llm.complete(system, [] , user)<br/>historique = [] ⛔ M1"]
    LLM --> REC
    HIST -. jamais relue .-> LLM
    LLM --> REPLY["AgentReply<br/>within_scope=True codé en dur ⛔ R1"]
    REPLY --> U
```

### Version ASCII (secours)

```text
Client --message--> [chat.py] (try/except = KeyboardInterrupt seulement)
                        |
                        v
                 [agent.handle]
                        |
   GARDE-FOUS --> validate_input  -- abus détecté [OK] / exception non rattrapée [!]R3
                        |
   FLUX ---------> classify  -- Intent("after_sales") => crash [!]F1 / 1er mot-clé gagne [!]F2
                        |
   GARDE-FOUS --> is_in_scope  -- jamais appelé [!]R1 / logique réparée [OK]R2
                        |
                  build_system_prompt(persona)
                        |
                        v
              llm.complete(system, [], user)  -- historique = []  [!]M1
                        |
   MÉMOIRE ----> record() écrit [OK]   |   history() => _turns[:window] [!]M2
                        |                (... jamais relue par le LLM)
                        v
              AgentReply(within_scope=True en dur [!]R1)  --> Client

   route() + tools.py  -- JAMAIS INVOQUÉS [!]F3
```

---

## 6. Synthèse — périmètre explicite & cap

```text
+-----------------------+-------------------------------------------+------------+
| Axe                   | Critère de performance visé               | Défauts    |
+=======================+===========================================+============+
| MÉMOIRE               | Tenir le contexte multi-tours             | M1, M2     |
+-----------------------+-------------------------------------------+------------+
| RÔLE                  | Rester dans son rôle / refuser proprement | R1, R2, R3 |
+-----------------------+-------------------------------------------+------------+
| FLUX MÉTIER (connexe) | Flux conforme au nouveau besoin           | F1, F2, F3 |
+-----------------------+-------------------------------------------+------------+
```

**Conclusion.** Le périmètre est **explicitement scindé** : un problème de
**mémoire** (contexte non transmis) et un problème de **rôle** (garde-fous
absents/inopérants/non rattrapés), distincts dans leur cause comme dans leur
localisation. La correction fera l'objet de l'étape suivante.

---

### Annexe — blocages d'amorçage corrigés (pour pouvoir reproduire)

```text
+----+---------------------------------+------------------------------------------+------------------------------------------+
| #  | Erreur                          | Cause                                    | Correctif                                |
+====+=================================+==========================================+==========================================+
| C1 | `KeyError: 'AZURE_AI_ENDPOINT'` | nom de variable d'env incohérent         | `config.py` ->                           |
|    |                                 |                                          | `AZURE_AI_INFERENCE_ENDPOINT`            |
+----+---------------------------------+------------------------------------------+------------------------------------------+
| C2 | `KeyError: 'persona'`           | placeholder `{persona}` vs               | `prompts.py` ->                          |
|    |                                 | `.format(role=...)`                      | `.format(persona=persona)`               |
+----+---------------------------------+------------------------------------------+------------------------------------------+
```
