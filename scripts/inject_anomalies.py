"""
inject_anomalies.py — Introduction volontaire d'anomalies dans les donnees.

Ce script AGIT DIRECTEMENT sur la base MySQL edusmart_learning.
Il modifie / ajoute des donnees pour simuler les imperfections typiques
d'un environnement reel :

  - erreurs de saisie (orthographes multiples, casses variees)
  - valeurs hors bornes (scores > max, pourcentages > 100)
  - references orphelines (student_code fantomes, dernier_cours inexistant)
  - donnees manquantes (deconnexions non enregistrees, IP invalides)
  - doublons pedagogiques

Architecture :
  - Une fonction par anomalie, nommee inject_A<numero>_<description>()
  - Chaque fonction retourne le nombre de lignes affectees
  - Le main() les orchestre et produit un rapport final
  - Toutes les fonctions utilisent SEED_ANOMALIES pour la reproductibilite

IMPORTANT : ce script doit etre execute APRES generate_data.py + insert_data.py
sur une base propre. Le rejouer une seconde fois amplifierait les anomalies.
"""

import logging
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mysql.connector
from mysql.connector import Error

from config.db_config import DB_CONFIG, check_config
from config.generator_config import (
    # Seed dedie
    SEED_ANOMALIES,
    # Anomalies modules
    TAUX_MODULES_INACTIFS,
    VARIANTES_CATEGORIES,
    # Anomalies cours
    TAUX_COURS_DOUBLONS_TITRE,
    VARIANTES_TYPE_COURS,
    # Anomalies quiz
    TAUX_QUIZ_DUREE_INCOHERENTE,
    # Anomalies notes
    TAUX_NOTES_SCORE_SUPERIEUR,
    TAUX_NOTES_DOUBLONS,
    # Anomalies progression
    TAUX_PROGRESSION_SUP_100,
    TAUX_PROGRESSION_NEGATIF,
    TAUX_PROGRESSION_COURS_FANTOME,
    TAUX_PROGRESSION_MODULE_FANTOME,
    # Anomalies temps_connexion
    TAUX_CONNEXION_SANS_DECONNEXION,
    TAUX_CONNEXION_DUREE_NEGATIVE,
    TAUX_CONNEXION_IP_INVALIDE,
    TAUX_CONNEXION_APPAREIL_VARIANTE,
    TAUX_CONNEXION_DATES_INVERSEES,
    VARIANTES_APPAREILS,
    IP_INVALIDES,
    # Anomalies transversales
    TAUX_STUDENT_CODE_FANTOME,
    TAUX_NULL_COLONNES_NULLABLES,
    CODES_FANTOMES_PREFIX,
    # Utilitaires
    LOGS_DIR,
    BATCH_SIZE,
)


# =============================================================
# LOGGING
# =============================================================

LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "inject_anomalies.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================
# INITIALISATION RANDOM (seed dedie aux anomalies)
# =============================================================

random.seed(SEED_ANOMALIES)


# =============================================================
# UTILITAIRES
# =============================================================

