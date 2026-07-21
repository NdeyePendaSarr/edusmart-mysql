"""
generate_data.py — Generation des donnees pour edusmart_learning.

Ce script produit les donnees de la source MySQL EN MEMOIRE, puis
les ecrit dans des fichiers CSV dans le dossier data/.

Etat actuel : BLOC CATALOGUE uniquement (modules, cours, quiz).
Le bloc Activite (notes, progression, temps_connexion) sera
implemente en 4.3 apres reception des student_codes d'Aissata.

Principes appliques :
  - Reproductibilite : seed fixe (Faker + random)
  - Aucune anomalie a ce stade : les donnees sont propres.
    Les anomalies seront introduites en Phase 5 via un script dedie.
  - Separation generation / insertion : ce script ne parle PAS a MySQL.
    Il produit des CSV lus ensuite par insert_data.py.
"""

import csv
import logging
import random
import sys
import uuid
from pathlib import Path

# --- Ajout de la racine du projet au PYTHONPATH ---
# Permet a Python de trouver le module 'config' depuis scripts/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faker import Faker

from config.generator_config import (
    SEED,
    FAKER_LOCALE,
    NB_MODULES,
    COURS_PAR_MODULE_MIN,
    COURS_PAR_MODULE_MAX,
    PROBA_QUIZ_PAR_COURS,
    QUIZ_PAR_COURS_MAX,
    CATEGORIES_MODULES,
    NIVEAUX,
    TYPES_COURS,
    PREFIX_MODULE,
    PREFIX_COURSE,
    PREFIX_QUIZ,
    CSV_MODULES,
    CSV_COURS,
    CSV_QUIZ,
    DATA_DIR,
    LOGS_DIR,
)


# =============================================================
# CONFIGURATION DES LOGS
# =============================================================

LOGS_DIR.mkdir(exist_ok=True)  # cree logs/ s'il n'existe pas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "generate_data.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================
# INITIALISATION FAKER + RANDOM
# =============================================================

fake = Faker(FAKER_LOCALE)
Faker.seed(SEED)
random.seed(SEED)


# =============================================================
# GENERATION : MODULES
# =============================================================

def generate_modules():
    """
    Genere NB_MODULES modules avec :
      - un UUID unique (id_module)
      - un code metier unique (MOD-CAT-XX)
      - une categorie parmi CATEGORIES_MODULES
      - un niveau parmi NIVEAUX
      - une duree entre 20 et 120 heures
      - un flag actif (95 % actifs a ce stade, sans anomalies)

    Retourne : list[dict], une entree par module.
    """
    logger.info(f"Generation de {NB_MODULES} modules...")

    modules = []
    for i in range(1, NB_MODULES + 1):
        categorie = random.choice(CATEGORIES_MODULES)
        # Code metier : abreviation de la categorie + numero sur 2 chiffres
        # Ex: MOD-DEV-01, MOD-DAT-05, MOD-IA-12
        abrev = categorie[:3].upper().replace(" ", "").replace("/", "")
        code = f"{PREFIX_MODULE}-{abrev}-{i:02d}"

        module = {
            "id_module": str(uuid.uuid4()),
            "code_module": code,
            "nom_module": fake.catch_phrase(),  # nom "commercial" court
            "categorie": categorie,
            "niveau": random.choice(NIVEAUX),
            "duree_heures": random.randint(20, 120),
            "actif": 1,  # tous actifs a ce stade (anomalies en Phase 5)
        }
        modules.append(module)

    logger.info(f"  {len(modules)} modules generes.")
    return modules


# =============================================================
# GENERATION : COURS
# =============================================================

def generate_cours(modules):
    """
    Pour chaque module, genere un nombre aleatoire de cours entre
    COURS_PAR_MODULE_MIN et COURS_PAR_MODULE_MAX.

    Chaque cours est numerote (ordre 1, 2, 3...) dans son module.

    Retourne : list[dict].
    """
    logger.info("Generation des cours...")

    cours_list = []
    global_counter = 1  # pour code metier COURSE-0001, COURSE-0002, ...

    for module in modules:
        nb_cours = random.randint(COURS_PAR_MODULE_MIN, COURS_PAR_MODULE_MAX)
        for ordre in range(1, nb_cours + 1):
            cours = {
                "id_cours": str(uuid.uuid4()),
                "id_module": module["id_module"],
                "code_cours_temp": f"{PREFIX_COURSE}-{global_counter:04d}",
                "titre": fake.sentence(nb_words=5).rstrip("."),
                "ordre": ordre,
                "duree_minutes": random.randint(15, 180),
                "type_cours": random.choice(TYPES_COURS),
                "statut": "PUBLIE",
            }
            cours_list.append(cours)
            global_counter += 1

    logger.info(f"  {len(cours_list)} cours generes (sur {len(modules)} modules).")
    return cours_list


