\# EduSmart Learning — Source MySQL (Plateforme pédagogique)



\*\*Projet :\*\* EduSmart Decision Platform

\*\*Groupe :\*\* 2

\*\*Membre :\*\* Ndeye Penda SARR (Responsable MySQL, Cheffe de groupe)

\*\*Source :\*\* MySQL — Plateforme pédagogique (`edusmart\_learning`)



\---



\## Contexte



Ce module fait partie du projet \*\*EduSmart Decision Platform\*\*, dont l'objectif est de construire une plateforme décisionnelle unifiée à partir de cinq sources de données hétérogènes (PostgreSQL, MySQL, CSV, MongoDB, Redis).



Cette source MySQL représente la \*\*plateforme d'apprentissage en ligne\*\* d'EduSmart. Elle contient :



\- \*\*Catalogue pédagogique\*\* : modules, cours, quiz

\- \*\*Activité des étudiants\*\* : notes, progression, temps de connexion



\---



\## Chiffres-clés



| Élément | Valeur |

|---------|--------|

| Tables | 6 (InnoDB, utf8mb4) |

| Volume total | \*\*826 210 lignes\*\* |

| Étudiants LMS référencés | 10 000 |

| Modules | 200 |

| Cours | 2 305 |

| Quiz | 2 758 |

| Progressions | 66 919 |

| Notes | 378 512 |

| Sessions de connexion | 376 516 |

| Anomalies volontaires | \*\*126 515\*\* (\~15.3 %) |

| Tests automatisés | 30/30 (100 %) |

\---



\## Architecture technique



\### Schéma relationnel



6 tables reliées par 4 clés étrangères :



\- \*\*`modules`\*\* — Catalogue de modules pédagogiques (Data, IA, DevOps, etc.)

\- \*\*`cours`\*\* — Contenus pédagogiques (Vidéo, PDF, TP, Projet) → référence `modules`

\- \*\*`quiz`\*\* — Évaluations liées aux cours → référence `cours`

\- \*\*`notes`\*\* — Historique événementiel des tentatives de quiz → référence `quiz`

\- \*\*`progression`\*\* — Snapshot unique par (étudiant, module) → référence `modules`

\- \*\*`temps\_connexion`\*\* — Historique des sessions de connexion (indépendant)



Le diagramme MCD/MLD est disponible dans `docs/schema\_edusmart\_learning.png`.



\### Choix techniques



| Décision | Motivation |

|----------|------------|

| Moteur \*\*InnoDB\*\* | Support des FK et transactions |

| Encodage \*\*utf8mb4\*\* + collation \*\*utf8mb4\_unicode\_ci\*\* | Support Unicode complet |

| UUID stockés en \*\*CHAR(36)\*\* | Lisibilité debug > perf pure |

| \*\*FK ON DELETE/UPDATE RESTRICT\*\* | Protection stricte de l'intégrité |

| Aucune FK sur `student\_code` | Identifiant fonctionnel externe, pas une clé technique |

| CHECK volontairement omises sur `progression.pourcentage` et `temps\_connexion.duree\_minutes` | Permettre l'injection d'anomalies pédagogiques |



\---



\## Structure du dépôt



edusmart-mysql/

├── config/ # Configuration Python (chargement .env)

│ ├── db\_config.py

│ └── generator\_config.py # Paramètres de génération et anomalies

├── sql/

│ └── create\_database.sql # Script idempotent de création du schéma

├── scripts/

│ ├── test\_connection.py # Test de connexion MySQL

│ ├── generate\_data.py # Génération des données propres (seed 42)

│ ├── insert\_data.py # Insertion batch avec transactions

│ ├── export\_catalog.py # Export du catalogue pour le groupe

│ ├── build\_student\_codes.py # Dérivation des student\_codes depuis PostgreSQL

│ └── inject\_anomalies.py # Injection des 18 anomalies (seed 4242)

├── tests/

│ ├── init.py

│ └── test\_data\_quality.py # 30 tests automatisés

├── data/ # Fichiers CSV (NON versionnés)

├── docs/

│ ├── schema.md # Documentation du schéma

│ ├── schema\_edusmart\_learning.png

│ ├── schema\_edusmart\_learning.mwb

│ ├── anomalies.md # Catalogue des 18 anomalies

│ └── tests.md # Documentation des tests

├── logs/ # Logs d'exécution (NON versionnés)

├── .env # Secrets (NON versionné)

├── .env.example # Modèle de configuration

├── .gitignore

├── requirements.txt

└── README.md





\---



\## Installation



\### Prérequis

\- Python 3.12+ (testé sur 3.14.0)

\- MySQL Server 8.0.16 ou supérieur

\- Git



\### Mise en place



\*\*1. Cloner le dépôt :\*\*

```bash

git clone https://github.com/NdeyePendaSarr/edusmart-mysql.git

cd edusmart-mysql

```



\*\*2. Créer et activer l'environnement virtuel :\*\*

```bash

python -m venv venv

venv\\Scripts\\activate       # Windows

source venv/bin/activate    # macOS/Linux

```



\*\*3. Installer les dépendances :\*\*

```bash

pip install -r requirements.txt

```



\*\*4. Configurer les secrets :\*\*

```bash

copy .env.example .env      # Windows

cp .env.example .env        # macOS/Linux

```

