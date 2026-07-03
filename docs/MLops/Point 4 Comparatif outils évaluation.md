# 4. Comparer deux outils d’évaluation d’agents IA

Pour un mini-benchmark pédagogique, on peut comparer **Langfuse** et **LangSmith**. C’est un duo intéressant parce qu’il permet de voir la différence entre un outil très orienté tracing / observabilité et un outil plus complet sur l’évaluation, le debug et le cycle de vie de l’agent.

## Pourquoi ce duo est intéressant

- **Langfuse** est très bon pour tracer les appels LLM, suivre les prompts et observer le comportement d’un agent en production.
- **LangSmith** va plus loin avec des évaluations, du debug, du suivi des expériences et une logique plus intégrée autour du développement d’agents.
- Les deux outils sont assez proches pour être comparés, mais assez différents pour produire une vraie recommandation.

## Critères de comparaison

Pour comparer deux outils d’évaluation d’agents, on peut utiliser des critères simples et visibles :

- Tracing / observabilité : permet de voir ce que fait l’agent étape par étape.
- Évaluation automatisée : permet de noter les sorties ou les comportements avec des métriques.
- Gestion des prompts : permet de versionner et tester les prompts.
- Alertes et suivi en production : permet de repérer une dégradation ou une dérive.
- Self-host / conformité : permet de mieux contrôler les données et l’hébergement.
- Facilité de prise en main : permet de savoir si l’outil est simple à adopter.

## Mini-comparatif

| Critère | Langfuse | LangSmith |
|---|---|---|
| Tracing / observabilité | Très bon pour suivre les traces et les coûts. | Très bon aussi, avec une approche plus intégrée au cycle de développement. |
| Évaluation automatisée | Présente, surtout pour analyser les comportements et les sorties. | Très développée, avec une logique forte d’évaluation et de debug. |
| Gestion des prompts | Point fort important. | Aussi présent, avec une bonne intégration au workflow. |
| Suivi en production | Bon niveau d’observabilité. | Plus complet sur la boucle dev → test → production. |
| Self-host / conformité | Souvent mis en avant pour le contrôle de la donnée. | Plus orienté expérience intégrée, selon l’usage. |
| Facilité de prise en main | Assez accessible si on veut démarrer vite. | Très pratique pour les équipes déjà dans l’écosystème LangChain. |

## Lecture du benchmark

Langfuse est souvent le meilleur choix pour **commencer** quand on veut surtout tracer, comprendre et monitorer les appels de l’agent. LangSmith devient plus intéressant quand on veut une chaîne plus large, avec debug, évaluation et amélioration continue dans un même environnement.


## Conclusion

**Langfuse aide surtout à voir et comprendre ce que fait l’agent. LangSmith aide davantage à évaluer, tester et faire évoluer l’agent dans une boucle plus complète.**

## Sources

1. LangChain, *LangSmith vs. Langfuse*.
2. Noveum AI, *9 Best AI Agent Evaluation Platforms in 2026*.
