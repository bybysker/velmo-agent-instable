# Partie 1 — Diagnostiquer oublis et sorties de rôle

---

## 1. Caractériser les oublis observés

**Cas observé — `ctx-oubli-1` :**
L'utilisateur mentionne la commande `4521`, parle ensuite de la `4490`, puis revient à "la première commande". L'agent ne sait plus laquelle c'est.

**Mécanisme manquant :**
L'agent n'a pas de mémoire conversationnelle opérationnelle — il ne conserve pas le contexte des tours précédents pour le réutiliser.

> Source : `memory.py` — `class ConversationMemory`, `agent.py` — `def handle`

**Conséquence :**
L'agent ne peut pas résoudre des références comme "la première commande" ou "la précédente" — il traite chaque message comme s'il était le premier.

---

## 2. Caractériser les sorties de rôle

**Cas observés :**

| Cas | Ce que l'utilisateur demande | Ce que l'agent devrait faire |
|-----|------------------------------|------------------------------|
| `perimetre-1` | Une recette de cookies | Refus poli — hors périmètre support |
| `perimetre-2` | Un conseil de placement boursier | Refus poli — hors périmètre support |
| `entree-abusive-1` | Envoie "imbécile" | Rejet propre avant tout traitement |

**Mécanisme manquant :**
L'agent n'a pas de garde-fou qui vérifie si une demande entre dans son périmètre avant de répondre. Il n'a pas non plus de filtre capable d'intercepter un message abusif avant tout traitement.

> Source : `scope.py` — `def is_in_scope`, `guardrails.py` — `def validate_input`

**Conséquence :**
L'agent répond à n'importe quelle question, y compris du conseil financier. Il ne bloque pas les insultes et tente d'y répondre.

---

## 3. Note de diagnostic + schéma de l'agent

### Note de diagnostic

Le périmètre du problème se divise en quatre familles distinctes :

| Famille | Définition | Symptôme observé |
|---------|------------|-----------------|
| **Mémoire** | L'agent oublie ce qui a été dit avant | Commande `4521` perdue après mention de `4490` |
| **Sorties de rôle** | L'agent répond hors de son domaine | Recette de cookies, conseil boursier |
| **Garde-fous d'entrée** | L'agent accepte des messages abusifs | "imbécile" non intercepté |
| **Flux métier** | Mauvaise orientation d'une demande valide | "remboursement" non routé vers l'après-vente |

> Mémoire et sorties de rôle ne se corrigent pas au même endroit.

### Schéma de l'agent cible (flux + mémoire + garde-fous)

```
Message utilisateur
        │
        ▼
┌─────────────────────┐
│ Validation d'entrée │  → bloque insultes et messages hors usage
└──────────┬──────────┘    GARDE-FOU AMONT
           │
           ▼
┌─────────────────────┐
│ Détection intention │  → greeting / commande / livraison / après-vente / hors-scope
└──────────┬──────────┘
           │
     ┌─────┴──────┐
     │            │
  Hors scope   In scope
     │            │
     ▼            ▼
 Refus poli  ┌─────────────────────┐
             │  Chargement mémoire │  → injecte les derniers tours dans le prompt
             └──────────┬──────────┘    MÉMOIRE CONVERSATIONNELLE
                        │
                        ▼
             ┌─────────────────────┐
             │   Génération LLM    │  → le modèle reçoit une instruction qui lui interdit de répondre hors support Velmo
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │  Réponse structurée │  → message + catégorie + within_scope
             └─────────────────────┘    GARDE-FOU AVAL
```

- **Garde-fou amont** — `guardrails.py` — `def validate_input` — filtre avant tout traitement métier
- **Détection d'intention** — `flow.py` — `def classify` — classe et route le message vers le bon parcours
- **Mémoire conversationnelle** — `memory.py` — `class ConversationMemory` — réinjecte l'historique récent pour garder le contexte
- **Génération LLM** — `llm.py` + `prompts.py` — `def build_system_prompt` — appel avec système + historique + message actuel
- **Garde-fou aval** — `guardrails.py` — `class AgentReply` — format contraint (Pydantic) pour garantir la cohérence de sortie
