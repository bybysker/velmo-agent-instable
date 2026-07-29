# Schémas Mermaid — architecture, classes, séquences

Versions Mermaid des schémas ASCII de [cadrage_flux_cible.md](cadrage_flux_cible.md).
Chaque bloc se colle tel quel dans [mermaid.live](https://mermaid.live) (Mermaid
Live Editor), dans un README GitHub ou dans la prévisualisation Markdown de VS Code.

> **Périmètre.** §1 à §3 décrivent la **cible** (le flux tel qu'il doit être).
> §4 décrit l'**état réel du code** au moment de la rédaction, pour que l'écart
> soit visible plutôt que sous-entendu.

---

## 1. Architecture — modules et dépendances

Vue statique : qui dépend de qui. `agent.py` est le seul point d'assemblage ;
les modules de règles (`guardrails`, `scope`, `flow`) ne dépendent de rien —
c'est ce qui les rend testables sans réseau.

```mermaid
flowchart TB
    subgraph IO["Entrée / sortie"]
        CHAT["chat.py<br/><i>boucle CLI</i>"]
        REG["regression.py<br/><i>rejeu des cas fournis</i>"]
        DATA[("data/<br/>conversations_<br/>problematiques.json")]
    end

    subgraph CORE["Cœur — orchestration"]
        AG["agent.py<br/><b>VelmoAgent.handle()</b>"]
    end

    subgraph RULES["Règles déterministes — sans réseau"]
        GR["guardrails.py<br/>validate_input · AgentReply"]
        SC["scope.py<br/>is_in_scope · IN_SCOPE_TOPICS"]
        FL["flow.py<br/>Intent · classify · route"]
        TL["tools.py<br/>lookup_order · track_delivery<br/>open_after_sales"]
        PR["prompts.py<br/>build_system_prompt"]
    end

    subgraph EXT["Adaptateurs externes"]
        LLM["llm.py<br/>AzureLLM.complete"]
        CFG["config.py<br/>Settings · load_settings"]
        AZ(["Azure AI Inference<br/><i>Kimi-K2.6</i>"])
    end

    MEM["memory.py<br/>ConversationMemory"]

    CHAT --> AG
    CHAT --> LLM
    REG --> DATA
    REG -.rejeu.-> AG

    AG --> GR
    AG --> SC
    AG --> FL
    AG --> PR
    AG --> MEM
    AG -->|"protocole LLMClient"| LLM
    FL -.route vers.-> TL
    AG -.appelle l'outil routé.-> TL

    LLM --> CFG
    LLM --> AZ

    classDef ext fill:#fde,stroke:#b57
    classDef rules fill:#eef,stroke:#77b
    class AZ ext
    class GR,SC,FL,TL,PR rules
```

**Lecture.** La frontière `RULES` / `EXT` est le point clé : tout ce qui décide
d'un refus est à gauche (déterministe, gratuit, testable) ; tout ce qui coûte un
appel réseau est à droite. `VelmoAgent` ne connaît le LLM que par le protocole
`LLMClient`, ce qui autorise un double (`FakeLLM`) dans les tests.

---

## 2. Flux cible — parcours d'un message

Version Mermaid du schéma §A.5.

```mermaid
flowchart TD
    U([Client]) -->|message| CHAT["chat.py — boucle CLI"]
    CHAT --> G1{"1. validate_input<br/>entrée abusive ?"}

    G1 -- oui --> RJ["AgentReply<br/>category = rejet<br/>within_scope = False"]
    G1 -- non --> SC{"2. is_in_scope<br/>dans le périmètre ?"}

    SC -- non --> HP["AgentReply<br/>category = hors_perimetre<br/>within_scope = False"]
    SC -- oui --> CLS["3. classify → Intent<br/><i>AFTER_SALES unifié</i>"]

    CLS --> RT["4. route → outil<br/>lookup_order / track_delivery<br/>open_after_sales"]
    RT --> MEM["5. memory.history()<br/>_turns[-window:]"]
    MEM --> LLM["6. llm.complete(system, history, user)"]
    LLM --> REC["record(user) / record(assistant)"]
    REC --> RP["7. AgentReply<br/>category + within_scope cohérents"]

    RJ --> U
    HP --> U
    RP --> U

    classDef stop fill:#fdd,stroke:#c55
    class RJ,HP stop
```

---

## 3. Diagramme de classes

Ce qui est réellement une classe dans le code : `VelmoAgent`, `ConversationMemory`,
`AgentReply`, `AzureLLM`, `Settings`, plus deux types (`Intent`, `GuardrailError`)
et le protocole `LLMClient`. Les modules purement fonctionnels (`scope`, `flow`,
`prompts`, `tools`) sont représentés comme utilitaires `<<module>>`.

```mermaid
classDiagram
    direction LR

    class VelmoAgent {
        +LLMClient llm
        +ConversationMemory memory
        +str persona
        +handle(user_message) AgentReply
    }

    class LLMClient {
        <<Protocol>>
        +complete(system, history, user) str
    }

    class AzureLLM {
        -model
        +complete(system, history, user) str
    }

    class ConversationMemory {
        <<dataclass>>
        +int window
        -list~Turn~ _turns
        +record(role, content) None
        +history() list~Turn~
        +clear() None
        +len(memory) int
    }

    class AgentReply {
        <<BaseModel>>
        +str message
        +Category category
        +bool within_scope
    }

    class Intent {
        <<enumeration>>
        GREETING
        ORDER_STATUS
        DELIVERY
        RETURN
        REFUND
        AFTER_SALES
        UNKNOWN
    }

    class GuardrailError {
        <<exception ValueError>>
    }

    class Settings {
        <<frozen dataclass>>
        +str endpoint
        +str api_key
        +str model
    }

    class guardrails {
        <<module>>
        +BLOCKED_TERMS set
        +Category Literal
        +validate_input(text) None
    }

    class scope {
        <<module>>
        +IN_SCOPE_TOPICS set
        +is_in_scope(text) bool
    }

    class flow {
        <<module>>
        -_PRIORITY list
        -_ROUTES dict
        +classify(text) Intent
        +route(intent) str
    }

    class tools {
        <<module>>
        +TOOLS dict
        +register(fn) Callable
        +lookup_order(order_id) str
        +track_delivery(tracking) str
        +open_after_sales(order_id) str
    }

    class prompts {
        <<module>>
        +SYSTEM_PROMPT str
        +build_system_prompt(persona) str
    }

    LLMClient <|.. AzureLLM : implémente
    VelmoAgent o-- LLMClient : injecté
    VelmoAgent *-- ConversationMemory : possède
    VelmoAgent ..> AgentReply : produit
    VelmoAgent ..> guardrails : validate_input
    VelmoAgent ..> scope : is_in_scope
    VelmoAgent ..> flow : classify / route
    VelmoAgent ..> prompts : build_system_prompt
    VelmoAgent ..> tools : outil routé
    guardrails ..> GuardrailError : lève
    guardrails ..> AgentReply : valide category
    flow ..> Intent
    flow ..> tools : _ROUTES → nom d'outil
    AzureLLM ..> Settings : load_settings()
```

### 3.1 Points de conception à retenir

- `VelmoAgent o-- LLMClient` (agrégation) : le client est **injecté**, l'agent ne
  le crée pas — condition du test hors-réseau.
- `VelmoAgent *-- ConversationMemory` (composition) : si aucune mémoire n'est
  fournie, l'agent en crée une ; sa durée de vie est celle de l'agent.
- `Category` est un `Literal` Pydantic : toute `category` hors liste fait échouer
  la construction d'`AgentReply` — la sortie est **contrainte par le type**.

---

## 4. Diagrammes de séquence

### 4.1 Cas nominal — « remboursement commande 4490 » (après-vente unifié)

Le parcours complet, tous les garde-fous franchis. C'est la séquence **cible** :
elle inclut l'étape 4 (routage vers `open_after_sales`).

```mermaid
sequenceDiagram
    autonumber
    actor C as Client
    participant CH as chat.py
    participant AG as VelmoAgent
    participant GR as guardrails
    participant SC as scope
    participant FL as flow
    participant TL as tools
    participant PR as prompts
    participant ME as ConversationMemory
    participant LM as AzureLLM
    participant AZ as Azure AI Inference

    C->>CH: "remboursement commande 4490"
    CH->>AG: handle(user_message)

    AG->>GR: validate_input(text)
    GR-->>AG: None (aucun terme bloqué)

    AG->>SC: is_in_scope(text)
    SC-->>AG: True ("remboursement" ∈ IN_SCOPE_TOPICS)

    AG->>FL: classify(text)
    Note right of FL: _PRIORITY : AFTER_SALES testé<br/>AVANT ORDER_STATUS —<br/>"commande" ne masque plus<br/>"remboursement" (défaut F2)
    FL-->>AG: Intent.AFTER_SALES

    AG->>FL: route(Intent.AFTER_SALES)
    FL-->>AG: "open_after_sales"
    AG->>TL: open_after_sales("4490")
    TL-->>AG: "Demande après-vente enregistrée…"

    AG->>PR: build_system_prompt(persona)
    PR-->>AG: system

    AG->>ME: history()
    ME-->>AG: _turns[-window:]

    AG->>LM: complete(system, history, user)
    LM->>AZ: invoke(messages)
    AZ-->>LM: content
    LM-->>AG: answer

    AG->>ME: record("user", user_message)
    AG->>ME: record("assistant", answer)

    AG-->>CH: AgentReply(message, "after_sales", True)
    CH-->>C: réponse affichée
```

### 4.2 Court-circuit 1 — entrée abusive

Aucun appel LLM, aucune exception qui remonte : le refus est une **réponse
structurée**, pas un crash.

```mermaid
sequenceDiagram
    autonumber
    actor C as Client
    participant CH as chat.py
    participant AG as VelmoAgent
    participant GR as guardrails
    participant LM as AzureLLM

    C->>CH: "imbécile"
    CH->>AG: handle(user_message)
    AG->>GR: validate_input(text)
    GR--)AG: raise GuardrailError

    Note over AG: try / except GuardrailError<br/>l'exception est convertie<br/>en réponse (défaut R3)

    AG-->>CH: AgentReply("Merci de rester courtois…", "rejet", False)
    CH-->>C: refus poli
    Note over LM: jamais sollicité —<br/>0 token dépensé
```

### 4.3 Court-circuit 2 — hors périmètre

```mermaid
sequenceDiagram
    autonumber
    actor C as Client
    participant CH as chat.py
    participant AG as VelmoAgent
    participant GR as guardrails
    participant SC as scope
    participant LM as AzureLLM

    C->>CH: "une recette de cookies ?"
    CH->>AG: handle(user_message)
    AG->>GR: validate_input(text)
    GR-->>AG: None
    AG->>SC: is_in_scope(text)
    SC-->>AG: False (aucun mot de IN_SCOPE_TOPICS)
    AG-->>CH: AgentReply(REFUSAL_MESSAGE, "hors_perimetre", False)
    CH-->>C: refus standard Velmo
    Note over LM: jamais sollicité
```

### 4.4 Mémoire sur 3 tours — cas `ctx-oubli-1`

Ce que le test de non-régression doit observer : au 3ᵉ tour, l'historique passé
au LLM est **non vide** et contient le tour 1.

```mermaid
sequenceDiagram
    autonumber
    actor C as Client
    participant AG as VelmoAgent
    participant ME as ConversationMemory
    participant LM as LLMClient

    C->>AG: T1 "où en est ma commande 4521 ?"
    AG->>ME: history()
    ME-->>AG: [] (mémoire vide)
    AG->>LM: complete(system, [], T1)
    LM-->>AG: R1
    AG->>ME: record(user, T1) / record(assistant, R1)

    C->>AG: T2 "et la 4490 ?"
    AG->>ME: history()
    ME-->>AG: [T1, R1]
    AG->>LM: complete(system, [T1, R1], T2)
    LM-->>AG: R2
    AG->>ME: record(user, T2) / record(assistant, R2)

    C->>AG: T3 "finalement, la première ?"
    AG->>ME: history()
    ME-->>AG: [T1, R1, T2, R2]
    Note right of ME: _turns[-window:] → les tours<br/>RÉCENTS (défaut M2).<br/>window = 8 : T1 est encore là.
    AG->>LM: complete(system, [T1, R1, T2, R2], T3)
    LM-->>AG: R3 — la 4521 est retrouvée
```

### 4.5 Harnais de non-régression

```mermaid
sequenceDiagram
    autonumber
    participant PT as pytest (paramétré)
    participant RG as regression.py
    participant DT as conversations_problematiques.json
    participant AG as VelmoAgent
    participant FK as FakeLLM

    PT->>RG: load_problem_conversations()
    RG->>DT: read_text()
    DT-->>RG: 5 cas
    RG-->>PT: list[dict]

    loop pour chaque cas
        PT->>AG: handle(entrée)
        alt entrée refusée (abusive / hors périmètre)
            AG-->>PT: AgentReply — aucun appel LLM
        else entrée légitime
            AG->>FK: complete(system, history, user)
            FK-->>AG: réponse fixe (déterministe)
            AG-->>PT: AgentReply
        end
        PT->>PT: assert category / within_scope / pas d'exception
    end
```

---

## 5. Écart entre ces schémas et le code actuel

Les séquences §4 décrivent la **cible**. Vérification faite dans `src/velmo/`
à la date de rédaction :

```text
+--------------------------------------------------------+-----------------------------+-------------------+
| Étape du flux                                          | Code actuel                 | Statut            |
+========================================================+=============================+===================+
| 1. `validate_input` + `try/except GuardrailError`      | présent dans `handle`       | conforme (R3)     |
+--------------------------------------------------------+-----------------------------+-------------------+
| 2. `is_in_scope` bouclant sur `IN_SCOPE_TOPICS`        | présent                     | conforme (R2)     |
+--------------------------------------------------------+-----------------------------+-------------------+
| 3. `Intent.AFTER_SALES` + `_PRIORITY`                  | présents                    | conforme (F1, F2) |
+--------------------------------------------------------+-----------------------------+-------------------+
| 4. `route()` / `tools`                                 | JAMAIS APPELÉS par `handle` | ÉCART F3 OUVERT   |
+--------------------------------------------------------+-----------------------------+-------------------+
| 5. `memory.history()` passé au LLM, `_turns[-window:]` | présents                    | conforme (M1, M2) |
+--------------------------------------------------------+-----------------------------+-------------------+
| 7. `within_scope` reflétant le résultat                | présent                     | conforme (R1)     |
+--------------------------------------------------------+-----------------------------+-------------------+
```

Deux points à trancher lors de la validation du cadrage :

1. **Ordre des étapes 2 et 3.** Le cadrage place le contrôle de périmètre
   **avant** la classification. `handle` fait l'inverse : il classifie d'abord et
   n'appelle `is_in_scope` que si l'intention est `UNKNOWN`. Le résultat est
   équivalent sur les 5 cas fournis, mais le schéma §2 et le code divergent.
2. **Nom de la catégorie de refus.** Le cadrage écrit `hors_perimetre` ; le code
   renvoie `"refusal"`, seule valeur autorisée par le `Literal` `Category` de
   `guardrails.py`. Il faut aligner les deux — soit le document, soit le type.