def fetch_all_ids(conn, table, id_column):
    """Recupere tous les identifiants d'une table (liste)."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT {id_column} FROM {table}")
    ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return ids


def sample_ids(ids, taux):
    """
    Selectionne aleatoirement un echantillon d'IDs selon un taux (0.0 - 1.0).
    Retourne : liste des IDs echantillonnes.
    """
    nb = int(round(len(ids) * taux))
    return random.sample(ids, nb) if nb > 0 else []


def execute_update_batch(conn, sql, params_list, label):
    """
    Execute un UPDATE (ou INSERT) sur une liste de parametres, par batch.
    Commit apres chaque batch, rollback en cas d'erreur.
    """
    if not params_list:
        logger.info(f"    {label} : 0 lignes affectees.")
        return 0

    cursor = conn.cursor()
    affected = 0
    try:
        for i in range(0, len(params_list), BATCH_SIZE):
            batch = params_list[i : i + BATCH_SIZE]
            cursor.executemany(sql, batch)
            conn.commit()
            affected += cursor.rowcount
    except Error as e:
        conn.rollback()
        logger.error(f"    ECHEC {label} : {e}")
        raise
    finally:
        cursor.close()

    logger.info(f"    {label} : {affected} lignes affectees.")
    return affected


# =============================================================
# FONCTIONS D'ANOMALIES (a completer aux etapes suivantes)
# =============================================================


# =============================================================
# ANOMALIES : table modules
# =============================================================

def inject_A1_categories_desordonnees(conn):
    """
    A1 : remplace les categories propres par des variantes desordonnees.
    Chaque module voit sa categorie potentiellement remplacee par une
    variante orthographique (ex. 'Data Science' -> 'DATA', 'data science').

    Taux : environ 60 % des modules sont affectes (variantes tirees).
    """
    logger.info("A1 : Categories mal standardisees dans modules...")

    cursor = conn.cursor()
    cursor.execute("SELECT id_module, categorie FROM modules")
    rows = cursor.fetchall()
    cursor.close()

    updates = []
    for id_module, categorie_propre in rows:
        # 60 % de chance qu'un module recoive une variante
        if random.random() < 0.60:
            variantes = VARIANTES_CATEGORIES.get(categorie_propre)
            if variantes:
                variante = random.choice(variantes)
                updates.append((variante, id_module))

    sql = "UPDATE modules SET categorie = %s WHERE id_module = %s"
    return execute_update_batch(conn, sql, updates, "A1 categories")


def inject_A2_modules_inactifs(conn):
    """
    A2 : passe TAUX_MODULES_INACTIFS des modules a actif=0.
    Simule des modules retires du catalogue mais non supprimes.
    """
    logger.info("A2 : Modules inactifs...")

    ids = fetch_all_ids(conn, "modules", "id_module")
    ids_a_desactiver = sample_ids(ids, TAUX_MODULES_INACTIFS)

    updates = [(id_module,) for id_module in ids_a_desactiver]
    sql = "UPDATE modules SET actif = 0 WHERE id_module = %s"
    return execute_update_batch(conn, sql, updates, "A2 inactifs")

# =============================================================
# ANOMALIES : tables cours et quiz
# =============================================================

def inject_A3_cours_doublons_titre(conn):
    """
    A3 : duplique le titre de TAUX_COURS_DOUBLONS_TITRE des cours
    en le remplacant par le titre d'un AUTRE cours du meme module.

    Ne cree pas de nouvelles lignes -- modifie juste le titre existant.
    Le meme titre apparaitra donc pour 2 cours differents.
    """
    logger.info("A3 : Doublons de titres dans cours...")

    cursor = conn.cursor()
    cursor.execute("SELECT id_cours, id_module, titre FROM cours")
    all_cours = cursor.fetchall()
    cursor.close()

    # Groupe les cours par module (pour piocher un titre du meme module)
    from collections import defaultdict
    cours_par_module = defaultdict(list)
    for id_cours, id_module, titre in all_cours:
        cours_par_module[id_module].append((id_cours, titre))

    # Selectionne les cours a "doublonner"
    ids_a_doublonner = sample_ids(
        [c[0] for c in all_cours],
        TAUX_COURS_DOUBLONS_TITRE
    )
    map_id_module = {c[0]: c[1] for c in all_cours}

    updates = []
    for id_cible in ids_a_doublonner:
        id_module = map_id_module[id_cible]
        candidats = [
            (id_c, titre) for id_c, titre in cours_par_module[id_module]
            if id_c != id_cible
        ]
        if not candidats:
            continue  # module d'un seul cours : pas de doublon possible
        _, titre_source = random.choice(candidats)
        updates.append((titre_source, id_cible))

    sql = "UPDATE cours SET titre = %s WHERE id_cours = %s"
    return execute_update_batch(conn, sql, updates, "A3 doublons titres")


def inject_A4_type_cours_variantes(conn):
    """
    A4 : remplace le type_cours propre par une variante orthographique
    pour TAUX_CONNEXION_APPAREIL_VARIANTE des cours.

    Ex : 'Video' -> 'video' ou 'VIDEO'
         'PDF'   -> 'pdf' ou 'Pdf'
    """
    logger.info("A4 : Variantes de type_cours...")

    ids = fetch_all_ids(conn, "cours", "id_cours")
    ids_a_modifier = sample_ids(ids, 0.10)  # 10 %

    updates = [
        (random.choice(VARIANTES_TYPE_COURS), id_cours)
        for id_cours in ids_a_modifier
    ]

    sql = "UPDATE cours SET type_cours = %s WHERE id_cours = %s"
    return execute_update_batch(conn, sql, updates, "A4 type_cours variantes")


def inject_A5_quiz_duree_incoherente(conn):
    """
    A5 : donne une duree incoherente a TAUX_QUIZ_DUREE_INCOHERENTE des quiz.
    Les valeurs choisies sont manifestement absurdes :
      - soit tres courtes (1 minute) : impossible de repondre a 20 questions
      - soit tres longues (240+ minutes) : 4 heures pour un quiz de 5 questions
    """
    logger.info("A5 : Durees incoherentes dans quiz...")

    ids = fetch_all_ids(conn, "quiz", "id_quiz")
    ids_a_modifier = sample_ids(ids, TAUX_QUIZ_DUREE_INCOHERENTE)

    updates = []
    for id_quiz in ids_a_modifier:
        # Une chance sur deux : trop court ou trop long
        if random.random() < 0.5:
            duree = random.randint(1, 2)
        else:
            duree = random.randint(240, 480)
        updates.append((duree, id_quiz))

    sql = "UPDATE quiz SET duree_minutes = %s WHERE id_quiz = %s"
    return execute_update_batch(conn, sql, updates, "A5 durees incoherentes")

# =============================================================
# ANOMALIES : table notes
# =============================================================

def inject_A6_notes_score_superieur(conn):
    """
    A6 : donne un score > score_max du quiz a TAUX_NOTES_SCORE_SUPERIEUR
    des notes. Simule une erreur de saisie ou un bug de scoring.
    """
    logger.info("A6 : Scores superieurs au score_max...")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.id_note, q.score_max
        FROM notes n
        INNER JOIN quiz q ON q.id_quiz = n.id_quiz
    """)
    all_notes = cursor.fetchall()
    cursor.close()

    ids_a_modifier = sample_ids(
        [n[0] for n in all_notes],
        TAUX_NOTES_SCORE_SUPERIEUR
    )
    map_score_max = {n[0]: float(n[1]) for n in all_notes}

    updates = []
    for id_note in ids_a_modifier:
        score_max = map_score_max[id_note]
        score_absurde = round(score_max + random.uniform(1, 20), 2)
        updates.append((score_absurde, id_note))

    sql = "UPDATE notes SET score = %s WHERE id_note = %s"
    return execute_update_batch(conn, sql, updates, "A6 scores > max")


