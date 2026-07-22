\# Tests et validation qualité — edusmart\_learning



\## Vue d'ensemble



Le script `tests/test\_data\_quality.py` audite la qualité de la base MySQL

`edusmart\_learning`. Il exécute \*\*30 tests automatisés\*\* en environ 30 secondes.



Usage :



```bash

python tests/test\_data\_quality.py

```



Code de sortie :

\- `0` : tous les tests passent

\- `1` : au moins un test échoue

\- `2` : impossible de se connecter à MySQL



Ce script est exploitable dans un pipeline CI/CD pour arrêter automatiquement

un déploiement en cas d'anomalie détectée.



\## Catégorie 1 — Tests de volumétrie (6 tests)



Vérifie \*\*strictement\*\* (égalité exacte) le nombre de lignes par table :



| Table | Volume attendu |

|-------|----------------|

| modules | 50 |

| cours | 568 |

| quiz | 690 |

| progression | 66 931 (66 268 propres + 663 fantômes A11) |

| notes | 378 028 (376 147 propres + 1 881 doublons A7) |

| temps\_connexion | 377 047 |



\*\*Un écart d'une seule ligne fait échouer le test.\*\*



\## Catégorie 2 — Tests d'anomalies (18 tests)



Chaque anomalie A1 à A18 est détectée par une requête SQL dédiée et comparée

au volume annoncé dans `docs/anomalies.md`.



\*\*Tolérance : ± 3 %\*\* (élargie à ± 10 % pour A3).



Cette tolérance absorbe :

\- Les interactions entre anomalies (une ligne peut cumuler plusieurs anomalies)

\- La variance statistique inhérente au tirage aléatoire

\- Les cas particuliers documentés (module à un seul cours pour A3)



\## Catégorie 3 — Tests d'intégrité relationnelle (6 tests)



Vérifie \*\*strictement\*\* (0 violation attendue) les invariants relationnels :



| Test | Ce qu'il vérifie |

|------|------------------|

| Intégrité cours → modules | Aucun cours orphelin |

| Intégrité quiz → cours | Aucun quiz orphelin |

| Intégrité notes → quiz | Aucune note orpheline |

| Unicité progression | Contrainte UNIQUE(student\_code, id\_module) respectée |

| Tentatives ≤ 3 | Limite NB\_TENTATIVES\_MAX respectée |

| `foreign\_key\_checks = ON` | FK checks bien réactivées après A11 |



\*\*Ces tests doivent TOUJOURS passer.\*\* Un échec indique un état corrompu de la base.



\*\*Exception documentée\*\* : l'anomalie A11 injecte volontairement 663 progressions

avec un `id\_module` fantôme (violation FK explicite). Elle est détectée par

le test A11 dans la catégorie 2, non par les tests d'intégrité.



\## Sortie type



================================================================================

RAPPORT DE QUALITE - edusmart\_learning

================================================================================

TESTS DE VOLUMETRIE (strict)

\[PASS] Volume modules observe: 50 (attendu: 50)

\[PASS] Volume cours observe: 568 (attendu: 568)

...

RESUME : 30/30 tests reussis (100.0 %)



\## Reproductibilité



Le script s'exécute sur l'état actuel de la base. Pour reproduire l'état

de référence :



```bash

mysql -u root -p < sql/create\_database.sql

python scripts/insert\_data.py

python scripts/inject\_anomalies.py

python tests/test\_data\_quality.py

```



Résultat garanti : \*\*30/30 tests réussis\*\*.

