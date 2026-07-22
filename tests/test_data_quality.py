"""
test_data_quality.py — Rapport de qualite de la base edusmart_learning.

Ce script se connecte a MySQL et execute une batterie de tests :

  1. Tests de volumetrie : verifie que chaque table contient le bon
     nombre de lignes (par rapport aux valeurs officielles).

  2. Tests d'anomalies : pour chacune des 18 anomalies (A1 a A18),
     execute une requete de detection et compare au volume annonce.

Chaque test produit une ligne [PASS] ou [FAIL] dans la sortie.
Un rapport final resume le taux de reussite.

Usage :
    python tests/test_data_quality.py

Sortie : code 0 si tous les tests passent, 1 sinon.
"""

import logging
import sys
from pathlib import Path

# --- Racine du projet ---
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mysql.connector
from mysql.connector import Error

from config.db_config import DB_CONFIG, check_config


# =============================================================
# LOGGING (console seulement, pas de fichier)
# =============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# =============================================================
# VALEURS OFFICIELLES (a comparer aux valeurs observees)
# =============================================================

VOLUMES_ATTENDUS = {
    "modules": 50,
    "cours": 568,
    "quiz": 690,
    "progression": 66931,     # 66268 propres + 663 fantomes A11
    "notes": 378028,          # 376147 propres + 1881 doublons A7
    "temps_connexion": 377047,
}

# Tolerance de +/- 3 % pour les tests statistiques
TOLERANCE_PCT = 3


# =============================================================
# UTILITAIRES
# =============================================================

def query_scalar(cursor, sql):
    """Execute une requete et retourne la premiere colonne de la premiere ligne."""
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0] if row else None


def check_test(nom_test, observe, attendu, tolerance_pct=None):
    """
    Compare une valeur observee a une valeur attendue.

    - Si tolerance_pct est None : test strict (egalite exacte).
    - Sinon : accepte un ecart jusqu'a tolerance_pct pourcent.

    Retourne : True si le test passe, False sinon.
    Affiche : [PASS] ou [FAIL] avec details.
    """
    # Conversion en int (les agregations MySQL peuvent renvoyer Decimal ou None)
    observe = int(observe) if observe is not None else 0

    if tolerance_pct is None:
        passe = (observe == attendu)
        detail = f"attendu: {attendu}"
    else:
        borne = attendu * tolerance_pct / 100
        passe = abs(observe - attendu) <= borne
        detail = f"attendu: {attendu} +/- {tolerance_pct}%"

    statut = "[PASS]" if passe else "[FAIL]"
    logger.info(f"{statut} {nom_test:50s} observe: {observe:>7d}  ({detail})")
    return passe

# =============================================================
# TESTS DE VOLUMETRIE
# =============================================================