def inject_A7_notes_doublons(conn):
    """
    A7 : cree TAUX_NOTES_DOUBLONS de doublons parfaits
    (meme student_code, meme id_quiz, meme tentative, meme date, meme score).

    Contrairement a A6 qui MODIFIE des lignes, A7 en INSERE de nouvelles.
    """
    logger.info("A7 : Doublons dans notes...")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_quiz, student_code, date_passage, score, tentative, valide
        FROM notes
    """)
    all_notes = cursor.fetchall()
    cursor.close()

    nb_doublons = int(round(len(all_notes) * TAUX_NOTES_DOUBLONS))
    notes_a_dupliquer = random.sample(all_notes, nb_doublons)

    inserts = []
    for id_quiz, student_code, date_passage, score, tentative, valide in notes_a_dupliquer:
        nouveau_id = str(uuid.uuid4())
        inserts.append((
            nouveau_id, id_quiz, student_code, date_passage,
            float(score), int(tentative), int(valide)
        ))

    sql = """
        INSERT INTO notes
            (id_note, id_quiz, student_code, date_passage, score, tentative, valide)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    return execute_update_batch(conn, sql, inserts, "A7 doublons")

# =============================================================
# ANOMALIES : table progression
# =============================================================

def inject_A8_progression_sup_100(conn):
    """
    A8 : donne un pourcentage > 100 (entre 101 et 150) a TAUX_PROGRESSION_SUP_100
    des lignes. Ce genre d'anomalie survient a cause de bugs de calcul cote application
    (division par zero, arrondi, cumul incorrect).
    """
    logger.info("A8 : Progressions > 100 %...")

    ids = fetch_all_ids(conn, "progression", "id_progression")
    ids_a_modifier = sample_ids(ids, TAUX_PROGRESSION_SUP_100)

    updates = [
        (round(random.uniform(101, 150), 2), id_progression)
        for id_progression in ids_a_modifier
    ]

    sql = "UPDATE progression SET pourcentage = %s WHERE id_progression = %s"
    return execute_update_batch(conn, sql, updates, "A8 progression > 100")


