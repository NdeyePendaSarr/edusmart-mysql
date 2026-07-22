"""
generator_config.py — Parametres de generation des donnees EduSmart Learning.

Toutes les constantes de generation sont ici, pour ne jamais avoir
de "magic numbers" dans le code metier.

Modifier ce fichier pour ajuster :
  - les volumes generes
  - le seed de reproductibilite
  - les listes de valeurs categorielles (categories, niveaux, etc.)
"""

# =============================================================
# REPRODUCTIBILITE
# =============================================================

# Seed fixe pour Faker et random.
# Toute modification de ce nombre changera l'integralite des donnees generees.
SEED = 42

# Locale Faker pour la generation des textes (titres, descriptions, etc.)
FAKER_LOCALE = "fr_FR"


# =============================================================
# VOLUMES CIBLES
# =============================================================

# Bloc Catalogue
NB_MODULES = 200

# Cours : entre MIN et MAX par module (tire aleatoirement pour chaque module)
COURS_PAR_MODULE_MIN = 8
COURS_PAR_MODULE_MAX = 15

# Quiz : probabilite qu'un cours ait un quiz + nb max de quiz par cours
PROBA_QUIZ_PAR_COURS = 0.80  # 80 % des cours auront au moins un quiz
QUIZ_PAR_COURS_MAX = 2       # jusqu'a 2 quiz max par cours

# =============================================================
# BLOC ACTIVITE (Phase 4b, apres reception des student_codes)
# =============================================================

# Profils d'activite des etudiants (repartition en proportions).
# Total = 1.0 obligatoirement.
PROFILS_ACTIVITE = {
    "inactif":     0.20,  # 20 % ne se connectent quasiment jamais
    "regulier":    0.50,  # 50 % ont une activite moderee
    "investi":     0.25,  # 25 % consomment beaucoup
    "super_actif": 0.05,  # 5  % sont les champions de la plateforme
}

# Nombre de modules suivis par profil (bornes min/max)
NB_MODULES_SUIVIS_PAR_PROFIL = {
    "inactif":     (0, 0),
    "regulier":    (3, 8),
    "investi":     (8, 15),
    "super_actif": (15, 25),
}

# Nombre de notes (tentatives de quiz) par profil
NB_NOTES_PAR_PROFIL = {
    "inactif":     (0, 2),      # les rares actifs de cette categorie
    "regulier":    (10, 40),
    "investi":     (40, 100),
    "super_actif": (100, 200),
}

# Nombre de connexions par profil
NB_CONNEXIONS_PAR_PROFIL = {
    "inactif":     (0, 3),
    "regulier":    (10, 40),
    "investi":     (40, 100),
    "super_actif": (100, 200),
}

# Duree moyenne d'une session (en minutes) - loi normale approchee
DUREE_SESSION_MOY_MINUTES = 45
DUREE_SESSION_ECART_MINUTES = 20

# Devices, browsers, IP pour les connexions
APPAREILS = ["Mobile", "PC", "Tablette"]
NAVIGATEURS = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]

# Probabilite qu'un etudiant valide un quiz (score >= 50 % du score_max)
PROBA_VALIDATION_QUIZ = 0.65

# Nombre max de tentatives pour un meme quiz par un meme etudiant
NB_TENTATIVES_MAX = 3

# =============================================================
# ANOMALIES (Phase 5)
# =============================================================
# Chaque taux est une PROBABILITE (entre 0 et 1) d'introduire
# l'anomalie sur chaque ligne concernee.
# Toutes les anomalies sont documentees dans docs/anomalies.md

# Seed dedie aux anomalies pour permettre de rejouer independamment
# du seed de generation.
SEED_ANOMALIES = 4242

# --- Table modules ---
TAUX_MODULES_INACTIFS = 0.08          # A2 : 8 % de modules inactifs

# Variantes de categories pour l'anomalie A1
# La categorie sera remplacee aleatoirement par une variante
VARIANTES_CATEGORIES = {
    "Data Science":              ["Data", "DATA", "data science", "DataScience"],
    "Intelligence Artificielle": ["IA", "ia", "AI", "Ingenierie IA"],
    "Developpement Web":         ["Dev Web", "dev web", "WebDev", "web development"],
    "Developpement Mobile":      ["Dev Mobile", "MOBILE", "mobile dev"],
    "Cybersecurite":             ["Cyber", "CYBER", "Securite", "InfoSec"],
    "Cloud Computing":           ["Cloud", "cloud", "CLOUD", "AWS/Azure"],
    "DevOps":                    ["devops", "DEVOPS", "Dev Ops", "SRE"],
    "Bases de donnees":          ["BDD", "bdd", "Database", "SGBD"],
    "UX/UI Design":              ["UX", "UI", "UX-UI", "Design UX"],
    "Marketing Digital":         ["Marketing", "MARKETING", "Digital Marketing", "Marketing D."],
}

