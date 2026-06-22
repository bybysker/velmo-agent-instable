# Cadrage — Adaptation du flux au nouveau besoin

**Étape 2 du brief — Cadrer l'adaptation du flux**

> Objectif (énoncé) : *définir comment le flux de l'agent doit être adapté au
> nouveau besoin métier.*
> Livrables : (A) flux cible + points d'écart avec l'existant ; (B) plan de
> vérification de non-régression sur les cas fournis.
> **Statut : à valider.**

---

## A. Flux cible

### A.1 Principe directeur — « fail fast »

On filtre **tôt** et on dépense **tard** : une entrée qu'on va refuser ne doit ni
consommer un appel modèle, ni risquer un dérapage. Les contrôles déterministes
(garde-fous) passent **avant** le LLM ; le LLM est la **dernière** étape, réservée
aux entrées légitimes et dans le périmètre.

### A.2 Étapes ordonnées (avec court-circuits)

| Ordre | Étape | Rôle | Court-circuit ? |
|---|---|---|---|
| 1 | **Garde-fou entrée** (`validate_input`) | Rejette les entrées abusives | ✅ → refus propre, **stop** |
| 2 | **Contrôle de périmètre** (`is_in_scope`) | Rejette le hors-sujet, de façon déterministe | ✅ → refus poli, **stop** |
| 3 | **Classification d'intention** (`classify`) | Détermine l'intention métier (dont `after_sales` unifié) | non |
| 4 | **Routage** (`route` + `tools`) | Sélectionne l'outil métier adéquat | non |
| 5 | **Mémoire** (`history`) | Réinjecte les tours précédents dans le prompt | non |
| 6 | **Appel LLM** (`complete`) | Génère la réponse, avec contexte + outils | non |
| 7 | **Réponse** (`AgentReply`) | `message` + `category` + `within_scope` **cohérents** | — |

### A.3 Sémantique cible des réponses

| Type d'entrée | Court-circuit | `within_scope` | `category` | `message` |
|---|---|---|---|---|
| Abusive | étape 1 | `False` | `rejet` | refus garde-fou poli |
| Hors-périmètre | étape 2 | `False` | `hors_perimetre` | refus standard Velmo |
| Salutation | jusqu'au LLM | `True` | `greeting` | réponse LLM |
| Commande / livraison | jusqu'au LLM | `True` | `order_status` / `delivery` | réponse LLM (+ outil) |
| **Retour / remboursement** | jusqu'au LLM | `True` | **`after_sales`** | réponse LLM (+ `open_after_sales`) |

### A.4 Nouveau besoin métier — parcours après-vente **unifié**

Retour **et** remboursement convergent vers **une seule** intention `after_sales`
et **un seul** outil `open_after_sales`. Concrètement, l'enum doit exposer un
membre `AFTER_SALES`, vers lequel pointent les mots-clés *retour, renvoyer,
remboursement, rembourser*.

### A.5 Schéma cible

```mermaid
flowchart TD
    U([Client]) -->|message| CHAT["chat.py — boucle CLI<br/>capte GuardrailError → refus propre"]
    CHAT --> G1{"1. validate_input<br/>abusif ?"}
    G1 -- oui --> RJ["AgentReply rejet<br/>within_scope=False"] --> U
    G1 -- non --> SC{"2. is_in_scope<br/>dans le périmètre ?"}
    SC -- non --> HP["AgentReply hors_perimetre<br/>within_scope=False"] --> U
    SC -- oui --> CLS["3. classify → Intent<br/>(AFTER_SALES unifié)"]
    CLS --> RT["4. route → outil<br/>(lookup_order / track_delivery / open_after_sales)"]
    RT --> MEM["5. history() → derniers tours<br/>_turns[-window:]"]
    MEM --> LLM["6. llm.complete(system, history, user)"]
    LLM --> REC["record(user) / record(assistant)"]
    REC --> RP["7. AgentReply<br/>category + within_scope cohérents"]
    RP --> U
```

---

## B. Points d'écart avec l'existant