# =============================================================
# GENERATION : QUIZ
# =============================================================

def generate_quiz(cours_list):
    """
    Pour chaque cours, avec une probabilite PROBA_QUIZ_PAR_COURS,
    genere entre 1 et QUIZ_PAR_COURS_MAX quiz.

    Certains cours n'auront donc aucun quiz (c'est realiste).

    Retourne : list[dict].
    """
    logger.info("Generation des quiz...")

    quiz_list = []
    global_counter = 1

    for cours in cours_list:
        # Tirage : ce cours a-t-il des quiz ?
        if random.random() > PROBA_QUIZ_PAR_COURS:
            continue

        # Combien de quiz pour ce cours ?
        nb_quiz = random.randint(1, QUIZ_PAR_COURS_MAX)
        for _ in range(nb_quiz):
            nb_questions = random.randint(5, 30)
            # score_max coherent : ~1 point par question (arrondi a 2 dec.)
            score_max = round(nb_questions * random.uniform(0.8, 1.2), 2)
            # duree coherente : ~1 min par question, +/- 50 %
            duree = int(nb_questions * random.uniform(0.5, 1.5))
            duree = max(duree, 5)  # au moins 5 min

            quiz = {
                "id_quiz": str(uuid.uuid4()),
                "id_cours": cours["id_cours"],
                "code_quiz_temp": f"{PREFIX_QUIZ}-{global_counter:04d}",
                "titre": f"Quiz {fake.word().capitalize()}",
                "nb_questions": nb_questions,
                "score_max": score_max,
                "duree_minutes": duree,
            }
            quiz_list.append(quiz)
            global_counter += 1

    logger.info(f"  {len(quiz_list)} quiz generes.")
    return quiz_list


# =============================================================
# ECRITURE EN CSV
# =============================================================

def write_csv(path, data, fieldnames):
    """Ecrit une liste de dicts dans un CSV UTF-8 avec separateur ';'."""
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"  Ecrit : {path} ({len(data)} lignes)")


# =============================================================
# MAIN
# =============================================================

def main():
    logger.info("=" * 60)
    logger.info("Generation des donnees - BLOC CATALOGUE")
    logger.info("=" * 60)

    # Etape 1 : generation en memoire
    modules = generate_modules()
    cours_list = generate_cours(modules)
    quiz_list = generate_quiz(cours_list)

    # Etape 2 : ecriture des CSV
    logger.info("\nEcriture des fichiers CSV...")

    write_csv(
        CSV_MODULES,
        modules,
        fieldnames=[
            "id_module", "code_module", "nom_module", "categorie",
            "niveau", "duree_heures", "actif",
        ],
    )

    write_csv(
        CSV_COURS,
        cours_list,
        fieldnames=[
            "id_cours", "id_module", "code_cours_temp", "titre",
            "ordre", "duree_minutes", "type_cours", "statut",
        ],
    )

    write_csv(
        CSV_QUIZ,
        quiz_list,
        fieldnames=[
            "id_quiz", "id_cours", "code_quiz_temp", "titre",
            "nb_questions", "score_max", "duree_minutes",
        ],
    )

    # Etape 3 : bilan
    logger.info("\n" + "=" * 60)
    logger.info("BILAN")
    logger.info("=" * 60)
    logger.info(f"  Modules  : {len(modules)}")
    logger.info(f"  Cours    : {len(cours_list)}")
    logger.info(f"  Quiz     : {len(quiz_list)}")
    logger.info(f"  Fichiers ecrits dans : {DATA_DIR}")
    logger.info("=" * 60)
    logger.info("Generation terminee avec succes.")


if __name__ == "__main__":
    main()