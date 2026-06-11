# Notes formateur — Velmo Agent Instable

Branche locale `instructor` — **ne pas pousser sur le remote**. Cette branche contient les éléments réservés au formateur :

- la liste des trous seedés sur `main` avec localisation, symptôme, cause et correctif
- un dossier `solutions/` avec les fichiers corrigés (miroir de `src/velmo/`)
- la branche `instructor` porte aussi le `src/` corrigé : `make test` y passe au vert (21/21)

Repère rapide : sur `main`, `uv run pytest` ⇒ **13 échecs / 8 succès**. Sur `instructor` ⇒ **21/21**.
`git diff main instructor -- src/` montre l'ensemble des correctifs.

## Trous

### Trou n°1 — Variable d'environnement mal nommée
- **Compétence ciblée**: C8 — Paramétrer un service d'IA à partir de sa documentation
- **Difficulté**: facile
- **Localisation**: `src/velmo/config.py:20`
- **Symptôme**: `KeyError: 'AZURE_AI_ENDPOINT'` au démarrage / dans `test_config`.
- **Cause racine**: le code lit `AZURE_AI_ENDPOINT` alors que `.env.example` (et le service) exposent `AZURE_AI_INFERENCE_ENDPOINT`.
- **Correctif**: `os.environ["AZURE_AI_INFERENCE_ENDPOINT"]`.

### Trou n°2 — Fenêtre de mémoire prise à l'envers
- **Compétence ciblée**: C17 — Développer les composants techniques (mémoire)
- **Difficulté**: moyen
- **Localisation**: `src/velmo/memory.py:30`
- **Symptôme**: `test_history_keeps_most_recent_turns` échoue ; l'agent « oublie » les tours récents.
- **Cause racine**: `self._turns[: self.window]` garde les plus **anciens** tours et jette les plus récents.
- **Correctif**: `self._turns[-self.window :]`.

### Trou n°3 — Mauvais nom de paramètre dans le prompt système
- **Compétence ciblée**: C10 — Intégrer l'API d'un modèle dans l'application
- **Difficulté**: moyen
- **Localisation**: `src/velmo/prompts.py:18`
- **Symptôme**: `KeyError: 'persona'` ; casse aussi les deux tests d'intégration `test_agent` (cascade).
- **Cause racine**: `SYSTEM_PROMPT.format(role=persona)` alors que le gabarit attend `{persona}`.
- **Correctif**: `SYSTEM_PROMPT.format(persona=persona)`.

### Trou n°4 — Validation d'entrée jamais déclenchée
- **Compétence ciblée**: C21 — Résoudre les incidents / CT3 — Définir le périmètre
- **Difficulté**: moyen
- **Localisation**: `src/velmo/guardrails.py` (`validate_input`)
- **Symptôme**: `test_validate_input_rejects_abusive_message` ne lève pas ; les entrées abusives passent.
- **Cause racine**: comparaison `if term == lowered` (égalité stricte) au lieu d'une recherche de sous-chaîne.
- **Correctif**: `if term in lowered`.

### Trou n°5 — Schéma de sortie non contraint
- **Compétence ciblée**: C17 / C21 — sécuriser les composants
- **Difficulté**: difficile
- **Localisation**: `src/velmo/guardrails.py` (`AgentReply.category`)
- **Symptôme**: `test_reply_rejects_unknown_category` : une catégorie arbitraire est acceptée.
- **Cause racine**: `category: str` accepte n'importe quelle valeur.
- **Correctif**: typer en `Literal["greeting", "order_status", "delivery", "after_sales", "refusal"]`.

### Trou n°6 — Contrôle de périmètre toujours vrai
- **Compétence ciblée**: C21 / CT3 — périmètre
- **Difficulté**: moyen
- **Localisation**: `src/velmo/scope.py` (`is_in_scope`)
- **Symptôme**: `test_out_of_scope_for_unrelated_question` : une question hors sujet est jugée dans le périmètre.
- **Cause racine**: `any(topic in lowered for topic in lowered.split())` compare chaque mot du message à lui-même ⇒ toujours `True`.
- **Correctif**: itérer sur `IN_SCOPE_TOPICS`, pas sur `lowered.split()`.

