"""
export_catalog.py — Extract du catalogue pour partage avec le groupe.

Produit deux fichiers dans data/ :
  - catalogue_modules.csv   (id_module + code_module + nom + categorie)
  - catalogue_cours_quiz.csv (code_module + code_cours + code_quiz + titres)

Ces fichiers permettent a Mouhameth (MongoDB) et Seydina (Redis) de
referencer les codes du catalogue pedagogique dans leurs sources.

A regenerer apres chaque nouvelle generation de donnees.
"""

import csv
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.generator_config import (
    CSV_MODULES,
    CSV_COURS,
    CSV_QUIZ,
    DATA_DIR,
    LOGS_DIR,
)

# --- Logs ---
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "export_catalog.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def read_csv(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def main():
    logger.info("=" * 60)
    logger.info("Export du catalogue pour le groupe")
    logger.info("=" * 60)

    # Lecture des CSV sources
    modules = read_csv(CSV_MODULES)
    cours = read_csv(CSV_COURS)
    quiz = read_csv(CSV_QUIZ)

    # Index rapides
    modules_by_id = {m["id_module"]: m for m in modules}
    cours_by_id = {c["id_cours"]: c for c in cours}

    # --- Fichier 1 : catalogue_modules.csv ---
    export_modules_path = DATA_DIR / "catalogue_modules.csv"
    with open(export_modules_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["code_module", "nom_module", "categorie", "niveau"])
        for m in modules:
            writer.writerow([m["code_module"], m["nom_module"], m["categorie"], m["niveau"]])
    logger.info(f"  Ecrit : {export_modules_path} ({len(modules)} modules)")

    # --- Fichier 2 : catalogue_cours_quiz.csv ---
    export_cours_quiz_path = DATA_DIR / "catalogue_cours_quiz.csv"
    with open(export_cours_quiz_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "code_module", "code_cours", "titre_cours", "type_cours",
            "code_quiz", "titre_quiz"
        ])

        # Pour chaque cours, on ecrit une ligne (avec quiz si present)
        # Sinon, une ligne avec les colonnes quiz vides
        quiz_by_cours = {}
        for q in quiz:
            quiz_by_cours.setdefault(q["id_cours"], []).append(q)

        nb_lignes = 0
        for c in cours:
            module = modules_by_id[c["id_module"]]
            quizzes = quiz_by_cours.get(c["id_cours"], [])
            if quizzes:
                for q in quizzes:
                    writer.writerow([
                        module["code_module"],
                        c["code_cours_temp"],
                        c["titre"],
                        c["type_cours"],
                        q["code_quiz_temp"],
                        q["titre"],
                    ])
                    nb_lignes += 1
            else:
                writer.writerow([
                    module["code_module"],
                    c["code_cours_temp"],
                    c["titre"],
                    c["type_cours"],
                    "",  # pas de quiz
                    "",
                ])
                nb_lignes += 1

    logger.info(f"  Ecrit : {export_cours_quiz_path} ({nb_lignes} lignes)")

    logger.info("=" * 60)
    logger.info("Export termine. Ces fichiers peuvent etre partages avec :")
    logger.info("  - Mouhameth (MongoDB) : pour les module_code / course_code / quiz_code")
    logger.info("  - Seydina (Redis)     : pour les last_course et progress:{code}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()