def inject_A9_progression_negatif(conn):
    """
    A9 : donne un pourcentage negatif (entre -50 et -1) a TAUX_PROGRESSION_NEGATIF
    des lignes. Simule un bug de retour arriere (ex. un cours "supprime" reduit
    la progression au lieu de la laisser stable).
    """
    logger.info("A9 : Progressions negatives...")

    ids = fetch_all_ids(conn, "progression", "id_progression")
    ids_a_modifier = sample_ids(ids, TAUX_PROGRESSION_NEGATIF)

    updates = [
        (round(random.uniform(-50, -1), 2), id_progression)
        for id_progression in ids_a_modifier
    ]

    sql = "UPDATE progression SET pourcentage = %s WHERE id_progression = %s"
    return execute_update_batch(conn, sql, updates, "A9 progression negative")


def inject_A10_progression_dernier_cours_fantome(conn):
    """
    A10 : donne un dernier_cours = UUID inexistant a TAUX_PROGRESSION_COURS_FANTOME
    des lignes. Simule une reference brisee (le cours a ete supprime, mais la
    progression ne l'a pas ete).

    La colonne dernier_cours n'a PAS de FK dans notre schema : c'est possible.
    """
    logger.info("A10 : dernier_cours fantomes...")

    ids = fetch_all_ids(conn, "progression", "id_progression")
    ids_a_modifier = sample_ids(ids, TAUX_PROGRESSION_COURS_FANTOME)

    updates = [
        (str(uuid.uuid4()), id_progression)  # UUID totalement invente
        for id_progression in ids_a_modifier
    ]

    sql = "UPDATE progression SET dernier_cours = %s WHERE id_progression = %s"
    return execute_update_batch(conn, sql, updates, "A10 cours fantomes")


