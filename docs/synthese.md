\# Synthèse — Ma source MySQL edusmart\_learning



> Note personnelle pour les échanges avec le groupe.

> Résume tout ce que je dois pouvoir expliquer à Bachir, Aissata, Mouhameth et Seydina.



\---



\## Résumé en une phrase



J'ai construit une base MySQL de \*\*826 210 lignes\*\* simulant la plateforme d'apprentissage EduSmart sur 22 mois, avec \*\*126 515 anomalies volontaires documentées\*\* et un pipeline \*\*totalement reproductible\*\* validé par un script de 30 tests automatisés.



\---



\## Structure — 6 tables, 2 groupes fonctionnels



\### Bloc Catalogue (le contenu pédagogique)

\- \*\*`modules`\*\* — 200 modules (Data, IA, DevOps...)

\- \*\*`cours`\*\* — 2 305 cours répartis dans les modules

\- \*\*`quiz`\*\* — 2 758 évaluations liées aux cours



\### Bloc Activité (le comportement des étudiants)

\- \*\*`notes`\*\* — 378 512 tentatives de quiz

\- \*\*`progression`\*\* — 66 919 avancements

\- \*\*`temps\_connexion`\*\* — 376 516 sessions de connexion

\---



\## Choix architecturaux — Les 5 décisions à défendre



\### 1. UUID en CHAR(36) plutôt que BINARY(16)

\*\*Pourquoi :\*\* Priorité à la lisibilité pour débugger. La perte de perf est acceptable sur nos volumes (\~800K lignes).



\### 2. `student\_code` sans FK vers PostgreSQL

\*\*Pourquoi :\*\* C'est un \*\*identifiant fonctionnel externe\*\*, pas une clé technique. MySQL et PostgreSQL sont deux systèmes autonomes qui se parlent via une convention partagée, pas via une contrainte.



\### 3. Contrainte `UNIQUE(student\_code, id\_module)` sur `progression`

\*\*Pourquoi :\*\* Cette contrainte définit la nature \*\*snapshot\*\* de la table. Un étudiant a UNE seule progression par module, mise à jour au fil du temps. C'est différent de `notes` qui est événementielle (une ligne par tentative).



\### 4. CHECK volontairement omises sur `progression.pourcentage` et `temps\_connexion.duree\_minutes`

\*\*Pourquoi :\*\* Pour permettre l'injection d'anomalies pédagogiques (progression > 100, durée négative). Un CHECK strict aurait empêché la Phase 5.



\### 5. Aucune FK sur `temps\_connexion`

\*\*Pourquoi :\*\* Cette table n'a besoin que de `student\_code` (référence externe) et pas d'autres tables MySQL. Pas de contrainte inutile.



\---



\## Pipeline de production — Les 4 scripts



sql/create\_database.sql → crée les 6 tables (idempotent)

scripts/generate\_data.py → produit les CSV propres (seed 42)

scripts/insert\_data.py → charge en base par batch de 1000

scripts/inject\_anomalies.py → introduit 18 anomalies (seed 4242)



\*\*Principe fondamental\*\* : séparation génération / insertion. Je peux inspecter mes CSV avant de les charger, rejouer l'insertion sans régénérer, et partager les CSV avec le groupe sans donner accès à ma base.



\*\*Seeds différents\*\* : SEED=42 pour les données propres, SEED\_ANOMALIES=4242 pour les anomalies. Ça permet de rejouer les anomalies indépendamment si je change un paramètre de génération.



\---



\## Distribution réaliste des étudiants



Sur mes 10 000 étudiants LMS :



| Profil | Proportion | Modules suivis | Notes | Connexions |

|---|---|---|---|---|

| Inactifs | 20 % (2000) | 0 | 0-2 | 0-3 |

| Réguliers | 50 % (5000) | 3-8 | 10-40 | 10-40 |

| Investis | 25 % (2500) | 8-15 | 40-100 | 40-100 |

| Super-actifs | 5 % (500) | 15-25 | 100-200 | 100-200 |



\*\*C'est une distribution de Pareto\*\* : la plupart des utilisateurs consomment un peu, une minorité consomme beaucoup. Reflet réaliste d'une vraie plateforme.



\---



\## Les 18 anomalies — Résumé



\*\*Types d'anomalies injectées\*\* :

\- Erreurs de saisie (variantes de casse, orthographes multiples)