def tests_volumetrie(cursor):
    """
    Verifie le nombre de lignes de chaque table.
    Test strict (pas de tolerance).
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TESTS DE VOLUMETRIE (strict)")
    logger.info("=" * 80)

    resultats = []
    for table, attendu in VOLUMES_ATTENDUS.items():
        observe = query_scalar(cursor, f"SELECT COUNT(*) FROM {table}")
        nom_test = f"Volume {table}"
        resultats.append(check_test(nom_test, observe, attendu))

    return resultats


# =============================================================
# TESTS D'ANOMALIES (18 tests avec tolerance +/- 3 %)
# =============================================================

ANOMALIES_ATTENDUES = {
    "A1_categories_desordonnees":  30,
    "A2_modules_inactifs":          4,
    "A3_cours_doublons_titre":     17,
    "A4_type_cours_variantes":     37,  # 53 UPDATE, 16 sans effet (valeur propre re-tiree)
    "A5_quiz_duree_incoherente":   21,
    "A6_notes_score_superieur":  3761,
    "A7_notes_doublons":         1881,
    "A8_progression_sup_100":    1325,
    "A9_progression_negatif":     331,
    "A10_progression_dernier_cours_fantome": 2651,
    "A11_progression_module_fantome":         663,
    "A12_connexion_sans_deconnexion": 30164,
    "A13_connexion_duree_negative":    3770,
    "A14_connexion_ip_invalide":       7541,
    "A15_connexion_appareil_variantes": 45246,
    "A16_connexion_dates_inversees":   1734,
    "A17_student_code_fantome":        8219,
    "A18_null_colonnes_nullables":    18895,
}


def tests_anomalies(cursor):
    """
    Detecte chaque anomalie via une requete SQL et compare au volume attendu.
    Tolerance : +/- 3 % (pour absorber les variations statistiques).
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"TESTS D'ANOMALIES (tolerance +/- {TOLERANCE_PCT} %)")
    logger.info("=" * 80)

    resultats = []

    # A1 : categories desordonnees
    sql = """
        SELECT COUNT(*) FROM modules
        WHERE BINARY categorie NOT IN (
            'Data Science', 'Intelligence Artificielle', 'Developpement Web',
            'Developpement Mobile', 'Cybersecurite', 'Cloud Computing',
            'DevOps', 'Bases de donnees', 'UX/UI Design', 'Marketing Digital'
        )
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A1 categories desordonnees", observe,
                                ANOMALIES_ATTENDUES["A1_categories_desordonnees"],
                                TOLERANCE_PCT))

    # A2 : modules inactifs
    observe = query_scalar(cursor, "SELECT COUNT(*) FROM modules WHERE actif = 0")
    resultats.append(check_test("A2 modules inactifs", observe,
                                ANOMALIES_ATTENDUES["A2_modules_inactifs"]))

    # A3 : doublons de titres (tolerance elargie a 10%)
    sql = """
        SELECT COUNT(*) FROM (
            SELECT titre FROM cours GROUP BY titre HAVING COUNT(*) >= 2
        ) t
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A3 cours doublons titre", observe,
                                ANOMALIES_ATTENDUES["A3_cours_doublons_titre"],
                                10))
    # A4 : variantes type_cours
    sql = """
        SELECT COUNT(*) FROM cours
        WHERE BINARY type_cours NOT IN ('Video', 'PDF', 'TP', 'Projet')
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A4 type_cours variantes", observe,
                                ANOMALIES_ATTENDUES["A4_type_cours_variantes"],
                                TOLERANCE_PCT))

    # A5 : durees quiz incoherentes
    sql = "SELECT COUNT(*) FROM quiz WHERE duree_minutes < 5 OR duree_minutes > 120"
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A5 quiz duree incoherente", observe,
                                ANOMALIES_ATTENDUES["A5_quiz_duree_incoherente"],
                                TOLERANCE_PCT))

    # A6 : scores > score_max
    sql = """
        SELECT COUNT(*) FROM notes n
        INNER JOIN quiz q ON q.id_quiz = n.id_quiz
        WHERE n.score > q.score_max
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A6 notes score > max", observe,
                                ANOMALIES_ATTENDUES["A6_notes_score_superieur"],
                                TOLERANCE_PCT))

    # A7 : doublons de triplets (student_code, id_quiz, tentative)
    sql = """
        SELECT COALESCE(SUM(nb - 1), 0) FROM (
            SELECT COUNT(*) AS nb
            FROM notes GROUP BY student_code, id_quiz, tentative
            HAVING nb >= 2
        ) t
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A7 notes doublons", observe,
                                ANOMALIES_ATTENDUES["A7_notes_doublons"],
                                TOLERANCE_PCT))

    # A8 : progressions > 100
    observe = query_scalar(cursor,
                           "SELECT COUNT(*) FROM progression WHERE pourcentage > 100")
    resultats.append(check_test("A8 progression > 100", observe,
                                ANOMALIES_ATTENDUES["A8_progression_sup_100"],
                                TOLERANCE_PCT))

    # A9 : progressions negatives
    observe = query_scalar(cursor,
                           "SELECT COUNT(*) FROM progression WHERE pourcentage < 0")
    resultats.append(check_test("A9 progression negatif", observe,
                                ANOMALIES_ATTENDUES["A9_progression_negatif"],
                                TOLERANCE_PCT))

    # A10 : dernier_cours pointe vers un UUID inexistant
    sql = """
        SELECT COUNT(*) FROM progression p
        LEFT JOIN cours c ON c.id_cours = p.dernier_cours
        WHERE p.dernier_cours IS NOT NULL AND c.id_cours IS NULL
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A10 dernier_cours fantome", observe,
                                ANOMALIES_ATTENDUES["A10_progression_dernier_cours_fantome"],
                                TOLERANCE_PCT))

    # A11 : progressions avec id_module fantome (violation FK)
    sql = """
        SELECT COUNT(*) FROM progression p
        LEFT JOIN modules m ON m.id_module = p.id_module
        WHERE m.id_module IS NULL
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A11 progression module fantome", observe,
                                ANOMALIES_ATTENDUES["A11_progression_module_fantome"],
                                TOLERANCE_PCT))

    # A12 : connexions sans deconnexion
    observe = query_scalar(cursor,
                           "SELECT COUNT(*) FROM temps_connexion WHERE date_deconnexion IS NULL")
    resultats.append(check_test("A12 connexion sans deconnexion", observe,
                                ANOMALIES_ATTENDUES["A12_connexion_sans_deconnexion"],
                                TOLERANCE_PCT))

    # A13 : durees negatives
    observe = query_scalar(cursor,
                           "SELECT COUNT(*) FROM temps_connexion WHERE duree_minutes < 0")
    resultats.append(check_test("A13 connexion duree negative", observe,
                                ANOMALIES_ATTENDUES["A13_connexion_duree_negative"],
                                TOLERANCE_PCT))

    # A14 : IP invalides
    sql = """
        SELECT COUNT(*) FROM temps_connexion
        WHERE adresse_ip IN
            ('999.999.999.999', '0.0.0.0', '256.1.1.1',
             'invalid_ip', '', '1.2.3', '127.0.0.1.1')
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A14 connexion IP invalide", observe,
                                ANOMALIES_ATTENDUES["A14_connexion_ip_invalide"],
                                TOLERANCE_PCT))

    # A15 : variantes d'appareils
    sql = """
        SELECT COUNT(*) FROM temps_connexion
        WHERE appareil IS NOT NULL
          AND BINARY appareil NOT IN ('Mobile', 'PC', 'Tablette')
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A15 connexion appareil variantes", observe,
                                ANOMALIES_ATTENDUES["A15_connexion_appareil_variantes"],
                                TOLERANCE_PCT))

    # A16 : dates inversees
    sql = """
        SELECT COUNT(*) FROM temps_connexion
        WHERE date_deconnexion IS NOT NULL
          AND date_deconnexion < date_connexion
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A16 connexion dates inversees", observe,
                                ANOMALIES_ATTENDUES["A16_connexion_dates_inversees"],
                                TOLERANCE_PCT))

    # A17 : student_codes fantomes (sur les 3 tables)
    sql = """
        SELECT
            (SELECT COUNT(*) FROM notes WHERE student_code LIKE 'LMS-999%')
          + (SELECT COUNT(*) FROM progression WHERE student_code LIKE 'LMS-999%')
          + (SELECT COUNT(*) FROM temps_connexion WHERE student_code LIKE 'LMS-999%')
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A17 student_code fantome (total)", observe,
                                ANOMALIES_ATTENDUES["A17_student_code_fantome"],
                                TOLERANCE_PCT))

    # A18 : NULL sur colonnes nullables (temps_connexion)
    sql = """
        SELECT
            SUM(CASE WHEN navigateur IS NULL THEN 1 ELSE 0 END)
          + SUM(CASE WHEN appareil IS NULL THEN 1 ELSE 0 END)
          + SUM(CASE WHEN adresse_ip IS NULL THEN 1 ELSE 0 END)
        FROM temps_connexion
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("A18 NULL colonnes nullables", observe,
                                ANOMALIES_ATTENDUES["A18_null_colonnes_nullables"],
                                TOLERANCE_PCT))

    return resultats

