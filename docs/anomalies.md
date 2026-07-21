\# Catalogue des anomalies volontaires — MySQL edusmart\_learning



\## Vue d'ensemble



Ce document recense les \*\*18 anomalies volontaires\*\* introduites dans la base

`edusmart\_learning` par le script `scripts/inject\_anomalies.py`.



\*\*Total observé\*\* : 126 306 lignes anormales sur 823 314 (soit 15.3 %).



Chaque anomalie est \*\*paramétrable\*\* dans `config/generator\_config.py`

et \*\*reproductible\*\* grâce au seed `SEED\_ANOMALIES = 4242`.



Ces anomalies simulent les imperfections typiques d'un système de production

et serviront de matière première à la Phase B (ETL / nettoyage).



\---



\## Anomalies par table



\### Table `modules` (50 lignes)



| Code | Description | Colonne | Taux cible | Volume observé | Détection Phase B |

|------|-------------|---------|------------|----------------|-------------------|

| \*\*A1\*\* | Catégories désordonnées (variantes : DATA / data science / DataScience...) | `categorie` | 60 % | 30 | `GROUP BY BINARY UPPER(TRIM(categorie))` |

| \*\*A2\*\* | Modules inactifs | `actif` | 8 % | 4 | `WHERE actif = 0` |



\### Table `cours` (568 lignes)



| Code | Description | Colonne | Taux cible | Volume observé | Détection Phase B |

|------|-------------|---------|------------|----------------|-------------------|

| \*\*A3\*\* | Doublons de titres | `titre` | 3 % | 17 | `GROUP BY titre HAVING COUNT(\*) > 1` |

| \*\*A4\*\* | Variantes de type\_cours (video / VIDEO / pdf / Pdf) | `type\_cours` | 10 % | 53 | `GROUP BY BINARY type\_cours` |



\### Table `quiz` (690 lignes)



| Code | Description | Colonne | Taux cible | Volume observé | Détection Phase B |

|------|-------------|---------|------------|----------------|-------------------|

| \*\*A5\*\* | Durées incohérentes (1-2 min ou 240-480 min) | `duree\_minutes` | 3 % | 21 | `WHERE duree\_minutes NOT BETWEEN 5 AND 120` |



\### Table `notes` (378 028 lignes)



| Code | Description | Colonne | Taux cible | Volume observé | Détection Phase B |

|------|-------------|---------|------------|----------------|-------------------|

| \*\*A6\*\* | Scores supérieurs au score\_max du quiz | `score` | 1 % | 3 761 | `INNER JOIN quiz WHERE score > score\_max` |

| \*\*A7\*\* | Doublons `(student\_code, id\_quiz, tentative)` | (triplet) | 0.5 % | 1 881 | `GROUP BY student\_code, id\_quiz, tentative HAVING COUNT(\*) > 1` |



\### Table `progression` (66 931 lignes)



| Code | Description | Colonne | Taux cible | Volume observé | Détection Phase B |

|------|-------------|---------|------------|----------------|-------------------|

| \*\*A8\*\* | Pourcentages > 100 | `pourcentage` | 2 % | 1 325 | `WHERE pourcentage > 100` |

| \*\*A9\*\* | Pourcentages négatifs | `pourcentage` | 0.5 % | 331 | `WHERE pourcentage < 0` |

| \*\*A10\*\* | `dernier\_cours` = UUID inexistant | `dernier\_cours` | 4 % | 2 651 | `LEFT JOIN cours ON dernier\_cours = id\_cours WHERE cours.id\_cours IS NULL` |

| \*\*A11\*\* | `id\_module` fantôme (\*\*violation FK explicite\*\*) | `id\_module` | 1 % | 663 | `LEFT JOIN modules WHERE modules.id\_module IS NULL` |



> \*\*Note importante A11\*\* : cette anomalie viole intentionnellement la contrainte

> `fk\_progression\_module`. Elle est injectée après désactivation temporaire de

> `foreign\_key\_checks`, comme autorisé par la spec (« quelques violations de clés

> étrangères pour les besoins pédagogiques »). Les FK sont réactivées

> immédiatement après.



\### Table `temps\_connexion` (377 047 lignes)



| Code | Description | Colonne | Taux cible | Volume observé | Détection Phase B |

|------|-------------|---------|------------|----------------|-------------------|

| \*\*A12\*\* | Sessions sans déconnexion (crash / fermeture brutale) | `date\_deconnexion`, `duree\_minutes` | 8 % | 30 164 | `WHERE date\_deconnexion IS NULL` |

| \*\*A13\*\* | Durées négatives (bug de calcul) | `duree\_minutes` | 1 % | 3 770 | `WHERE duree\_minutes < 0` |

| \*\*A14\*\* | IP invalides (999.999.999.999, texte, chaîne vide...) | `adresse\_ip` | 2 % | 7 541 | Expression régulière IPv4 |

| \*\*A15\*\* | Variantes d'appareils (mobile / MOBILE / Mobile / Phone / iPad) | `appareil` | 12 % | 45 246 | `GROUP BY BINARY UPPER(TRIM(appareil))` |

| \*\*A16\*\* | Dates de connexion / déconnexion inversées | `date\_connexion`, `date\_deconnexion` | 0.5 % | 1 734 | `WHERE date\_deconnexion < date\_connexion` |



\### Anomalies transversales



| Code | Description | Tables affectées | Taux cible | Volume observé | Détection Phase B |

|------|-------------|------------------|------------|----------------|-------------------|

| \*\*A17\*\* | `student\_code` fantômes (LMS-999XXX) | notes, progression, temps\_connexion | 1 % | 8 219 | `WHERE student\_code LIKE 'LMS-999%'` ou LEFT JOIN avec fichier PostgreSQL |

| \*\*A18\*\* | Valeurs NULL supplémentaires | temps\_connexion : navigateur, appareil, adresse\_ip | 5 % | 18 895 | `WHERE navigateur IS NULL OR appareil IS NULL OR adresse\_ip IS NULL` |



\---



\## Bilan total



| Table | Volume | Anomalies | % |

|-------|--------|-----------|---|

| modules | 50 | 34 | 68 % |

| cours | 568 | 70 | 12 % |

| quiz | 690 | 21 | 3 % |

| notes | 378 028 | 9 422 | 2.5 % |

| progression | 66 931 | 5 639 | 8.4 % |

| temps\_connexion | 377 047 | 108 674 | 28.8 % |

| \*\*TOTAL\*\* | \*\*823 314\*\* | \*\*\~126 306\*\* | \*\*15.3 %\*\* |



> Le taux d'anomalies varie fortement selon les tables. La table `temps\_connexion`

> concentre le plus d'anomalies (28.8 %) car elle cumule plusieurs types d'anomalies

> (A12, A13, A14, A15, A16, A17, A18) qui peuvent se superposer sur une même ligne.



\---



\## Reproductibilité



Pour reproduire à l'identique cet état de base :



```bash

\# 1. Recréer les structures vides

mysql -u root -p < sql/create\_database.sql



\# 2. Réinsérer les données propres (SEED = 42)

python scripts/insert\_data.py



\# 3. Injecter les 18 anomalies (SEED\_ANOMALIES = 4242)

python scripts/inject\_anomalies.py

```



Résultat garanti : \*\*126 306 anomalies volontaires\*\* sur 823 314 lignes.



> \*\*Attention\*\* : le script `inject\_anomalies.py` n'est pas idempotent au sens strict

> (les anomalies A7 et A11 ajoutent des lignes). Ne pas le rejouer sur une base

> déjà injectée — la procédure officielle est CREATE + INSERT + INJECT une seule fois.

