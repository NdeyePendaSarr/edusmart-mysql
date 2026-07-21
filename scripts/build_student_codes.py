"""
build_student_codes.py — Derive les student_codes depuis le fichier
etudiants_postgres.csv d'Aissata.

Regle de mapping (definie par MySQL, source consommatrice) :
    ETU00001 -> LMS-000001
    ETU10100 -> LMS-010100

Formule Python : "LMS-" + matricule[3:].zfill(6)

Produit deux fichiers dans data/ :
  - student_codes.csv                  (colonne : student_code)
      -> a partager avec Mouhameth (MongoDB) et Seydina (Redis)
  - mapping_matricule_student_code.csv (matricule + student_code)
      -> archive interne pour la tracabilite

Verifications effectuees :
  - format du matricule (ETU + 5 chiffres)
  - detection des doublons de matricules
  - detection des matricules invalides ou vides
"""

import csv
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.generator_config import DATA_DIR, LOGS_DIR


# --- Chemins ---
INPUT_FILE = DATA_DIR / "etudiants_postgres.csv"
OUTPUT_STUDENT_CODES = DATA_DIR / "student_codes.csv"
OUTPUT_MAPPING = DATA_DIR / "mapping_matricule_student_code.csv"

# Format attendu : ETU suivi d'exactement 5 chiffres
MATRICULE_PATTERN = re.compile(r"^ETU(\d{5})$")


# --- Logs ---
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "build_student_codes.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def matricule_to_student_code(matricule):
    """
    Applique la regle de mapping : ETU00001 -> LMS-000001.

    Retourne None si le matricule ne suit pas le format attendu.
    """
    if not matricule:
        return None
    match = MATRICULE_PATTERN.match(matricule.strip())
    if not match:
        return None
    numero = match.group(1)  # 5 chiffres (groupe capturant de la regex)
    return f"LMS-{numero.zfill(6)}"


def main():
    logger.info("=" * 60)
    logger.info("Derivation des student_codes depuis PostgreSQL (Aissata)")
    logger.info("=" * 60)

    # Verification prealable
    if not INPUT_FILE.exists():
        logger.error(f"Fichier introuvable : {INPUT_FILE}")
        logger.error("Verifie que le fichier d'Aissata est bien copie dans :")
        logger.error(f"  {INPUT_FILE}")
        sys.exit(1)

    # Lecture du fichier source
    logger.info(f"Lecture : {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    logger.info(f"  {len(rows)} lignes lues.")

    # Verification que la colonne matricule existe
    if not rows or "matricule" not in rows[0]:
        logger.error("La colonne 'matricule' n'a pas ete trouvee dans le fichier.")
        logger.error(f"Colonnes disponibles : {list(rows[0].keys()) if rows else 'aucune'}")
        sys.exit(1)

    # Application du mapping avec verifications
    mapping = []
    codes_generes = []
    matricules_invalides = []
    matricules_vus = set()
    doublons_matricule = []

    for row in rows:
        matricule = row.get("matricule", "").strip()

        # Detection des doublons de matricule
        if matricule in matricules_vus:
            doublons_matricule.append(matricule)
            continue
        matricules_vus.add(matricule)

        # Conversion
        code = matricule_to_student_code(matricule)
        if code is None:
            matricules_invalides.append(matricule if matricule else "(vide)")
            continue

        mapping.append({"matricule": matricule, "student_code": code})
        codes_generes.append(code)

    # --- Rapport de qualite ---
    logger.info("")
    logger.info("Bilan de la derivation :")
    logger.info(f"  Lignes lues                : {len(rows)}")
    logger.info(f"  student_codes generes      : {len(codes_generes)}")
    logger.info(f"  Matricules invalides       : {len(matricules_invalides)}")
    logger.info(f"  Doublons de matricules     : {len(doublons_matricule)}")

    if matricules_invalides:
        logger.warning(f"  Exemples invalides : {matricules_invalides[:5]}")
    if doublons_matricule:
        logger.warning(f"  Exemples doublons  : {doublons_matricule[:5]}")

    # Verification unicite des codes produits
    if len(set(codes_generes)) != len(codes_generes):
        logger.error("ATTENTION : des student_codes en double ont ete generes !")

    # --- Ecriture des fichiers ---
    logger.info("")
    logger.info("Ecriture des fichiers...")

    # Fichier 1 : student_codes.csv (a partager)
    with open(OUTPUT_STUDENT_CODES, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["student_code"])
        for code in codes_generes:
            writer.writerow([code])
    logger.info(f"  Ecrit : {OUTPUT_STUDENT_CODES.name} ({len(codes_generes)} codes)")

    # Fichier 2 : mapping (tracabilite)
    with open(OUTPUT_MAPPING, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["matricule", "student_code"], delimiter=";"
        )
        writer.writeheader()
        writer.writerows(mapping)
    logger.info(f"  Ecrit : {OUTPUT_MAPPING.name} ({len(mapping)} correspondances)")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Fichiers pretes a etre partages :")
    logger.info(f"  student_codes.csv                  -> Mouhameth + Seydina")
    logger.info(f"  mapping_matricule_student_code.csv -> archive interne")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()