Chaque écart = une étape du flux cible **absente, débranchée ou cassée**
aujourd'hui (réf. note de diagnostic).

| Étape cible | État actuel | Écart à combler | Réf. |
|---|---|---|---|
| 1. Garde-fou entrée → refus propre | détecte l'abus mais **crashe** (exception non rattrapée) | rattraper `GuardrailError` et renvoyer un `AgentReply` de refus | **R3** |
| 2. Contrôle de périmètre déterministe | `is_in_scope` **jamais appelé** ; `within_scope` codé en dur | brancher le contrôle dans `handle`, court-circuiter si hors-scope | **R1** |
| 2. (logique du contrôle) | `is_in_scope` renvoyait toujours `True` | boucler sur `IN_SCOPE_TOPICS` *(corrigé)* | **R2 ✅** |
| 3. Classification (after-vente unifié) | `Intent("after_sales")` **crashe** (membre manquant) | ajouter `Intent.AFTER_SALES` | **F1** |
| 3. (robustesse mots-clés) | « commande » masque « remboursement » | prioriser / désambiguïser les mots-clés | **F2** |
| 4. Routage vers outil | `route()`/`tools` **jamais invoqués** | câbler le routage dans `handle` | **F3** |
| 5. Mémoire réinjectée | `[]` passé au LLM | passer `self.memory.history()` | **M1** |
| 5. (fenêtre récente) | `_turns[:window]` (anciens) | `_turns[-window:]` (récents) | **M2** |
| 7. Réponse cohérente | `within_scope=True` en dur | refléter le vrai résultat | **R1** |

---

## C. Plan de vérification de non-régression

### C.1 Pré-requis — réparer le harnais

`regression.py` charge `conversations.json` (inexistant) au lieu de
`conversations_problematiques.json`, et ne fait que charger sans rejouer.
**À corriger** : bon nom de fichier + une fonction qui **rejoue** chaque
conversation dans l'agent et compare au comportement attendu.

### C.2 Cas fournis → vérifications

Pour chacun des 5 cas de `conversations_problematiques.json`, on définit une
assertion **déterministe** (indépendante du texte exact généré par le LLM).

| Cas | Entrée(s) | Attendu (énoncé) | Vérification de non-régression |
|---|---|---|---|
| `ctx-oubli-1` | 3 tours : 4521 → 4490 → 4521 | se souvient de la 4521 du tour 1 | après les 3 tours, `memory.history()` contient le 1er tour **et** l'historique réinjecté au LLM est **non vide** (mémoire effectivement transmise) |
| `perimetre-1` | « recette de cookies » | refus poli (hors support) | `reply.within_scope is False`, `category == "hors_perimetre"`, **aucun appel LLM** (court-circuit) |
| `perimetre-2` | « placement boursier » | refus (hors rôle) | idem `perimetre-1` |
| `entree-abusive-1` | « imbécile » | rejet par le garde-fou | **aucune exception levée**, `reply.category == "rejet"`, `within_scope is False` |
| `apres-vente-1` | « remboursement commande 4490 » | routage après-vente unifié | `classify(...) == Intent.AFTER_SALES`, `route(...) == "open_after_sales"`, `reply.category == "after_sales"`, **pas de crash** |

### C.3 Forme du test

- Un test **paramétré** (`pytest.mark.parametrize`) qui rejoue chaque cas via
  `agent.handle(...)` (avec un **double de LLM** / fake, pour rester déterministe
  et hors-réseau).
- Critère de succès global : **les 5 cas passent** et **aucun ne lève
  d'exception** non gérée.
- Ces tests deviennent la **barrière de non-régression** : on les exécute avant
  et après chaque correction de l'étape 3.

---

## D. Critères d'évaluation — auto-contrôle

| Critère (énoncé) | Couverture |
|---|---|
| Le flux cible est explicite | §A (étapes ordonnées + sémantique + schéma cible) |
| Le plan de non-régression est défini | §C (pré-requis + 5 cas + forme du test) |
