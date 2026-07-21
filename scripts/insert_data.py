"""
insert_data.py — Insertion des donnees generees dans MySQL.

Lit les CSV produits par generate_data.py et les insere dans la base
edusmart_learning, en respectant :
  - l'ordre des dependances FK
  - l'insertion par batch (BATCH_SIZE lignes) pour la performance
  - les transactions (commit par batch, rollback en cas d'erreur)

Ordre d'insertion :
  1. modules
  2. cours (FK vers modules)
  3. quiz (FK vers cours)
  4. progression (FK vers modules + student_code externe)
  5. notes (FK vers quiz + student_code externe)
  6. temps_connexion (student_code externe uniquement)
"""

import csv
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mysql.connector
from mysql.connector import Error
from tqdm import tqdm

from config.db_config import DB_CONFIG, check_config
from config.generator_config import (
    BATCH_SIZE,
    CSV_MODULES,
    CSV_COURS,
    CSV_QUIZ,
    CSV_NOTES,
    CSV_PROGRESSION,
    CSV_TEMPS_CONNEXION,
    LOGS_DIR,
)


# --- Logs ---
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "insert_data.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================
# UTILITAIRES
# =============================================================

def read_csv(path):
    """Lit un CSV UTF-8 avec separateur ';' et retourne une liste de dicts."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def none_if_empty(value):
    """Convertit une chaine vide en None (pour les colonnes NULLables)."""
    return value if value != "" else None


def insert_with_batches(conn, table_name, sql, rows, columns_desc):
    """
    Insere une liste de tuples dans MySQL par batchs de BATCH_SIZE.
    Commit apres chaque batch, rollback + arret en cas d'erreur.
    """
    total = len(rows)
    logger.info(f"Insertion dans {table_name} : {total} lignes ({columns_desc})")

    cursor = conn.cursor()
    inserted = 0

    try:
        with tqdm(total=total, desc=f"  {table_name}", unit="lignes") as pbar:
            for i in range(0, total, BATCH_SIZE):
                batch = rows[i : i + BATCH_SIZE]
                cursor.executemany(sql, batch)
                conn.commit()
                inserted += len(batch)
                pbar.update(len(batch))
    except Error as e:
        conn.rollback()
        logger.error(f"ECHEC insertion dans {table_name} apres {inserted} lignes.")
        logger.error(f"Erreur MySQL : {e}")
        cursor.close()
        raise
    finally:
        cursor.close()

    logger.info(f"  {inserted} lignes inserees dans {table_name}.")


# =============================================================
# INSERTIONS - BLOC CATALOGUE
# =============================================================

def insert_modules(conn):
    rows_dict = read_csv(CSV_MODULES)
    rows = [
        (
            r["id_module"], r["code_module"], r["nom_module"], r["categorie"],
            r["niveau"], int(r["duree_heures"]), int(r["actif"]),
        )
        for r in rows_dict
    ]
    sql = """
        INSERT INTO modules
            (id_module, code_module, nom_module, categorie, niveau, duree_heures, actif)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    insert_with_batches(conn, "modules", sql, rows, "7 colonnes")


def insert_cours(conn):
    rows_dict = read_csv(CSV_COURS)
    rows = [
        (
            r["id_cours"], r["id_module"], r["titre"], int(r["ordre"]),
            int(r["duree_minutes"]), r["type_cours"], r["statut"],
        )
        for r in rows_dict
    ]
    sql = """
        INSERT INTO cours
            (id_cours, id_module, titre, ordre, duree_minutes, type_cours, statut)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    insert_with_batches(conn, "cours", sql, rows, "7 colonnes, code_cours_temp ignore")


def insert_quiz(conn):
    rows_dict = read_csv(CSV_QUIZ)
    rows = [
        (
            r["id_quiz"], r["id_cours"], r["titre"],
            int(r["nb_questions"]), float(r["score_max"]), int(r["duree_minutes"]),
        )
        for r in rows_dict
    ]
    sql = """
        INSERT INTO quiz
            (id_quiz, id_cours, titre, nb_questions, score_max, duree_minutes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    insert_with_batches(conn, "quiz", sql, rows, "6 colonnes, code_quiz_temp ignore")


# =============================================================
# INSERTIONS - BLOC ACTIVITE
# =============================================================

def insert_progression(conn):
    rows_dict = read_csv(CSV_PROGRESSION)
    rows = [
        (
            r["id_progression"],
            r["student_code"],
            r["id_module"],
            float(r["pourcentage"]),
            none_if_empty(r["dernier_cours"]),
            r["date_maj"],
        )
        for r in rows_dict
    ]
    sql = """
        INSERT INTO progression
            (id_progression, student_code, id_module, pourcentage, dernier_cours, date_maj)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    insert_with_batches(conn, "progression", sql, rows, "6 colonnes")


def insert_notes(conn):
    rows_dict = read_csv(CSV_NOTES)
    rows = [
        (
            r["id_note"],
            r["id_quiz"],
            r["student_code"],
            r["date_passage"],
            float(r["score"]),
            int(r["tentative"]),
            int(r["valide"]),
        )
        for r in rows_dict
    ]
    sql = """
        INSERT INTO notes
            (id_note, id_quiz, student_code, date_passage, score, tentative, valide)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    insert_with_batches(conn, "notes", sql, rows, "7 colonnes")


def insert_temps_connexion(conn):
    rows_dict = read_csv(CSV_TEMPS_CONNEXION)
    rows = [
        (
            r["id_connexion"],
            r["student_code"],
            r["date_connexion"],
            none_if_empty(r["date_deconnexion"]),
            int(r["duree_minutes"]) if r["duree_minutes"] else None,
            none_if_empty(r["appareil"]),
            none_if_empty(r["navigateur"]),
            none_if_empty(r["adresse_ip"]),
        )
        for r in rows_dict
    ]
    sql = """
        INSERT INTO temps_connexion
            (id_connexion, student_code, date_connexion, date_deconnexion,
             duree_minutes, appareil, navigateur, adresse_ip)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    insert_with_batches(conn, "temps_connexion", sql, rows, "8 colonnes")


# =============================================================
# MAIN
# =============================================================

def main():
    logger.info("=" * 60)
    logger.info("Insertion des donnees - CATALOGUE + ACTIVITE")
    logger.info("=" * 60)

    check_config()
    logger.info(f"Connexion a MySQL : {DB_CONFIG['user']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        logger.error(f"ECHEC de connexion : {e}")
        sys.exit(1)

    logger.info("Connexion etablie.")

    # Insertion dans l'ordre des dependances
    try:
        # Catalogue
        insert_modules(conn)
        insert_cours(conn)
        insert_quiz(conn)
        # Activite
        insert_progression(conn)
        insert_notes(conn)
        insert_temps_connexion(conn)
    except Error:
        logger.error("Arret du script suite a une erreur MySQL.")
        conn.close()
        sys.exit(1)

    # Verification finale
    logger.info("")
    logger.info("Verification post-insertion :")
    cursor = conn.cursor()
    for table in ["modules", "cours", "quiz", "progression", "notes", "temps_connexion"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logger.info(f"  {table:20s} : {count:>8d} lignes")
    cursor.close()

    conn.close()
    logger.info("")
    logger.info("=" * 60)
    logger.info("Insertion terminee avec succes.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()