### Trou n°7 — Énumération métier périmée (flux)
- **Compétence ciblée**: C17 / CT4 — recherche méthodique
- **Difficulté**: difficile
- **Localisation**: `src/velmo/flow.py` (`Intent`, `_ROUTES`) + report dans `agent.py` (`_CATEGORY_BY_INTENT`)
- **Symptôme**: `ValueError: 'after_sales' is not a valid Intent` et `AttributeError: AFTER_SALES`.
- **Cause racine**: le métier a fusionné retours + remboursements en un parcours `after_sales`, mais l'enum garde encore `RETURN`/`REFUND`. La table de mots-clés produit déjà `after_sales`.
- **Correctif**: remplacer `RETURN`/`REFUND` par `AFTER_SALES = "after_sales"` ; mettre à jour `_ROUTES` et `_CATEGORY_BY_INTENT`.

### Trou n°8 — Outil non documenté donc non exposé
- **Compétence ciblée**: C10 / C17
- **Difficulté**: moyen
- **Localisation**: `src/velmo/tools.py` (`track_delivery`)
- **Symptôme**: `test_track_delivery_is_exposed` : l'outil n'apparaît pas dans `available_tools()`.
- **Cause racine**: `track_delivery` n'a pas de docstring ; le registre n'expose que les fonctions documentées.
- **Correctif**: ajouter une docstring décrivant l'outil.

### Trou n°9 — Mauvais nom de fichier de régression
- **Compétence ciblée**: CT4 / C21
- **Difficulté**: facile
- **Localisation**: `src/velmo/regression.py`
- **Symptôme**: `FileNotFoundError: .../data/conversations.json` ; le jeu de cas n'est pas chargé.
- **Cause racine**: le runner cible `conversations.json` alors que le fichier fourni est `conversations_problematiques.json`.
- **Correctif**: pointer sur `conversations_problematiques.json`.

### Trou n°10 — Mémoire non câblée dans l'appel modèle
- **Compétence ciblée**: C17 — composants (mémoire / flux)
- **Difficulté**: moyen
- **Localisation**: `src/velmo/agent.py` (`VelmoAgent.handle`)
- **Symptôme**: `test_agent_keeps_conversation_context` : l'historique transmis au modèle est vide.
- **Cause racine**: `self.llm.complete(system, [], user_message)` passe une liste vide au lieu de l'historique.
- **Correctif**: `self.llm.complete(system, self.memory.history(), user_message)`.

### Trou n°11 — Garde-fou de périmètre non appelé
- **Compétence ciblée**: C21 / CT3 — périmètre
- **Difficulté**: moyen
- **Localisation**: `src/velmo/agent.py` (`VelmoAgent.handle`)
- **Symptôme**: `test_agent_refuses_out_of_scope` : une demande hors sujet reçoit une réponse au lieu d'un refus.
- **Cause racine**: `handle` ne consulte jamais `is_in_scope` avant de répondre.
- **Correctif**: ajouter, avant le routage, un garde `if not is_in_scope(...)` qui renvoie une `AgentReply` de refus (`within_scope=False`, `category="refusal"`).

## Implémentation de référence

Le `src/velmo/` de la branche `instructor` est l'implémentation corrigée ; `solutions/src/velmo/` en est une copie figée (clé de correction). Le coeur (mémoire, garde-fous, périmètre, flux, outils) est testable hors-ligne via un `ScriptedLLM` ; l'appel réel à Azure AI Inference vit dans `llm.py`/`chat.py` et n'est pas couvert par les tests.

## Critères d'évaluation (rappel)

- L'agent tient le contexte sur une conversation multi-tours (trous 2, 3, 10).
- L'agent reste dans son rôle et refuse proprement les entrées hors périmètre (trous 4, 5, 6, 11).
- Le flux correspond au nouveau besoin métier (trou 7) ; les outils sont correctement exposés (trou 8) ; la non-régression est rejouable (trou 9) ; le service est correctement configuré (trou 1).

## Compétences ciblées

C8 (n1), C10 (n2), C17 (n2), C21 (n2), CT3 (n2), CT4 (n2).
