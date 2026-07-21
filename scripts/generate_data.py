"""
generate_data.py — Generation des donnees pour edusmart_learning.

Ce script produit les donnees de la source MySQL EN MEMOIRE, puis
les ecrit dans des fichiers CSV dans le dossier data/.

Phase 4a : bloc Catalogue (modules, cours, quiz)
Phase 4b : bloc Activite (notes, progression, temps_connexion)

Principes :
  - Reproductibilite : seed fixe (Faker + random)
  - Aucune anomalie a ce stade : les donnees sont propres.
    Les anomalies seront introduites en Phase 5 via un script dedie.
  - Separation generation / insertion : ce script ne parle PAS a MySQL.
"""

import csv
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faker import Faker
from tqdm import tqdm

from config.generator_config import (
    # Reproductibilite
    SEED,
    FAKER_LOCALE,
    # Bloc Catalogue
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
    # Bloc Activite
    PROFILS_ACTIVITE,
    NB_MODULES_SUIVIS_PAR_PROFIL,
    NB_NOTES_PAR_PROFIL,
    NB_CONNEXIONS_PAR_PROFIL,
    DUREE_SESSION_MOY_MINUTES,
    DUREE_SESSION_ECART_MINUTES,
    APPAREILS,
    NAVIGATEURS,
    PROBA_VALIDATION_QUIZ,
    NB_TENTATIVES_MAX,
    # Fenetre temporelle
    DATE_DEBUT_PROJET,
    DATE_FIN_PROJET,
    # Chemins
    CSV_MODULES,
    CSV_COURS,
    CSV_QUIZ,
    CSV_NOTES,
    CSV_PROGRESSION,
    CSV_TEMPS_CONNEXION,
    CSV_STUDENT_CODES,
    DATA_DIR,
    LOGS_DIR,
)


# =============================================================
# LOGS
# =============================================================

LOGS_DIR.mkdir(exist_ok=True)

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
# UTILITAIRES TEMPORELS
# =============================================================

