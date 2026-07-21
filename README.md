\# EduSmart Learning — Source MySQL (Plateforme pédagogique)



\*\*Projet :\*\* EduSmart Decision Platform

\*\*Groupe :\*\* 2

\*\*Membre :\*\* Ndeye Penda SARR (Responsable MySQL, Cheffe de groupe)

\*\*Source :\*\* MySQL — Plateforme pédagogique (`edusmart\_learning`)



\---



\## Contexte



Ce module fait partie du projet EduSmart Decision Platform, dont l'objectif est de construire une plateforme décisionnelle unifiée à partir de cinq sources de données hétérogènes (PostgreSQL, MySQL, CSV, MongoDB, Redis).



Cette source MySQL représente la \*\*plateforme d'apprentissage en ligne\*\* d'EduSmart. Elle contient :



\- Le catalogue pédagogique : modules, cours, quiz

\- L'activité des étudiants : notes, progression, temps de connexion



\---



\## Structure du dépôt



edusmart-mysql/

├── config/         # Configuration Python (chargement .env)

├── sql/            # Scripts SQL (création de base, tables)

├── scripts/        # Scripts Python (génération et insertion)

├── data/           # Fichiers de données partagés (ex. student\_codes.csv)

├── docs/           # Documentation technique

├── logs/           # Logs d'exécution

├── .env            # Secrets (NON versionné)

├── .env.example    # Modèle de configuration

├── requirements.txt

└── README.md



\---



\## Installation



\### Prérequis

\- Python 3.12+ (testé sur 3.14.0)

\- MySQL Server 8.0.16 ou supérieur

\- Git



\### Mise en place



1\. Cloner le dépôt :

```bash

&#x20;  git clone <url-du-depot>

&#x20;  cd edusmart-mysql

```



2\. Créer et activer l'environnement virtuel :

```bash

&#x20;  python -m venv venv

&#x20;  venv\\Scripts\\activate   # Windows

&#x20;  source venv/bin/activate   # macOS/Linux

```



3\. Installer les dépendances :

```bash

&#x20;  pip install -r requirements.txt

```



4\. Configurer les secrets :

```bash

&#x20;  copy .env.example .env

```

&#x20;  Puis éditer `.env` avec les vraies valeurs.



\---



\## État d'avancement



\- \[x] Phase 1 — Analyse et compréhension de la source

\- \[x] Phase 2 — Préparation de l'environnement

\- \[x] Phase 3 — Conception du schéma MySQL

\- \[x] Phase 4 — Développement du générateur de données

&#x20;   - \[x] 4a — Bloc Catalogue (modules, cours, quiz) : 50 / 568 / 690 lignes

&#x20;   - \[x] 4a-bis — Export catalogue pour partage inter-équipe

&#x20;   - \[x] 4b-préalable — Mapping student\_codes depuis PostgreSQL (10 000 codes uniques dérivés)

&#x20;   - \[x] 4b — Bloc Activité : 66 268 progressions / 376 147 notes / 377 047 connexions

&#x20;   - \*\*Total inséré : 820 770 lignes en 2 min 13 s\*\*

\- \[ ] Phase 5 — Introduction des anomalies

\- \[ ] Phase 6 — Insertion massive (déjà réalisée en 4b)

\- \[ ] Phase 7 — Tests et validation

\- \[ ] Phase 8 — Documentation et livraison



\## Coordination groupe



\*\*Décisions arrêtées :\*\*

\- Format `student\_code` : `LMS-XXXXXX` (préfixe LMS + 6 chiffres avec zéros non significatifs)

\- Règle de dérivation depuis PostgreSQL : `LMS-` + `matricule\[3:].zfill(6)` (ex. `ETU00001` → `LMS-000001`)

\- Fenêtre temporelle : 1er septembre 2024 → 30 juin 2026

\- 10 000 étudiants uniques (dérivés depuis les 10 100 lignes d'Aissata, incluant 100 doublons volontaires)



\*\*Fichiers partagés avec le groupe :\*\*

\- `data/catalogue\_modules.csv` (50 modules)

\- `data/catalogue\_cours\_quiz.csv` (568 cours + 690 quiz)

\- `data/student\_codes.csv` (10 000 codes uniques)



\## Coordination groupe



\*\*Décisions arrêtées :\*\*

\- Format `student\_code` : `LMS-XXXXXX` (préfixe LMS + 6 chiffres avec zéros non significatifs), dérivé du matricule PostgreSQL par Aissata.

\- Fenêtre temporelle : 1er septembre 2024 → 30 juin 2026.



\*\*En attente :\*\*

\- Fichier d'Aissata (PostgreSQL) mis à jour avec colonne `student\_code`.





\## Contact



Ndeye Penda SARR — Cheffe de groupe