def inject_A11_progression_module_fantome(conn):
    """
    A11 : ATTENTION -- viole la FK fk_progression_module.
    On INSERE de nouvelles lignes de progression pointant vers des id_module
    qui n'existent pas, apres avoir DESACTIVE temporairement les FK checks.

    C'est une anomalie "violation de FK" demandee explicitement par la spec :
    'quelques violations de cles etrangeres pour les besoins pedagogiques'.

    On REACTIVE les FK checks immediatement apres.
    """
    logger.info("A11 : id_module fantomes (avec desactivation FK)...")

    # Nombre de lignes fantomes a creer
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM progression")
    total = cursor.fetchone()[0]
    cursor.close()

    nb_fantomes = int(round(total * TAUX_PROGRESSION_MODULE_FANTOME))

    # Recupere quelques student_codes existants
    student_codes = fetch_all_ids(conn, "progression", "student_code")
    codes_uniques = list(set(student_codes))

    # Genere les lignes fantomes
    inserts = []
    for _ in range(nb_fantomes):
        id_progression = str(uuid.uuid4())
        student_code = random.choice(codes_uniques)
        id_module_fantome = str(uuid.uuid4())  # UUID totalement invente
        pourcentage = round(random.uniform(0, 100), 2)
        date_maj = "2025-06-15 12:00:00"  # date fixe simple
        inserts.append((
            id_progression, student_code, id_module_fantome,
            pourcentage, None, date_maj
        ))

    # DESACTIVATION temporaire des FK checks
    cursor = conn.cursor()
    cursor.execute("SET foreign_key_checks = 0")
    conn.commit()

    try:
        sql = """
            INSERT INTO progression
                (id_progression, student_code, id_module, pourcentage, dernier_cours, date_maj)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        affected = execute_update_batch(conn, sql, inserts, "A11 module fantomes")
    finally:
        # REACTIVATION obligatoire des FK checks (meme en cas d'erreur)
        cursor.execute("SET foreign_key_checks = 1")
        conn.commit()
        cursor.close()
        logger.info("    foreign_key_checks reactivees.")

    return affected

# =============================================================
# ANOMALIES : table temps_connexion
# =============================================================

def inject_A12_connexion_sans_deconnexion(conn):
    """
    A12 : passe TAUX_CONNEXION_SANS_DECONNEXION des lignes a
    date_deconnexion = NULL. Simule des sessions qui ne se sont
    pas fermees proprement (crash de l'app, fermeture brutale du navigateur).
    """
    logger.info("A12 : Sessions sans deconnexion...")

    ids = fetch_all_ids(conn, "temps_connexion", "id_connexion")
    ids_a_modifier = sample_ids(ids, TAUX_CONNEXION_SANS_DECONNEXION)

    updates = [(id_connexion,) for id_connexion in ids_a_modifier]
    sql = """
        UPDATE temps_connexion
        SET date_deconnexion = NULL,
            duree_minutes = NULL
        WHERE id_connexion = %s
    """
    return execute_update_batch(conn, sql, updates, "A12 sans deconnexion")


def inject_A13_connexion_duree_negative(conn):
    """
    A13 : donne une duree_minutes negative a TAUX_CONNEXION_DUREE_NEGATIVE
    des lignes. Simule un bug de calcul (soustraction inversee des timestamps).
    """
    logger.info("A13 : Durees negatives...")

    ids = fetch_all_ids(conn, "temps_connexion", "id_connexion")
    ids_a_modifier = sample_ids(ids, TAUX_CONNEXION_DUREE_NEGATIVE)

    updates = [
        (random.randint(-500, -1), id_connexion)
        for id_connexion in ids_a_modifier
    ]

    sql = "UPDATE temps_connexion SET duree_minutes = %s WHERE id_connexion = %s"
    return execute_update_batch(conn, sql, updates, "A13 durees negatives")


def inject_A14_connexion_ip_invalide(conn):
    """
    A14 : remplace l'adresse_ip par une valeur invalide pour
    TAUX_CONNEXION_IP_INVALIDE des lignes. Les valeurs sont tirees
    dans IP_INVALIDES (999.999.999.999, invalid_ip, chaine vide, etc.)
    """
    logger.info("A14 : IP invalides...")

    ids = fetch_all_ids(conn, "temps_connexion", "id_connexion")
    ids_a_modifier = sample_ids(ids, TAUX_CONNEXION_IP_INVALIDE)

    updates = [
        (random.choice(IP_INVALIDES), id_connexion)
        for id_connexion in ids_a_modifier
    ]

    sql = "UPDATE temps_connexion SET adresse_ip = %s WHERE id_connexion = %s"
    return execute_update_batch(conn, sql, updates, "A14 IP invalides")


def inject_A15_connexion_appareil_variantes(conn):
    """
    A15 : remplace l'appareil par une variante orthographique pour
    TAUX_CONNEXION_APPAREIL_VARIANTE des lignes. Cree du chaos de saisie
    (mobile, MOBILE, Mobile , Telephone, iPad, etc.)

    C'est l'anomalie la plus volumineuse : ~45 000 lignes affectees.
    """
    logger.info("A15 : Variantes d'appareils...")

    ids = fetch_all_ids(conn, "temps_connexion", "id_connexion")
    ids_a_modifier = sample_ids(ids, TAUX_CONNEXION_APPAREIL_VARIANTE)

    updates = [
        (random.choice(VARIANTES_APPAREILS), id_connexion)
        for id_connexion in ids_a_modifier
    ]

    sql = "UPDATE temps_connexion SET appareil = %s WHERE id_connexion = %s"
    return execute_update_batch(conn, sql, updates, "A15 appareils variantes")


def inject_A16_connexion_dates_inversees(conn):
    """
    A16 : inverse date_connexion et date_deconnexion pour
    TAUX_CONNEXION_DATES_INVERSEES des lignes. La date_deconnexion
    est ALORS plus ancienne que date_connexion -- physiquement impossible.

    Ne touche que des lignes ayant deja une date_deconnexion (pas les A12).
    """
    logger.info("A16 : Dates de connexion / deconnexion inversees...")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_connexion, date_connexion, date_deconnexion
        FROM temps_connexion
        WHERE date_deconnexion IS NOT NULL
    """)
    rows = cursor.fetchall()
    cursor.close()

    nb_inversions = int(round(len(rows) * TAUX_CONNEXION_DATES_INVERSEES))
    rows_a_modifier = random.sample(rows, nb_inversions)

    # Inversion : nouvelle date_connexion = ancienne date_deconnexion et vice versa
    updates = [
        (row[2], row[1], row[0])  # (nouvelle_conn, nouvelle_decon, id)
        for row in rows_a_modifier
    ]

    sql = """
        UPDATE temps_connexion
        SET date_connexion = %s,
            date_deconnexion = %s
        WHERE id_connexion = %s
    """
    return execute_update_batch(conn, sql, updates, "A16 dates inversees")

# =============================================================
# ANOMALIES TRANSVERSALES (plusieurs tables)
# =============================================================

