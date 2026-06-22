# Note de diagnostic — Agent Velmo « qui oublie et qui dérape »

> Livrable 1 (conception préliminaire) : note de diagnostic + schéma de l'agent.
> **Statut : BROUILLON à valider.**

## 1. Contexte & objectif

L'agent de support Velmo est en production. Deux plaintes récurrentes :
1. il **oublie** ce que le client a dit quelques messages plus tôt ;
2. il **sort de son rôle** (réponses hors périmètre, entrées douteuses mal gérées).

Par ailleurs, le **flux métier a évolué** : retours et remboursements doivent
désormais être traités par un **parcours après-vente unifié**.

Objectif de cette note : **délimiter le périmètre du problème** en distinguant
ce qui relève d'un **défaut de mémoire** de ce qui relève d'une **sortie de rôle**
(+ l'écart de **flux métier**), preuves à l'appui, avant toute correction.

## 2. Méthode

Démarche de diagnostic en 3 temps, appliquée à chaque cas problématique :
**observer le symptôme** (reproduction dans le chat) → **formuler une hypothèse**
→ **vérifier dans le code**. Aucune correction n'est faite à ce stade.

Matériel : les 5 conversations de `data/conversations_problematiques.json`,
rejouées sur l'agent réel (après déblocage de 2 erreurs de configuration —
voir annexe).

## 3. Périmètre du problème : 3 axes

| Axe | Question | Cas concernés |
|-----|----------|---------------|
| **A. Mémoire** | L'agent tient-il le contexte sur plusieurs tours ? | `ctx-oubli-1` |
| **B. Rôle / garde-fous** | Refuse-t-il proprement le hors-périmètre et les entrées abusives ? | `perimetre-1`, `perimetre-2`, `entree-abusive-1` |
| **C. Flux métier** | Le routage correspond-il au nouveau parcours après-vente ? | `apres-vente-1` |

**Le périmètre mémoire ≠ rôle est explicite** : l'oubli est un défaut de
*transmission du contexte* au modèle ; les sorties de rôle sont des défauts de
*garde-fous* (filtrage entrée + contrôle de périmètre). Les deux sont
indépendants et se corrigent séparément.

## 4. Constats détaillés

### Axe A — Mémoire (« qui oublie »)

| Réf | Défaut | Cause technique | Localisation | Effet observé |
|-----|--------|-----------------|--------------|---------------|
| **M1** | Historique jamais réinjecté | La mémoire est *écrite* (`record`) mais jamais *relue* : on passe `[]` au modèle au lieu de `self.memory.history()` | `agent.py:52` | À chaque tour l'agent repart de zéro ; il oublie la commande 4521 dès le tour suivant |
| **M2** | Fenêtre glissante inversée | `history()` renvoie `self._turns[:window]` (les tours les plus **anciens**) au lieu de `self._turns[-window:]` (les plus **récents**) | `memory.py:26` | Bug **latent** : même M1 corrigé, le contexte récent serait perdu dans une longue conversation |

**Preuve (M1)** — conversation rejouée :
> T1 « ma commande 4521 est en retard » → T3 « ma première commande 4521 est
> arrivée ? » → l'agent répond comme s'il découvrait la 4521, sans mémoire du
> « en retard » annoncé au T1.

**Mécanisme de mémoire :** présent mais **débranché**. Le composant
`ConversationMemory` existe et fonctionne ; c'est le *câblage* mémoire → modèle
qui est coupé (M1), et la sélection des tours qui est erronée (M2).

### Axe B — Rôle / garde-fous (« qui dérape »)

| Réf | Défaut | Cause technique | Localisation | Effet observé |
|-----|--------|-----------------|--------------|---------------|
| **R1** | Contrôle de périmètre non branché | `is_in_scope` est importé mais jamais appelé ; `within_scope=True` est codé en dur | `agent.py:51-59` | Le refus du hors-sujet (cookies, bourse) repose **uniquement sur le prompt système** : non garanti, contournable |
| **R2** | `is_in_scope` cassée | La fonction boucle sur les mots du message au lieu de `IN_SCOPE_TOPICS` → renvoie toujours `True` | `scope.py:23` | Même branchée, elle laisserait tout passer |
| **R3** | Garde-fou abusif non rattrapé | `validate_input` lève `GuardrailError`, mais aucun `try/except` ne l'intercepte (ni `handle`, ni la boucle chat) | `agent.py:48` + `chat.py:16-23` | L'entrée « imbécile » est bien détectée mais **fait planter l'application** au lieu d'un refus poli |

**Nuance importante** : pour cookies/bourse, l'agent *semble* bien refuser — mais
c'est le **modèle** qui obéit au prompt, pas un garde-fou déterministe. Le code
de contrôle de périmètre est soit débranché (R1), soit inopérant (R2).

### Axe C — Flux métier (parcours après-vente)

