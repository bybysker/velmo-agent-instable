# Velmo Agent Instable

Assistant de support conversationnel de Velmo, branché sur un modèle hébergé via Azure AI Inference (Kimi-K2.6). Il répond aux questions clients sur les commandes, livraisons et le parcours après-vente.

## Features

- Conversation multi-tours avec mémoire glissante du contexte client
- Garde-fous d'entrée (filtrage des messages hors politique d'usage)
- Contrôle de périmètre : l'assistant se cantonne au support commandes / livraisons / après-vente
- Routage par intention vers les outils métier (statut de commande, suivi de colis, après-vente)
- Réponses structurées via un schéma de sortie typé
- Rejeu d'un jeu de conversations de référence pour suivre la non-régression

## Stack

- Python 3.11 (géré avec `uv`)
- LangChain 1.x + `langchain-azure-ai` (Azure AI Inference, modèle Kimi-K2.6)
- Pydantic 2 pour les schémas de sortie
- pytest pour la suite de tests

## Setup

```bash
make install              # uv sync — installe les dépendances
cp .env.example .env      # puis renseigner les variables AZURE_AI_INFERENCE_*
make test                 # lance la suite de tests
make chat                 # démarre l'assistant en ligne de commande
```

Pour un lancement conteneurisé :

```bash
make up                                                   # docker compose up -d
docker compose exec agent uv run python -m velmo.chat     # ouvre le chat
make down
```

## Layout

```
src/velmo/
  agent.py        Orchestrateur : garde-fous, périmètre, mémoire, appel modèle
  config.py       Lecture de la configuration depuis l'environnement
  guardrails.py   Validation des entrées et schéma de réponse
  scope.py        Contrôle de périmètre des demandes
  flow.py         Classification d'intention et routage des outils
  tools.py        Outils métier exposés à l'assistant
  memory.py       Mémoire de conversation à fenêtre glissante
  prompts.py      Assemblage du prompt système
  llm.py          Client Azure AI Inference
  chat.py         Boucle de chat en ligne de commande
data/             Jeux de conversations de référence
tests/            Suite de tests
```

## Useful commands

```bash
make fmt        # ruff format + autofix
make lint       # ruff check
make typecheck  # mypy
make replay     # rejoue les conversations de référence sur le modèle réel
make replay-offline  # idem, sans connexion au modèle
make down       # arrête les services docker
```

## Documentation

- `docs/note_de_diagnostic.md` — diagnostic mémoire / rôle, schéma de l'agent, flux cible, plan de non-régression
- `docs/journal_des_choix.md` — décisions prises et limites connues

## Known issues

Les outils métier ne sont pas encore appelés par l'agent : le routage se traduit par la catégorie de réponse. Les filtres d'entrée et de périmètre reposent sur des mots-clés. Voir les limites connues dans `docs/journal_des_choix.md`.

## License

Propriétaire — Velmo.
