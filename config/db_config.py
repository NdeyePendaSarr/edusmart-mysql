"""
Configuration de connexion MySQL — EduSmart Learning.

Ce module charge les variables d'environnement depuis le fichier .env
et expose un dictionnaire DB_CONFIG utilisable par mysql-connector-python.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Chemin absolu vers le fichier .env, indépendamment d'où on lance le script
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Chargement du fichier .env
load_dotenv(dotenv_path=ENV_PATH)


# Dictionnaire de configuration prêt à passer à mysql.connector.connect()
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
}


def check_config():
    """Vérifie que toutes les variables essentielles sont bien définies."""
    required = ["user", "password", "database"]
    missing = [key for key in required if not DB_CONFIG.get(key)]
    if missing:
        raise ValueError(
            f"Variables manquantes dans .env : {', '.join(missing)}. "
            f"Vérifiez votre fichier .env"
        )
    return True