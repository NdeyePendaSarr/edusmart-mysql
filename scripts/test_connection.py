"""
test_connection.py — Vérifie que Python peut se connecter à MySQL.

Ce script est le "Hello World" du projet : s'il passe, c'est que
l'environnement est correctement configuré. À exécuter APRÈS
avoir rempli le fichier .env.
"""

import sys
from pathlib import Path

# Ajoute la racine du projet au PYTHONPATH pour trouver le module config
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import mysql.connector
from mysql.connector import Error
from config.db_config import DB_CONFIG, check_config


def test_connection():
    """Tente une connexion MySQL et affiche les infos serveur."""
    print("=" * 60)
    print("Test de connexion — EduSmart Learning (MySQL)")
    print("=" * 60)

    # Étape 1 : vérifier que .env contient les bonnes variables
    print("\n[1/3] Vérification de la configuration...")
    check_config()
    print(f"  Host     : {DB_CONFIG['host']}")
    print(f"  Port     : {DB_CONFIG['port']}")
    print(f"  User     : {DB_CONFIG['user']}")
    print(f"  Database : {DB_CONFIG['database']}")
    print("  OK - Configuration lue depuis .env")

    # Étape 2 : établir la connexion
    print("\n[2/3] Connexion au serveur MySQL...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"  ECHEC : {e}")
        sys.exit(1)
    print("  OK - Connexion etablie")

    # Étape 3 : exécuter une requête simple pour valider
    print("\n[3/3] Execution d'une requete de verification...")
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION(), CURRENT_USER(), DATABASE();")
    version, user, database = cursor.fetchone()
    print(f"  Version MySQL   : {version}")
    print(f"  Utilisateur     : {user}")
    print(f"  Base courante   : {database}")

    cursor.close()
    conn.close()
    print("\n" + "=" * 60)
    print("SUCCES : L'environnement Python <-> MySQL est operationnel.")
    print("=" * 60)


if __name__ == "__main__":
    test_connection()