def generate_student_code_fantome():
    """Genere un student_code fantome au format LMS-999XXX (jamais dans PostgreSQL)."""
    numero = random.randint(1, 999)
    return f"{CODES_FANTOMES_PREFIX}{numero:03d}"


def inject_A17_student_code_fantome(conn):
    """
    A17 : remplace le student_code par un code fantome (LMS-999XXX) pour
    TAUX_STUDENT_CODE_FANTOME des lignes dans notes, progression et temps_connexion.

    Simule des references vers des etudiants qui n'existent pas dans PostgreSQL
    (bug d'integration, saisie erronee, systeme externe non synchronise).

    Note technique : progression a une contrainte UNIQUE(student_code, id_module),
    donc on doit gerer les collisions probabilistes (paradoxe des anniversaires).
    On sauvegarde les couples deja tentes et on saute les collisions.
    """
    logger.info("A17 : Student_codes fantomes (LMS-999XXX)...")

    total_affected = 0

    # --- Sous-partie 1 : notes (pas de contrainte UNIQUE) ---
    ids_notes = fetch_all_ids(conn, "notes", "id_note")
    ids_a_modifier = sample_ids(ids_notes, TAUX_STUDENT_CODE_FANTOME)
    updates = [
        (generate_student_code_fantome(), id_note)
        for id_note in ids_a_modifier
    ]
    total_affected += execute_update_batch(
        conn,
        "UPDATE notes SET student_code = %s WHERE id_note = %s",
        updates,
        "A17 notes"
    )

    # --- Sous-partie 2 : progression (contrainte UNIQUE) ---
    # On charge les couples (student_code, id_module) existants pour eviter les collisions
    cursor = conn.cursor()
    cursor.execute("SELECT id_progression, id_module FROM progression")
    all_prog = cursor.fetchall()  # [(id_progression, id_module), ...]
    cursor.close()

    ids_a_modifier = sample_ids([p[0] for p in all_prog], TAUX_STUDENT_CODE_FANTOME)
    map_id_module = {p[0]: p[1] for p in all_prog}

    # Set des couples (student_code, id_module) deja utilises apres modification
    couples_utilises = set()

    updates_prog = []
    collisions = 0
    for id_prog in ids_a_modifier:
        id_module = map_id_module[id_prog]
        # On essaie jusqu'a 5 fois avant de renoncer
        fantome = None
        for _ in range(5):
            candidat = generate_student_code_fantome()
            if (candidat, id_module) not in couples_utilises:
                fantome = candidat
                break

        if fantome is None:
            collisions += 1
            continue

        couples_utilises.add((fantome, id_module))
        updates_prog.append((fantome, id_prog))

    if collisions > 0:
        logger.warning(f"    A17 progression : {collisions} collisions non resolues (ignorees)")

    total_affected += execute_update_batch(
        conn,
        "UPDATE progression SET student_code = %s WHERE id_progression = %s",
        updates_prog,
        "A17 progression"
    )

    # --- Sous-partie 3 : temps_connexion (pas de contrainte UNIQUE) ---
    ids_tc = fetch_all_ids(conn, "temps_connexion", "id_connexion")
    ids_a_modifier = sample_ids(ids_tc, TAUX_STUDENT_CODE_FANTOME)
    updates = [
        (generate_student_code_fantome(), id_connexion)
        for id_connexion in ids_a_modifier
    ]
    total_affected += execute_update_batch(
        conn,
        "UPDATE temps_connexion SET student_code = %s WHERE id_connexion = %s",
        updates,
        "A17 temps_connexion"
    )

    return total_affected

def inject_A18_null_colonnes_nullables(conn):
    """
    A18 : met a NULL certaines colonnes nullables sur TAUX_NULL_COLONNES_NULLABLES
    des lignes de temps_connexion (navigateur, appareil, adresse_ip).

    Simule des donnees manquantes : detection navigateur echouee,
    appareil non identifie, IP anonymisee pour RGPD.
    """
    logger.info("A18 : NULL sur colonnes nullables (temps_connexion)...")

    ids = fetch_all_ids(conn, "temps_connexion", "id_connexion")
    ids_a_modifier = sample_ids(ids, TAUX_NULL_COLONNES_NULLABLES)

    # Pour chaque ligne selectionnee, on met NULL sur une colonne aleatoire
    # parmi navigateur, appareil et adresse_ip (comportement realiste :
    # ce ne sont jamais TOUTES les colonnes qui manquent en meme temps).
    colonnes_candidates = ["navigateur", "appareil", "adresse_ip"]

    total_affected = 0
    for colonne in colonnes_candidates:
        # On divise l'echantillon en 3 : chaque ligne perd 1 colonne (pas plusieurs)
        sous_echantillon = [
            id_conn for id_conn in ids_a_modifier
            if random.random() < 1/3  # ~1/3 des lignes perdent cette colonne
        ]
        updates = [(id_conn,) for id_conn in sous_echantillon]
        sql = f"UPDATE temps_connexion SET {colonne} = NULL WHERE id_connexion = %s"
        total_affected += execute_update_batch(
            conn, sql, updates, f"A18 {colonne} NULL"
        )

    return total_affected