Éditer `.env` avec les identifiants MySQL locaux.



\*\*5. Créer la base et l'utilisateur applicatif (via root) :\*\*

```sql

CREATE DATABASE edusmart\_learning CHARACTER SET utf8mb4 COLLATE utf8mb4\_unicode\_ci;

CREATE USER 'edusmart\_user'@'localhost' IDENTIFIED BY '<mot\_de\_passe>';

GRANT ALL PRIVILEGES ON edusmart\_learning.\* TO 'edusmart\_user'@'localhost';

FLUSH PRIVILEGES;

```



\---



\## Utilisation — Reproduction complète de la base



La procédure ci-dessous produit \*\*exactement\*\* l'état de référence : 823 314 lignes dont 126 306 anomalies documentées.



```bash

\# 1. Créer la structure des tables (idempotent : DROP TABLE + CREATE TABLE)

mysql -u root -p edusmart\_learning < sql/create\_database.sql



\# 2. Générer les données propres (seed 42)

python scripts/generate\_data.py



\# 3. Insérer les 820 770 lignes propres dans MySQL

python scripts/insert\_data.py



\# 4. Injecter les 18 anomalies volontaires (seed 4242)

python scripts/inject\_anomalies.py



\# 5. Valider avec la batterie de tests automatisés

python tests/test\_data\_quality.py

```



\*\*Résultat attendu :\*\* 30/30 tests réussis.



> ⚠️ Ne pas rejouer `inject\_anomalies.py` plusieurs fois sur la même base : certaines anomalies ajoutent des lignes (A7, A11), ce qui ferait croître le volume à chaque exécution. La procédure officielle est CREATE + INSERT + INJECT une seule fois.



\---



\## État d'avancement



\- \[x] \*\*Phase 1\*\* — Analyse et compréhension de la source

\- \[x] \*\*Phase 2\*\* — Préparation de l'environnement

\- \[x] \*\*Phase 3\*\* — Conception du schéma MySQL (6 tables, 4 FK, 8 CHECK)

\- \[x] \*\*Phase 4\*\* — Développement du générateur de données

&#x20;   - \[x] 4a — Bloc Catalogue (200 modules, 2 305 cours, 2 758 quiz)    - \[x] 4a-bis — Export catalogue pour partage inter-équipe

&#x20;   - \[x] 4b-préalable — Mapping student\_codes depuis PostgreSQL

&#x20;   - \[x] 4b — Bloc Activité (66 256 progressions, 376 629 notes, 376 516 connexions)

&#x20;   - \*\*Total inséré : 822 664 lignes\*\*- \[x] \*\*Phase 5\*\* — Introduction des anomalies

&#x20;   - \[x] Catalogue de \*\*18 anomalies\*\* documentées (`docs/anomalies.md`)

&#x20;   - \[x] Script `scripts/inject\_anomalies.py` reproductible (seed 4242)

&#x20;   - \[x] \*\*126 515 anomalies volontaires\*\* injectées (\~15.3 % de la base)

&#x20;   - \[x] A11 : violation FK explicite avec `foreign\_key\_checks = 0`

&#x20;   - \[x] A17 : gestion des collisions sur `UNIQUE(student\_code, id\_module)`

\- \[x] \*\*Phase 6\*\* — Insertion massive (réalisée en 4b)

\- \[x] \*\*Phase 7\*\* — Tests et validation

&#x20;   - \[x] Script `tests/test\_data\_quality.py` (30 tests automatisés)

&#x20;   - \[x] 6 tests de volumétrie stricts (100 %)

&#x20;   - \[x] 18 tests d'anomalies avec tolérance statistique (100 %)

&#x20;   - \[x] 6 tests d'intégrité relationnelle stricts (100 %)

\- \[x] \*\*Phase 8\*\* — Documentation et livraison



\---



\## Coordination groupe



\### Décisions arrêtées



\- \*\*Format `student\_code`\*\* : `LMS-XXXXXX` (préfixe LMS + 6 chiffres avec zéros non significatifs)

\- \*\*Règle de dérivation\*\* depuis PostgreSQL : `"LMS-" + matricule\[3:].zfill(6)` (ex. `ETU00001` → `LMS-000001`)

\- \*\*Fenêtre temporelle\*\* : 1er septembre 2024 → 30 juin 2026

\- \*\*10 000 étudiants uniques\*\* dérivés depuis les 10 100 lignes d'Aissata (100 doublons volontaires côté PostgreSQL)



\### Fichiers partagés avec le groupe (Google Drive)



| Fichier | Volume | Destinataires |

|---------|--------|---------------|

| `data/catalogue\_modules.csv` | 50 modules | Mouhameth (MongoDB), Seydina (Redis) |

| `data/catalogue\_cours\_quiz.csv` | 790 lignes | Mouhameth, Seydina |

| `data/student\_codes.csv` | 10 000 codes | Mouhameth, Seydina |



\---



\## Documentation complémentaire



\- \[`docs/schema.md`](docs/schema.md) — Détail des 6 tables, colonnes, contraintes

\- \[`docs/anomalies.md`](docs/anomalies.md) — Catalogue complet des 18 anomalies

\- \[`docs/tests.md`](docs/tests.md) — Documentation du script de qualité



\---



\## Contact



\*\*Ndeye Penda SARR\*\* — Cheffe de groupe