# --- Table cours ---
TAUX_COURS_DOUBLONS_TITRE = 0.03      # A3 : 3 % de titres dupliques

# Variantes de type_cours pour l'anomalie A4
VARIANTES_TYPE_COURS = ["Video", "video", "VIDEO", "PDF", "pdf", "Pdf",
                        "TP", "tp", "Projet", "PROJET", "projet"]

# --- Table quiz ---
TAUX_QUIZ_DUREE_INCOHERENTE = 0.03    # A5 : 3 % de durees incoherentes

# --- Table notes ---
TAUX_NOTES_SCORE_SUPERIEUR = 0.01     # A6 : 1 % de scores > score_max
TAUX_NOTES_DOUBLONS = 0.005           # A7 : 0.5 % de doublons

# --- Table progression ---
TAUX_PROGRESSION_SUP_100 = 0.02       # A8 : 2 % de pourcentages > 100
TAUX_PROGRESSION_NEGATIF = 0.005      # A9 : 0.5 % de pourcentages < 0
TAUX_PROGRESSION_COURS_FANTOME = 0.04 # A10 : 4 % de dernier_cours inexistants
TAUX_PROGRESSION_MODULE_FANTOME = 0.01# A11 : 1 % de id_module fantomes

# --- Table temps_connexion ---
TAUX_CONNEXION_SANS_DECONNEXION = 0.08   # A12 : 8 % de sessions non fermees
TAUX_CONNEXION_DUREE_NEGATIVE = 0.01     # A13 : 1 % de durees negatives
TAUX_CONNEXION_IP_INVALIDE = 0.02        # A14 : 2 % d'IP invalides
TAUX_CONNEXION_APPAREIL_VARIANTE = 0.12  # A15 : 12 % d'appareils non standard
TAUX_CONNEXION_DATES_INVERSEES = 0.005   # A16 : 0.5 % de dates inversees

# Variantes d'appareils pour l'anomalie A15
VARIANTES_APPAREILS = ["mobile", "MOBILE", "Mobile ", "Telephone", "Phone",
                       "pc", "PC ", "Ordinateur", "tablette", "TABLETTE", "iPad"]

# IP invalides pour l'anomalie A14
IP_INVALIDES = ["999.999.999.999", "0.0.0.0", "256.1.1.1",
                "invalid_ip", "", "1.2.3", "127.0.0.1.1"]

# --- Anomalies transversales ---
TAUX_STUDENT_CODE_FANTOME = 0.01      # A17 : 1 % de codes fantomes (LMS-999XXX)
TAUX_NULL_COLONNES_NULLABLES = 0.05   # A18 : 5 % de NULL supplementaires

# Range des codes fantomes pour l'anomalie A17
CODES_FANTOMES_PREFIX = "LMS-999"     # LMS-999001 a LMS-999999 (jamais dans PostgreSQL)


# =============================================================
# FENETRE TEMPORELLE
# =============================================================
# Periode couverte par les donnees generees.
# A coordonner avec le groupe (Aissata, Mouhameth, Seydina).

from datetime import date

DATE_DEBUT_PROJET = date(2024, 9, 1)   # 1er septembre 2024
DATE_FIN_PROJET   = date(2026, 6, 30)  # 30 juin 2026


# =============================================================
# VALEURS CATEGORIELLES (catalogue)
# =============================================================

# Categories thematiques des modules
CATEGORIES_MODULES = [
    "Developpement Web",
    "Data Science",
    "Intelligence Artificielle",
    "Cybersecurite",
    "Cloud Computing",
    "Developpement Mobile",
    "DevOps",
    "Bases de donnees",
    "UX/UI Design",
    "Marketing Digital",
]

# Niveaux
NIVEAUX = ["Debutant", "Intermediaire", "Avance"]

# Types de cours
TYPES_COURS = ["Video", "PDF", "TP", "Projet"]

# Prefixes des codes metier
PREFIX_MODULE = "MOD"
PREFIX_COURSE = "COURSE"
PREFIX_QUIZ = "QUIZ"


# =============================================================
# CHEMINS DE FICHIERS
# =============================================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Fichiers CSV de sortie pour le bloc Catalogue
CSV_MODULES = DATA_DIR / "modules.csv"
CSV_COURS = DATA_DIR / "cours.csv"
CSV_QUIZ = DATA_DIR / "quiz.csv"

# Fichiers CSV de sortie pour le bloc Activite
CSV_NOTES = DATA_DIR / "notes.csv"
CSV_PROGRESSION = DATA_DIR / "progression.csv"
CSV_TEMPS_CONNEXION = DATA_DIR / "temps_connexion.csv"

# Fichier des student_codes (fourni par Aissata en Phase B)
CSV_STUDENT_CODES = DATA_DIR / "student_codes.csv"


# =============================================================
# PARAMETRES D'INSERTION
# =============================================================

# Taille des batchs pour l'insertion MySQL
# 1000 est un bon compromis vitesse/memoire.
BATCH_SIZE = 1000