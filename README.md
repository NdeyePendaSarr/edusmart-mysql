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

\- \[ ] Phase 3 — Conception du schéma MySQL

\- \[ ] Phase 4 — Développement du générateur de données

\- \[ ] Phase 5 — Introduction des anomalies

\- \[ ] Phase 6 — Insertion massive

\- \[ ] Phase 7 — Tests et validation

\- \[ ] Phase 8 — Documentation et livraison



\---



\## Contact



Ndeye Penda SARR — Cheffe de groupe

