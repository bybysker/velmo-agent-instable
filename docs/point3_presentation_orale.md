# Point 3 — Notes pour présentation orale

> Version parlée de « ce qui a été fait ». À lire/raconter à voix haute.
> Chaque point suit le même fil : **ce qui clochait → ce qu'on a fait → où →
> comment on l'a prouvé.**

## Intro (à dire)

« Au point 3, la mission était d'adapter le flux de l'agent à un nouveau besoin
métier : les **retours** et les **remboursements** devaient désormais passer par
un **seul** parcours, le parcours après-vente. J'ai trouvé et corrigé cinq
problèmes, et surtout : pour chaque correction, j'ai écris un test automatique
qui garantit qu'elle ne pourra plus se re-casser. »

---

## 1. L'intention « après-vente » n'existait pas (F1)

*Source : `flow.py` — garanti par le test `test_route_after_sales_to_tool`.*

« Le code parlait encore l'ancien langage. Quand un client demandait un
remboursement, l'agent essayait de le ranger dans une catégorie *après-vente*…
qui ne figurait pas dans sa liste officielle d'intentions. Du coup, il
**plantait**. J'ai simplement **ajouté cette intention manquante** et je l'ai
**reliée au bon outil**, celui qui ouvre une demande après-vente. »


## 2. Le mauvais mot-clé l'emportait (F2)

*Source : `flow.py` — verrouillé par un test qu'on a ajouté,
`test_classify_after_sales_even_with_order_word`.*

« Plus subtil. Prenez la phrase : *« je veux un remboursement pour la commande
4490 »*. Elle contient deux mots-clés : **remboursement** et **commande**.
L'agent attrapait le premier qu'il croisait — *commande* — et croyait à une
simple demande de statut. Résultat : un remboursement traité comme un suivi de
colis. On a introduit une **règle de priorité claire** : si le client parle de
remboursement ou de retour, c'est de l'après-vente, un point c'est tout. »



## 3. L'outil de suivi de livraison "tracking" était invisible

*Source : `tools.py` — garanti par `test_track_delivery_is_exposed`.*

« L'agent ne pouvait pas utiliser son outil de suivi de colis. La raison est specifiée : dans ce le fichier tool, un outil n'est proposé à l'agent **que s'il est
documenté** — s'il a une petite phrase qui décrit ce qu'il fait. Celui-ci n'en
avait pas. j'ai donc **ajouté la description**, et l'outil est redevenu disponible. »



## 4. L'agent étiquetait mal ses réponses

*Source : `agent.py` — verrouillé par `test_agent_routes_refund_to_after_sales`.*

« Même après avoir réparé la classification, l'agent **étiquetait** encore mal
ce qu'il renvoyait : une demande de remboursement ressortait marquée
*« salutation »*. C'était la même cause que le cas où le client demandait un
remboursement, et que l'agent essayait de le ranger dans une catégorie *après-vente*. j'ai donc ajouté "after sales" et aligné l'intention.



## 5. Notre filet de sécurité était lui-même cassé


*Source : `regression.py` — garanti par `test_problem_conversations_load`.*

« Dernier point : le script censé **rejouer les conversations
de test** cherchait un fichier au **mauvais nom**. je l'ai donc
corrigé, et le filet de non-régression refonctionne. car sans ce filet, on ne peut pas prouver qu'on n'a rien cassé. »


---

## Conclusion (à dire)

« Au final, le parcours fonctionne **de bout en bout** : *« je veux un
remboursement pour la commande 4490 »* est bien reconnu comme de l'après-vente,
envoyé vers le bon outil, et correctement étiqueté. Côté chiffres, on est passé
de **6 tests en échec à 4** — et les 4 restants concernent d'autres sujets, la
mémoire et les garde-fous, qui sont les étapes suivantes. »
