"""
insert_data.py — Insertion des donnees generees dans MySQL.

Lit les CSV produits par generate_data.py et les insere dans la base
edusmart_learning, en respectant :
  - l'ordre des dependances FK (modules puis cours puis quiz)
  - l'insertion par batch (BATCH_SIZE lignes) pour la performance
  - les transactions (commit par batch, rollback en cas d'erreur)

Etat actuel : BLOC CATALOGUE (modules, cours, quiz).
Le bloc Activite sera ajoute en 4.4 apres reception des student_codes.
"""

import csv
import logging
import sys
from pathlib import Path

# --- Racine du projet pour les imports ---
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
    LOGS_DIR,
)


# =============================================================
# LOGGING
# =============================================================

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
# UTILITAIRES D'INSERTION
# =============================================================

def read_csv(path):
    """Lit un CSV UTF-8 avec separateur ';' et retourne une liste de dicts."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def insert_batch(cursor, sql, rows):
    """Execute une insertion batch avec executemany."""
    cursor.executemany(sql, rows)


def insert_with_batches(conn, table_name, sql, rows, columns_desc):
    """
    Insere une liste de tuples dans MySQL par batchs de BATCH_SIZE,
    avec commit apres chaque batch et barre de progression tqdm.

    En cas d'erreur, rollback du batch en cours et arret du script.
    """
    total = len(rows)
    logger.info(f"Insertion dans {table_name} : {total} lignes ({columns_desc})")

    cursor = conn.cursor()
    inserted = 0

    try:
        # tqdm : barre de progression visible dans la console
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
# INSERTIONS PAR TABLE
# =============================================================

def insert_modules(conn):
    """Insere les modules depuis modules.csv."""
    rows_dict = read_csv(CSV_MODULES)

    # Conversion en tuples ordonnes selon le SQL
    rows = [
        (
            r["id_module"],
            r["code_module"],
            r["nom_module"],
            r["categorie"],
            r["niveau"],
            int(r["duree_heures"]),
            int(r["actif"]),
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
    """Insere les cours depuis cours.csv (sans la colonne code_cours_temp)."""
    rows_dict = read_csv(CSV_COURS)

    rows = [
        (
            r["id_cours"],
            r["id_module"],
            r["titre"],
            int(r["ordre"]),
            int(r["duree_minutes"]),
            r["type_cours"],
            r["statut"],
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
    """Insere les quiz depuis quiz.csv (sans la colonne code_quiz_temp)."""
    rows_dict = read_csv(CSV_QUIZ)

    rows = [
        (
            r["id_quiz"],
            r["id_cours"],
            r["titre"],
            int(r["nb_questions"]),
            float(r["score_max"]),
            int(r["duree_minutes"]),
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
# MAIN
# =============================================================

def main():
    logger.info("=" * 60)
    logger.info("Insertion des donnees - BLOC CATALOGUE")
    logger.info("=" * 60)

    # Etape 1 : verifier la config et se connecter
    check_config()
    logger.info(f"Connexion a MySQL : {DB_CONFIG['user']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        logger.error(f"ECHEC de connexion : {e}")
        sys.exit(1)

    logger.info("Connexion etablie.")

    # Etape 2 : inserer dans l'ordre des dependances FK
    try:
        insert_modules(conn)
        insert_cours(conn)
        insert_quiz(conn)
    except Error as e:
        logger.error(f"Arret du script suite a une erreur MySQL.")
        conn.close()
        sys.exit(1)

    # Etape 3 : verification finale
    logger.info("\nVerification post-insertion :")
    cursor = conn.cursor()
    for table in ["modules", "cours", "quiz"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logger.info(f"  {table:15s} : {count} lignes")
    cursor.close()

    conn.close()
    logger.info("\n" + "=" * 60)
    logger.info("Insertion terminee avec succes.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()