| Réf | Défaut | Cause technique | Localisation | Effet observé |
|-----|--------|-----------------|--------------|---------------|
| **F1** | Refactor après-vente incomplet | `_KEYWORDS` mappe retour/remboursement → `"after_sales"`, mais l'enum `Intent` n'a **pas** de membre `AFTER_SALES` (il garde `RETURN`/`REFUND`) → `Intent("after_sales")` lève `ValueError` | `flow.py:12-17` vs `29-32` | « Je veux un remboursement » **fait planter** l'application |
| **F2** | Mots-clés à premier-match | « commande » est testé avant « remboursement » | `flow.py:21-51` | « remboursement **pour la commande** 4490 » est mal classé en `order_status` au lieu d'après-vente |
| **F3** | Routage non câblé | `handle()` appelle `classify()` mais jamais `route()` ni les outils de `tools.py` ; la réponse vient toujours du LLM seul | `agent.py:46-60` | `classify` ne sert qu'à étiqueter `category` ; aucun outil métier n'est réellement invoqué |

**Intention correcte, implémentation incohérente** : le besoin métier (unifier
retour + remboursement) est bien présent dans les mots-clés, la docstring de
`flow.py` et l'outil `open_after_sales` — mais l'enum et le câblage n'ont pas
suivi.

## 5. Schéma de l'agent (flux + mémoire + garde-fous)

État **actuel** du pipeline. Les ⛔ marquent les points défaillants identifiés.

```mermaid
flowchart TD
    U[Utilisateur] -->|message| CHAT["chat.py — boucle CLI<br/>try/except KeyboardInterrupt seulement ⛔ R3"]
    CHAT --> H["agent.handle(message)"]

    H --> G1["validate_input — garde-fou entrée abusive<br/>lève GuardrailError, non rattrapée ⛔ R3"]
    G1 --> CLS["classify — flow.py<br/>Intent('after_sales') ⛔ F1<br/>premier-match mots-clés ⛔ F2"]
    CLS --> SCOPE["is_in_scope — JAMAIS APPELÉ ⛔ R1<br/>+ logique cassée ⛔ R2"]
    SCOPE --> SYS["build_system_prompt(persona)"]
    SYS --> LLM["llm.complete(system, [], user)<br/>historique = [] ⛔ M1"]

    subgraph MEM["ConversationMemory (memory.py)"]
        REC["record(user) / record(assistant)"]
        HIST["history() → _turns[:window] ⛔ M2"]
    end

    LLM --> REC
    HIST -. jamais relue .-> LLM
    LLM --> REPLY["AgentReply<br/>within_scope=True codé en dur ⛔ R1"]
    REPLY --> U

    ROUTE["route() + tools.py<br/>JAMAIS INVOQUÉS ⛔ F3"]
```

### Version ASCII (secours)

```
Utilisateur
    │ message
    ▼
[chat.py] boucle CLI ── try/except = KeyboardInterrupt seulement  ⛔R3
    │
    ▼
[agent.handle]
    │
    ├─► validate_input  (garde-fou entrée) ── lève GuardrailError, NON rattrapée  ⛔R3
    │
    ├─► classify (flow)  ── Intent("after_sales") => ValueError  ⛔F1
    │                       premier mot-clé gagne ("commande" masque "remboursement")  ⛔F2
    │
    ├─► is_in_scope  ── JAMAIS APPELÉE ⛔R1  +  logique cassée (toujours True) ⛔R2
    │
    ├─► build_system_prompt(persona)
    │
    ├─► llm.complete(system, [] , user)  ── historique = [] (mémoire débranchée)  ⛔M1
    │
    ├─► memory.record(user) / record(assistant)   [écrit OK]
    │        memory.history() => _turns[:window]  ── fenêtre inversée  ⛔M2
    │        (… mais jamais relue par le LLM)
    │
    └─► AgentReply(within_scope=True codé en dur ⛔R1)
            │
            ▼
        Utilisateur

route() + tools.py  ── JAMAIS INVOQUÉS  ⛔F3
```

## 6. Synthèse & cap

Les trois axes sont **indépendants** et alignés sur les 3 critères de performance :

| Critère de performance attendu | Axe | Défauts à corriger |
|--------------------------------|-----|--------------------|
| Tenir le contexte multi-tours | A. Mémoire | M1, M2 |
| Rester dans son rôle / refuser proprement | B. Rôle | R1, R2, R3 |
| Flux conforme au nouveau besoin métier | C. Flux | F1, F2, F3 |

> Cette note **délimite** le problème. La correction fera l'objet des étapes
> suivantes du brief.

---

### Annexe — Erreurs de configuration corrigées pour pouvoir reproduire

| # | Erreur | Cause | Correctif appliqué |
|---|--------|-------|--------------------|
| C1 | `KeyError: 'AZURE_AI_ENDPOINT'` | nom de variable d'env incohérent | `config.py` → lire `AZURE_AI_INFERENCE_ENDPOINT` |
| C2 | `KeyError: 'persona'` | placeholder `{persona}` vs `.format(role=...)` | `prompts.py` → `.format(persona=persona)` |

*(Ces deux corrections étaient des blocages d'amorçage, distincts des 7 défauts
fonctionnels ci-dessus.)*