# =============================================================
# MAIN
# =============================================================

def main():
    logger.info("=" * 70)
    logger.info("INJECTION D'ANOMALIES DANS edusmart_learning")
    logger.info("=" * 70)
    logger.info(f"Seed anomalies : {SEED_ANOMALIES}")
    logger.info("")

    # Connexion
    check_config()
    logger.info(f"Connexion : {DB_CONFIG['user']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        logger.error(f"ECHEC de connexion : {e}")
        sys.exit(1)

    logger.info("Connexion etablie.")
    logger.info("")

    # Bilan cumule
    bilan = {}

    try:
       # --- Anomalies table modules ---
        logger.info("--- Table modules ---")
        bilan["A1_categories_desordonnees"] = inject_A1_categories_desordonnees(conn)
        bilan["A2_modules_inactifs"] = inject_A2_modules_inactifs(conn)

	# --- Anomalies tables cours et quiz ---
        logger.info("")
        logger.info("--- Tables cours et quiz ---")
        bilan["A3_cours_doublons_titre"] = inject_A3_cours_doublons_titre(conn)
        bilan["A4_type_cours_variantes"] = inject_A4_type_cours_variantes(conn)
        bilan["A5_quiz_duree_incoherente"] = inject_A5_quiz_duree_incoherente(conn)

	# --- Anomalies table notes ---
        logger.info("")
        logger.info("--- Table notes ---")
        bilan["A6_notes_score_superieur"] = inject_A6_notes_score_superieur(conn)
        bilan["A7_notes_doublons"] = inject_A7_notes_doublons(conn)
	
	# --- Anomalies table progression ---
        logger.info("")
        logger.info("--- Table progression ---")
        bilan["A8_progression_sup_100"] = inject_A8_progression_sup_100(conn)
        bilan["A9_progression_negatif"] = inject_A9_progression_negatif(conn)
        bilan["A10_progression_dernier_cours_fantome"] = inject_A10_progression_dernier_cours_fantome(conn)
        bilan["A11_progression_module_fantome"] = inject_A11_progression_module_fantome(conn)

	# --- Anomalies table temps_connexion ---
        logger.info("")
        logger.info("--- Table temps_connexion ---")
        bilan["A12_connexion_sans_deconnexion"] = inject_A12_connexion_sans_deconnexion(conn)
        bilan["A13_connexion_duree_negative"] = inject_A13_connexion_duree_negative(conn)
        bilan["A14_connexion_ip_invalide"] = inject_A14_connexion_ip_invalide(conn)
        bilan["A15_connexion_appareil_variantes"] = inject_A15_connexion_appareil_variantes(conn)
        bilan["A16_connexion_dates_inversees"] = inject_A16_connexion_dates_inversees(conn)

	# --- Anomalies transversales ---
        logger.info("")
        logger.info("--- Anomalies transversales ---")
        bilan["A17_student_code_fantome"] = inject_A17_student_code_fantome(conn)
        bilan["A18_null_colonnes_nullables"] = inject_A18_null_colonnes_nullables(conn)

    except Error:
        logger.error("Arret du script suite a une erreur MySQL.")
        conn.close()
        sys.exit(1)

    # --- Bilan final ---
    logger.info("")
    logger.info("=" * 70)
    logger.info("BILAN DES ANOMALIES INJECTEES")
    logger.info("=" * 70)
    total = 0
    for code, count in bilan.items():
        logger.info(f"  {code:35s} : {count:>6d} lignes")
        total += count
    logger.info(f"  {'TOTAL':35s} : {total:>6d} lignes")
    logger.info("")

    conn.close()
    logger.info("Injection terminee.")


if __name__ == "__main__":
    main()