def random_datetime_in_window(start_date, end_date):
    """Genere un datetime aleatoire entre deux dates (heure aleatoire dans la journee)."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86399)  # 24h * 3600s - 1
    return datetime.combine(start_date, datetime.min.time()) + timedelta(
        days=random_days, seconds=random_seconds
    )


# =============================================================
# BLOC CATALOGUE
# =============================================================

def generate_modules():
    """Genere NB_MODULES modules."""
    logger.info(f"Generation de {NB_MODULES} modules...")

    modules = []
    for i in range(1, NB_MODULES + 1):
        categorie = random.choice(CATEGORIES_MODULES)
        abrev = categorie[:3].upper().replace(" ", "").replace("/", "")
        code = f"{PREFIX_MODULE}-{abrev}-{i:02d}"

        module = {
            "id_module": str(uuid.uuid4()),
            "code_module": code,
            "nom_module": fake.catch_phrase(),
            "categorie": categorie,
            "niveau": random.choice(NIVEAUX),
            "duree_heures": random.randint(20, 120),
            "actif": 1,
        }
        modules.append(module)

    logger.info(f"  {len(modules)} modules generes.")
    return modules


def generate_cours(modules):
    """Pour chaque module, genere entre 8 et 15 cours."""
    logger.info("Generation des cours...")

    cours_list = []
    global_counter = 1

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


def generate_quiz(cours_list):
    """Pour chaque cours, generation probabiliste de quiz."""
    logger.info("Generation des quiz...")

    quiz_list = []
    global_counter = 1

    for cours in cours_list:
        if random.random() > PROBA_QUIZ_PAR_COURS:
            continue

        nb_quiz = random.randint(1, QUIZ_PAR_COURS_MAX)
        for _ in range(nb_quiz):
            nb_questions = random.randint(5, 30)
            score_max = round(nb_questions * random.uniform(0.8, 1.2), 2)
            duree = int(nb_questions * random.uniform(0.5, 1.5))
            duree = max(duree, 5)

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
# BLOC ACTIVITE
# =============================================================

def load_student_codes():
    """Charge la liste des student_codes depuis le fichier partage."""
    logger.info(f"Chargement des student_codes depuis {CSV_STUDENT_CODES.name}...")

    if not CSV_STUDENT_CODES.exists():
        logger.error(f"Fichier manquant : {CSV_STUDENT_CODES}")
        logger.error("Execute d'abord scripts/build_student_codes.py")
        sys.exit(1)

    with open(CSV_STUDENT_CODES, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        codes = [row["student_code"] for row in reader]

    logger.info(f"  {len(codes)} student_codes charges.")
    return codes


def assign_activity_profiles(student_codes):
    """
    Repartit les etudiants dans les 4 profils d'activite selon PROFILS_ACTIVITE.

    Retourne : list[dict] avec cles 'student_code' et 'profil'.
    """
    logger.info("Repartition des etudiants par profil d'activite...")

    n = len(student_codes)
    # Melange aleatoire pour ne pas biaiser (les 20% inactifs ne seront pas
    # les 2000 premiers de la liste triee)
    codes_shuffled = student_codes.copy()
    random.shuffle(codes_shuffled)

    students_with_profile = []
    index = 0
    for profil, proportion in PROFILS_ACTIVITE.items():
        count = int(round(n * proportion))
        for i in range(count):
            if index >= n:
                break
            students_with_profile.append({
                "student_code": codes_shuffled[index],
                "profil": profil,
            })
            index += 1

    # Le reste (a cause des arrondis) va dans "regulier" par defaut
    while index < n:
        students_with_profile.append({
            "student_code": codes_shuffled[index],
            "profil": "regulier",
        })
        index += 1

    # Statistiques
    from collections import Counter
    counts = Counter(s["profil"] for s in students_with_profile)
    for profil, count in counts.items():
        logger.info(f"  {profil:15s} : {count:6d} etudiants ({count/n*100:.1f} %)")

    return students_with_profile


def generate_progression(modules, students_with_profile):
    """
    Pour chaque etudiant, genere une ligne de progression par module suivi.
    """
    logger.info("Generation des progressions...")

    progressions = []
    module_ids = [m["id_module"] for m in modules]

    for student in tqdm(students_with_profile, desc="  progression", unit="etu"):
        profil = student["profil"]
        min_mods, max_mods = NB_MODULES_SUIVIS_PAR_PROFIL[profil]
        if max_mods == 0:
            continue

        nb_modules_suivis = random.randint(min_mods, max_mods)
        nb_modules_suivis = min(nb_modules_suivis, len(module_ids))

        # Tirage sans remise : un etudiant ne suit pas 2 fois le meme module
        modules_choisis = random.sample(module_ids, nb_modules_suivis)

        for id_module in modules_choisis:
            pourcentage = round(random.uniform(0, 100), 2)
            date_maj = random_datetime_in_window(DATE_DEBUT_PROJET, DATE_FIN_PROJET)

            progression = {
                "id_progression": str(uuid.uuid4()),
                "student_code": student["student_code"],
                "id_module": id_module,
                "pourcentage": pourcentage,
                "dernier_cours": "",  # NULL en base (a Phase 5 on remplira parfois)
                "date_maj": date_maj.strftime("%Y-%m-%d %H:%M:%S"),
            }
            progressions.append(progression)

    logger.info(f"  {len(progressions)} progressions generees.")
    return progressions


def generate_notes(quiz_list, students_with_profile):
    """
    Pour chaque etudiant, genere entre X et Y tentatives de quiz.
    Certains quiz seront tentes plusieurs fois (jusqu'a NB_TENTATIVES_MAX).
    """
    logger.info("Generation des notes...")

    # Index rapides
    quiz_by_id = {q["id_quiz"]: q for q in quiz_list}
    quiz_ids = list(quiz_by_id.keys())

    notes = []

    for student in tqdm(students_with_profile, desc="  notes", unit="etu"):
        profil = student["profil"]
        min_n, max_n = NB_NOTES_PAR_PROFIL[profil]
        if max_n == 0:
            continue

        nb_notes = random.randint(min_n, max_n)

        # Compteur de tentatives par quiz pour cet etudiant
        tentatives_par_quiz = {}

        for _ in range(nb_notes):
            id_quiz = random.choice(quiz_ids)
            tentative_num = tentatives_par_quiz.get(id_quiz, 0) + 1

            # Un etudiant abandonne apres NB_TENTATIVES_MAX
            if tentative_num > NB_TENTATIVES_MAX:
                # On tire un autre quiz
                id_quiz = random.choice(quiz_ids)
                tentative_num = tentatives_par_quiz.get(id_quiz, 0) + 1
                if tentative_num > NB_TENTATIVES_MAX:
                    continue  # tant pis, on saute cette note

            tentatives_par_quiz[id_quiz] = tentative_num
            quiz = quiz_by_id[id_quiz]

            # Score realiste : ~65 % chance de validation (score >= 50 % max)
            score_max = float(quiz["score_max"])
            if random.random() < PROBA_VALIDATION_QUIZ:
                score = round(random.uniform(score_max * 0.5, score_max), 2)
                valide = 1
            else:
                score = round(random.uniform(0, score_max * 0.5), 2)
                valide = 0

            date_passage = random_datetime_in_window(DATE_DEBUT_PROJET, DATE_FIN_PROJET)

            note = {
                "id_note": str(uuid.uuid4()),
                "id_quiz": id_quiz,
                "student_code": student["student_code"],
                "date_passage": date_passage.strftime("%Y-%m-%d %H:%M:%S"),
                "score": score,
                "tentative": tentative_num,
                "valide": valide,
            }
            notes.append(note)

    logger.info(f"  {len(notes)} notes generees.")
    return notes


def generate_temps_connexion(students_with_profile):
    """
    Genere des sessions de connexion realistes pour chaque etudiant.
    """
    logger.info("Generation des temps de connexion...")

    connexions = []

    for student in tqdm(students_with_profile, desc="  temps_connexion", unit="etu"):
        profil = student["profil"]
        min_c, max_c = NB_CONNEXIONS_PAR_PROFIL[profil]
        if max_c == 0:
            continue

        nb_connexions = random.randint(min_c, max_c)

        for _ in range(nb_connexions):
            date_connexion = random_datetime_in_window(DATE_DEBUT_PROJET, DATE_FIN_PROJET)

            # Duree via loi normale (moyenne 45 min, ecart-type 20 min)
            duree = max(1, int(random.gauss(
                DUREE_SESSION_MOY_MINUTES, DUREE_SESSION_ECART_MINUTES
            )))
            date_deconnexion = date_connexion + timedelta(minutes=duree)

            connexion = {
                "id_connexion": str(uuid.uuid4()),
                "student_code": student["student_code"],
                "date_connexion": date_connexion.strftime("%Y-%m-%d %H:%M:%S"),
                "date_deconnexion": date_deconnexion.strftime("%Y-%m-%d %H:%M:%S"),
                "duree_minutes": duree,
                "appareil": random.choice(APPAREILS),
                "navigateur": random.choice(NAVIGATEURS),
                "adresse_ip": fake.ipv4(),
            }
            connexions.append(connexion)

    logger.info(f"  {len(connexions)} connexions generees.")
    return connexions


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
    logger.info(f"  Ecrit : {path.name} ({len(data)} lignes)")


# =============================================================
# MAIN
# =============================================================

def main():
    logger.info("=" * 60)
    logger.info("Generation des donnees - CATALOGUE + ACTIVITE")
    logger.info("=" * 60)

    # --- 1. Bloc Catalogue ---
    modules = generate_modules()
    cours_list = generate_cours(modules)
    quiz_list = generate_quiz(cours_list)

    # --- 2. Chargement des student_codes ---
    student_codes = load_student_codes()
    students_with_profile = assign_activity_profiles(student_codes)

    # --- 3. Bloc Activite ---
    progressions = generate_progression(modules, students_with_profile)
    notes = generate_notes(quiz_list, students_with_profile)
    connexions = generate_temps_connexion(students_with_profile)

    # --- 4. Ecriture des CSV ---
    logger.info("")
    logger.info("Ecriture des fichiers CSV...")

    write_csv(CSV_MODULES, modules, fieldnames=[
        "id_module", "code_module", "nom_module", "categorie",
        "niveau", "duree_heures", "actif",
    ])
    write_csv(CSV_COURS, cours_list, fieldnames=[
        "id_cours", "id_module", "code_cours_temp", "titre",
        "ordre", "duree_minutes", "type_cours", "statut",
    ])
    write_csv(CSV_QUIZ, quiz_list, fieldnames=[
        "id_quiz", "id_cours", "code_quiz_temp", "titre",
        "nb_questions", "score_max", "duree_minutes",
    ])
    write_csv(CSV_PROGRESSION, progressions, fieldnames=[
        "id_progression", "student_code", "id_module",
        "pourcentage", "dernier_cours", "date_maj",
    ])
    write_csv(CSV_NOTES, notes, fieldnames=[
        "id_note", "id_quiz", "student_code", "date_passage",
        "score", "tentative", "valide",
    ])
    write_csv(CSV_TEMPS_CONNEXION, connexions, fieldnames=[
        "id_connexion", "student_code", "date_connexion", "date_deconnexion",
        "duree_minutes", "appareil", "navigateur", "adresse_ip",
    ])

    # --- 5. Bilan ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("BILAN")
    logger.info("=" * 60)
    logger.info(f"  Modules          : {len(modules):>8d}")
    logger.info(f"  Cours            : {len(cours_list):>8d}")
    logger.info(f"  Quiz             : {len(quiz_list):>8d}")
    logger.info(f"  Progressions     : {len(progressions):>8d}")
    logger.info(f"  Notes            : {len(notes):>8d}")
    logger.info(f"  Connexions       : {len(connexions):>8d}")
    total = len(modules) + len(cours_list) + len(quiz_list) + len(progressions) + len(notes) + len(connexions)
    logger.info(f"  {'TOTAL':17s}: {total:>8d}")
    logger.info(f"  Fichiers ecrits dans : {DATA_DIR}")
    logger.info("=" * 60)
    logger.info("Generation terminee avec succes.")


if __name__ == "__main__":
    main()