\- Valeurs hors bornes (scores > max, pourcentages > 100)

\- Références orphelines (student\_codes fantômes, dernier\_cours inexistant)

\- Données manquantes (déconnexions non enregistrées, IP invalides)

\- Doublons pédagogiques (titres, tentatives)

\- Violation FK explicite (A11)



\*\*Total : 126 306 lignes anormales sur 823 314 (\~15.3 %)\*\* — proche du taux moyen d'un vrai système opérationnel.



\*\*Détail complet\*\* : voir `docs/anomalies.md`



\---



\## Coordination avec le groupe



\### Ce que j'ai fourni



\- \*\*`student\_codes.csv`\*\* (10 000 codes) → Mouhameth et Seydina utilisent ces codes dans MongoDB et Redis

\- \*\*`catalogue\_modules.csv`\*\* (50 modules) → tous les `code\_module` référencables

\- \*\*`catalogue\_cours\_quiz.csv`\*\* (790 lignes) → tous les `code\_cours` et `code\_quiz`



\### Ce que je consomme d'Aissata



\- \*\*`etudiants.csv`\*\* (10 100 lignes) → j'en dérive mes 10 000 student\_codes

\- Règle de mapping que \*\*j'ai définie\*\* (pas Aissata) : `"LMS-" + matricule\[3:].zfill(6)`



\### Convention temporelle du groupe



Toutes les dates du projet dans la fenêtre : \*\*1er septembre 2024 → 30 juin 2026\*\*



\---



\## Questions probables et réponses préparées



\### « Pourquoi tu as choisi utf8mb4 et pas utf8 ? »



`utf8` en MySQL est \*\*incomplet\*\* (3 octets max). `utf8mb4` supporte l'Unicode complet, y compris les emojis et les caractères asiatiques. C'est le standard aujourd'hui.



\### « Pourquoi tes tests d'anomalies utilisent une tolérance de 3 % ? »



Parce que les anomalies interagissent entre elles. Par exemple, une ligne peut avoir son `appareil` remplacé par une variante (A15) puis mis à NULL (A18). Le test A15 la manquera. La tolérance à 3 % absorbe ces interactions statistiques.



\### « Comment tu as géré la contrainte UNIQUE sur progression pour A17 ? »



L'anomalie A17 remplace le `student\_code` par un fantôme LMS-999XXX (999 valeurs possibles). Sur 669 UPDATE, le paradoxe des anniversaires rend les collisions probables. J'ai ajouté une gestion à 5 tentatives par UPDATE : si le couple (fantôme, module) existe déjà, je re-tire un fantôme. Dans mon dataset final, aucune collision non résolue.



\### « C'est quoi la différence entre notes et progression ? »



\- \*\*notes = événementiel\*\* : une ligne à chaque tentative, la table croît indéfiniment

\- \*\*progression = snapshot\*\* : une seule ligne par (étudiant, module), mise à jour avec le temps



C'est un choix de modélisation classique en Data Engineering. La contrainte `UNIQUE(student\_code, id\_module)` matérialise ce choix.



\### « Comment tu prouves que ta base est cohérente ? »



Un script Python de 30 tests automatisés en 30 secondes : `python tests/test\_data\_quality.py`. Il vérifie les volumes exacts, les taux d'anomalies (avec tolérance), et l'intégrité relationnelle. 30/30 passent.



\### « Pourquoi tu utilises deux seeds différents ? »



\- SEED=42 pour les données propres → si je change SEED\_ANOMALIES, mes données propres restent identiques

\- SEED\_ANOMALIES=4242 pour les anomalies → si je change SEED, mes anomalies suivent une logique indépendante



Ça permet de \*\*paramétrer indépendamment\*\* les deux dimensions du système.



\---



\## Points forts à mettre en avant



1\. \*\*Pipeline totalement reproductible\*\* — n'importe qui peut cloner mon dépôt et retrouver le même état de base

2\. \*\*18 anomalies documentées\*\* avec leur taux, leur méthode de détection, et leur justification métier

3\. \*\*Script de tests automatisés\*\* qui audite 30 propriétés en 30 secondes

4\. \*\*Coordination proactive du groupe\*\* — j'ai produit et partagé les 3 fichiers dont Mouhameth et Seydina avaient besoin sans qu'ils me le demandent

5\. \*\*Documentation complète\*\* — README, schéma, anomalies, tests : tout est écrit

