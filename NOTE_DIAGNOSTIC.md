# Note de diagnostic - Agent Velmo

Question 1 : diagnostiquer les oublis et les sorties de rôle.

## Ma démarche

Avant de corriger, je commence par comprendre. Je lis d'abord les conversations
problématiques (data/conversations_problematiques.json) comme si j'étais le client,
pour voir les symptômes. Ensuite seulement je regarde le code. C'est une approche
technico-fonctionnelle : si je pars en mode full-technique, je risque de corriger
des bugs sans régler le bon problème.

Je range les défauts dans 2 familles, qui sont indépendantes :
- Mémoire : l'agent oublie une info déjà dite dans la conversation.
- Rôle : l'agent fait ou dit quelque chose hors de sa mission, ou accepte une
  entrée qu'il ne devrait pas.

## 1. Le périmètre (mémoire vs rôle)

| Famille | Définition | Cas du JSON |
|---|---|---|
| Mémoire | perd une info déjà dite | ctx-oubli-1 |
| Rôle | répond hors mission / accepte une entrée interdite | perimetre-1, perimetre-2, entree-abusive-1 |

Le cas après-vente-1 n'est ni mémoire ni rôle : c'est un changement de flux métier,
donc il part dans la question 2.

## 2. Les oublis (défaut de mémoire)

Ce que j'observe : dans ctx-oubli-1, le client parle de la commande 4521 au début,
et quelques messages plus tard l'agent ne s'en souvient plus.

Le mécanisme : la mémoire existe bien (memory.py garde les messages), mais la
méthode history() renvoie les tours du DÉBUT de la liste (les plus vieux) et jette
les plus récents. Du coup ce que le client vient de dire est justement ce qui est
perdu.

En une phrase : la mémoire garde le vieux et oublie le récent.

## 3. Les sorties de rôle

a) Hors périmètre (perimetre-1 et perimetre-2) : l'agent répond à une recette de
cookies et à un conseil boursier, alors que ce n'est pas son domaine. Le contrôle
de périmètre ne borne rien.

b) Entrée abusive (entree-abusive-1) : la validation refuse seulement si le message
est EXACTEMENT le mot interdit. Donc une insulte dans une phrase ("tu es un
imbécile") passe sans être filtrée.

En une phrase : l'agent ne se limite pas à son rôle, il répond hors sujet et ne
filtre pas vraiment les insultes.

## 4. Livrables

- Cette note de diagnostic.
- Le schéma de l'agent (flux + mémoire + garde-fous), avec les points de défaut
  marqués. Trajet d'un message : entrée -> garde-fou -> périmètre -> flux ->
  mémoire -> modèle -> garde-fou sortie -> réponse.

## Ce que je ne fais pas encore

Je ne corrige rien dans cette étape. Je cadre le problème et je relie chaque
symptôme à un mécanisme précis du code. Les corrections viennent après, une fois
ce diagnostic validé.