# =============================================================
# TESTS D'INTEGRITE RELATIONNELLE
# =============================================================

def tests_integrite(cursor):
    """
    Verifie que les contraintes relationnelles sont respectees.

    Ces tests devraient TOUJOURS passer (a l'exception documentee
    de l'anomalie A11 sur progression.id_module, volontairement injectee
    par contournement FK).
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("TESTS D'INTEGRITE RELATIONNELLE (strict)")
    logger.info("=" * 80)

    resultats = []

    # Chaque cours doit pointer vers un module existant
    sql = """
        SELECT COUNT(*) FROM cours c
        LEFT JOIN modules m ON m.id_module = c.id_module
        WHERE m.id_module IS NULL
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("Integrite cours -> modules (attendu: 0)",
                                observe, 0))

    # Chaque quiz doit pointer vers un cours existant
    sql = """
        SELECT COUNT(*) FROM quiz q
        LEFT JOIN cours c ON c.id_cours = q.id_cours
        WHERE c.id_cours IS NULL
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("Integrite quiz -> cours (attendu: 0)",
                                observe, 0))

    # Chaque note doit pointer vers un quiz existant
    sql = """
        SELECT COUNT(*) FROM notes n
        LEFT JOIN quiz q ON q.id_quiz = n.id_quiz
        WHERE q.id_quiz IS NULL
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("Integrite notes -> quiz (attendu: 0)",
                                observe, 0))

    # La contrainte UNIQUE(student_code, id_module) de progression est respectee
    sql = """
        SELECT COUNT(*) FROM (
            SELECT student_code, id_module
            FROM progression
            GROUP BY student_code, id_module
            HAVING COUNT(*) > 1
        ) t
    """
    observe = query_scalar(cursor, sql)
    resultats.append(check_test("Unicite (student_code, id_module) progression",
                                observe, 0))

    # Les tentatives sur notes ne depassent jamais NB_TENTATIVES_MAX = 3
    observe = query_scalar(cursor, "SELECT COUNT(*) FROM notes WHERE tentative > 3")
    resultats.append(check_test("Tentatives notes <= 3 (attendu: 0)",
                                observe, 0))

    # Verification que foreign_key_checks est bien reactivee
    observe_raw = query_scalar(cursor, "SELECT @@foreign_key_checks")
    fk_actif = int(observe_raw) if observe_raw is not None else 0
    fk_status = "ON" if fk_actif == 1 else "OFF"
    passe = (fk_actif == 1)
    statut = "[PASS]" if passe else "[FAIL]"
    logger.info(f"{statut} {'foreign_key_checks est ON':50s} observe: {fk_status:>7s}  (attendu: ON)")
    resultats.append(passe)

    return resultats

# =============================================================
# MAIN
# =============================================================

def main():
    logger.info("=" * 80)
    logger.info("RAPPORT DE QUALITE - edusmart_learning")
    logger.info("=" * 80)

    check_config()
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        logger.error(f"ECHEC de connexion MySQL : {e}")
        sys.exit(2)

    cursor = conn.cursor()

    # Execution des batteries de tests
    resultats_volumetrie = tests_volumetrie(cursor)

    resultats_anomalies = tests_anomalies(cursor)
    resultats_integrite = tests_integrite(cursor)

    # --- Rapport final ---
    tous_resultats = resultats_volumetrie + resultats_anomalies + resultats_integrite
    nb_pass = sum(tous_resultats)
    nb_total = len(tous_resultats)
    taux = nb_pass / nb_total * 100 if nb_total else 0

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"RESUME : {nb_pass}/{nb_total} tests reussis ({taux:.1f} %)")
    logger.info("=" * 80)

    cursor.close()
    conn.close()

    # Code de sortie : 0 si tout passe, 1 sinon
    sys.exit(0 if nb_pass == nb_total else 1)


if __name__ == "__main__":
    main()