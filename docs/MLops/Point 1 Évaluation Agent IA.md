# 1. Décrire l’évaluation d’un agent IA

L’évaluation d’un agent IA sert à vérifier qu’il accomplit correctement une tâche complète, dans un environnement réel ou simulé, et pas seulement qu’il produit une bonne réponse. On mesure sa capacité à raisonner, à utiliser des outils, à respecter des contraintes de sécurité, et à rester fiable dans le temps.

## Ce qu’on évalue

On peut évaluer plusieurs dimensions en même temps :

- **La réussite de la tâche** : l’agent atteint-il l’objectif final ?
- **La qualité des appels d’outils** : utilise-t-il le bon outil, au bon moment, avec les bons paramètres ?
- **La sécurité** : évite-t-il les actions interdites, les sorties dangereuses ou les fuites d’informations ?
- **La fiabilité** : obtient-il des résultats stables quand on rejoue le même cas ?
- **La performance opérationnelle** : combien de temps prend-il, combien coûte-t-il, combien d’appels d’outils déclenche-t-il ?

## Jeu de cas

Un **jeu de cas** est un ensemble de scénarios de test représentatifs des usages réels de l’agent. Chaque cas décrit un contexte, une consigne, des contraintes et un résultat attendu vérifiable. Pour être utile, il faut y mettre des cas simples, des cas complexes, des cas limites et quelques scénarios adverses pour tester la robustesse.

Un bon jeu de cas doit aussi être **versionné**, pour qu’on sache exactement sur quels scénarios on compare deux versions d’agent. Cela aide à détecter les régressions et à garder un historique clair des performances.

## Métriques utiles

Les métriques servent à objectiver l’évaluation et à comparer plusieurs versions d’un agent. Les plus courantes sont :

- Taux de réussite de la tâche.
- Exactitude des appels d’outils.
- Temps d’exécution.
- Nombre d’appels d’outils.
- Coût de calcul ou de tokens.
- Score de sécurité ou de conformité.
- Détection de dérive : l’agent fait-il moins bien qu’avant sur les mêmes cas ?

## Tests automatisés

Les tests automatisés permettent de rejouer régulièrement les mêmes scénarios pour détecter une régression. On peut utiliser des vérifications exactes, des seuils de score, ou des évaluateurs spécialisés pour juger la qualité, la sécurité ou la pertinence des réponses.

En production, ces tests ne servent pas seulement à “valider avant la mise en ligne” : ils servent aussi à surveiller l’agent dans le temps, pour repérer une baisse de qualité ou un changement de comportement.

## Bon réflexe pratique

En pratique, une bonne évaluation d’agent IA combine :

- des cas réalistes,
- des métriques claires,
- des tests automatisés,
- un suivi de production,
- et une revue humaine sur les situations ambiguës ou sensibles.


## Sources

1. Microsoft Learn, *Evaluation Quick Reference*.
2. Anthropic, *Writing effective tools for AI agents*.
3. IBM, *Évaluation des agents IA*.
4. AgentX, *Évaluer les Agents IA d’Entreprise*.
