\# Schéma de la base `edusmart\_learning`



\*\*Projet :\*\* EduSmart Decision Platform - Groupe 2

\*\*Source :\*\* MySQL - Plateforme pédagogique

\*\*Auteure :\*\* Ndeye Penda SARR



\---



\## 1. Vue d'ensemble



La base `edusmart\_learning` représente la \*\*plateforme d'apprentissage en ligne\*\* d'EduSmart. Elle est structurée en deux blocs fonctionnels :



\- \*\*Bloc Catalogue\*\* — contenu proposé sur la plateforme : `modules`, `cours`, `quiz`

\- \*\*Bloc Activité\*\* — usage de la plateforme par les étudiants : `notes`, `progression`, `temps\_connexion`



La base ne contient \*\*aucune information sur les étudiants\*\* (nom, prénom, filière, etc.). Ces informations sont dans la base PostgreSQL (source 1). Le lien entre les deux bases est assuré par un identifiant fonctionnel partagé : le \*\*`student\_code`\*\* (format `LMS-XXXXXX`).



\---



\## 2. Diagramme entité-association



!\[Schéma de la base edusmart\_learning](schema\_edusmart\_learning.png)



\---



\## 3. Choix techniques



| Décision | Choix retenu | Justification |

|---|---|---|

| Moteur | InnoDB | Seul moteur MySQL qui supporte réellement les FK et les transactions |

| Encodage | utf8mb4 + utf8mb4\_unicode\_ci | Support complet Unicode, gestion correcte des accents français |

| UUID | CHAR(36) | Lisibilité en debug, différence de perf négligeable à cette échelle |

| Comportement FK | ON DELETE RESTRICT / ON UPDATE RESTRICT | Protection de l'intégrité, on interdit la suppression d'un parent référencé |

| CHECK sur colonnes à anomalies | Volontairement omises | Une CHECK est appliquée par MySQL 8.0.16+ et refuserait les anomalies pédagogiques |



\---



\## 4. Description des tables



\### 4.1 `modules` (bloc Catalogue)



Brique de plus haut niveau du catalogue. Un module regroupe plusieurs cours.



| Colonne | Type | Contraintes | Description |

|---|---|---|---|

| id\_module | CHAR(36) | PK, NOT NULL | Identifiant technique (UUID) |

| code\_module | VARCHAR(20) | UNIQUE, NOT NULL | Code métier (ex. `MOD-IA-01`) |

| nom\_module | VARCHAR(150) | NOT NULL | Libellé du module |

| categorie | VARCHAR(100) | NOT NULL | Thématique (Data, IA, Développement...) |

| niveau | VARCHAR(30) | NOT NULL | Débutant, Intermédiaire, Avancé |

| duree\_heures | INT | CHECK > 0, NOT NULL | Durée estimée totale |

| actif | BOOLEAN | DEFAULT TRUE | Module actif ou non |



\### 4.2 `cours` (bloc Catalogue)



Leçons appartenant à un module. Relation n:1 avec `modules`.



| Colonne | Type | Contraintes | Description |

|---|---|---|---|

| id\_cours | CHAR(36) | PK, NOT NULL | Identifiant technique |

| id\_module | CHAR(36) | FK → modules, NOT NULL | Module de rattachement |

| titre | VARCHAR(200) | NOT NULL | Titre du cours |

| ordre | INT | CHECK > 0, NOT NULL | Position dans le module |

| duree\_minutes | INT | CHECK > 0, NOT NULL | Durée en minutes |

| type\_cours | VARCHAR(30) | NOT NULL | Vidéo, PDF, TP, Projet |

| statut | VARCHAR(20) | DEFAULT 'PUBLIE' | Statut de publication |



\### 4.3 `quiz` (bloc Catalogue)



Quiz associés à un cours. Relation n:1 avec `cours` (un cours peut avoir 0, 1 ou N quiz).



| Colonne | Type | Contraintes | Description |

|---|---|---|---|

| id\_quiz | CHAR(36) | PK, NOT NULL | Identifiant technique |

| id\_cours | CHAR(36) | FK → cours, NOT NULL | Cours de rattachement |

| titre | VARCHAR(150) | NOT NULL | Titre du quiz |

| nb\_questions | INT | CHECK > 0, NOT NULL | Nombre de questions |

| score\_max | DECIMAL(5,2) | CHECK > 0, NOT NULL | Score maximum atteignable |

| duree\_minutes | INT | CHECK > 0, NOT NULL | Durée maximale du quiz |



\### 4.4 `notes` (bloc Activité)



\*\*Table événementielle\*\* : chaque ligne = une tentative d'un étudiant à un quiz. Un étudiant peut avoir plusieurs lignes pour un même quiz (plusieurs tentatives).



| Colonne | Type | Contraintes | Description |

|---|---|---|---|

| id\_note | CHAR(36) | PK, NOT NULL | Identifiant technique |

| id\_quiz | CHAR(36) | FK → quiz, NOT NULL | Quiz concerné |

| student\_code | VARCHAR(30) | NOT NULL, INDEX | Identifiant LMS (LMS-XXXXXX). \*\*Pas de FK vers PostgreSQL.\*\* |

| date\_passage | DATETIME | NOT NULL, INDEX | Date de la tentative |

| score | DECIMAL(5,2) | CHECK >= 0, NOT NULL | Score obtenu |

| tentative | INT | CHECK > 0, DEFAULT 1 | Numéro de tentative |

| valide | BOOLEAN | DEFAULT FALSE | Quiz validé ou non |



\### 4.5 `progression` (bloc Activité)



\*\*Table snapshot\*\* : une ligne par couple (étudiant, module), garantie par `UNIQUE(student\_code, id\_module)`. Contrairement à `notes`, cette table est mise à jour (`UPDATE`), pas augmentée (`INSERT`).



| Colonne | Type | Contraintes | Description |

|---|---|---|---|

| id\_progression | CHAR(36) | PK, NOT NULL | Identifiant technique |

| student\_code | VARCHAR(30) | NOT NULL, INDEX | Identifiant LMS |

| id\_module | CHAR(36) | FK → modules, NOT NULL | Module concerné |

| pourcentage | DECIMAL(5,2) | \*\*PAS de CHECK\*\* (anomalies attendues) | Pourcentage d'avancement |

| dernier\_cours | CHAR(36) | NULL, \*\*PAS de FK\*\* (anomalies attendues) | Dernier cours consulté |

| date\_maj | DATETIME | DEFAULT CURRENT\_TIMESTAMP | Date de dernière mise à jour |



\*\*Contrainte métier :\*\* `UNIQUE(student\_code, id\_module)` — une seule progression par étudiant et par module.



\### 4.6 `temps\_connexion` (bloc Activité)



\*\*Table événementielle\*\* : historique brut des sessions de connexion. Aucune FK vers d'autres tables MySQL (ne dépend que du `student\_code` externe).



| Colonne | Type | Contraintes | Description |

|---|---|---|---|

| id\_connexion | CHAR(36) | PK, NOT NULL | Identifiant technique |

| student\_code | VARCHAR(30) | NOT NULL, INDEX | Identifiant LMS |

| date\_connexion | DATETIME | NOT NULL, INDEX | Début de session |

| date\_deconnexion | DATETIME | NULL (anomalies attendues) | Fin de session |

| duree\_minutes | INT | NULL, \*\*PAS de CHECK\*\* (anomalies attendues) | Durée en minutes |

| appareil | VARCHAR(50) | NULL | Mobile, PC, Tablette |

| navigateur | VARCHAR(50) | NULL | Chrome, Firefox, Safari... |

| adresse\_ip | VARCHAR(45)

