# ============================================================
# Fichier : log_utils.py
# Objectif : Journalisation des actions utilisateurs dans Datalyzer
# (import, corrections, export, suppressions, erreurs…)
# ============================================================

import os
import csv
from datetime import datetime
import streamlit as st
import pandas as pd

# Répertoire & chemin du fichier de log
LOG_PATH = "logs/history_log.csv"
os.makedirs("logs", exist_ok=True)

def log_action(action_type: str, message: str, display: bool = True):
    """
    Enregistre une action dans le fichier de log CSV, et l’affiche en console si souhaité.

    Args:
        action_type (str): Type d’action (import, export, nettoyage…)
        message (str): Message associé à l’action
        display (bool): Affiche ou non dans la console (utile pour debug)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ligne = [timestamp, action_type, message]

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ligne)

    if display:
        print(f"[{timestamp}] [{action_type.upper()}] {message}")

def append_log(path: str, headers: list[str], values: list):
    """
    Ajoute une ligne dans un fichier CSV avec entête personnalisée (ex : logs d’export).

    Args:
        path (str): Chemin du fichier à créer ou enrichir
        headers (list): Liste des noms de colonnes
        values (list): Valeurs à écrire dans l’ordre
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.isfile(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(values)

    print(f"[LOG] Ligne ajoutée à {path} : {values}")

def display_log(path: str = LOG_PATH):
    """
    Affiche le journal des logs dans Streamlit (ordre inverse = plus récents en haut).
    Permet aussi de filtrer par type d’action (facultatif).
    """
    if not os.path.exists(path):
        st.info("📭 Aucun log enregistré pour le moment.")
        return

    df_log = pd.read_csv(path, names=["Horodatage", "Type", "Message"])
    action_types = df_log["Type"].unique().tolist()
    selected = st.multiselect("🔎 Filtrer par type d'action", options=action_types, default=action_types)
    filtered = df_log[df_log["Type"].isin(selected)]

    st.dataframe(filtered[::-1], use_container_width=True)

def log_error(message: str, context: str = "général"):
    """
    Log une erreur critique (prévu pour extension).

    Args:
        message (str): Détail de l’erreur
        context (str): Contexte ou module concerné
    """
    log_action("error", f"[{context}] {message}")

def clear_logs(path: str = LOG_PATH):
    """
    Supprime le contenu du fichier de log (utile en dev/test).
    """
    if os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.truncate(0)
        st.success("🧹 Logs purgés avec succès.")
    else:
        st.warning("📭 Aucun fichier de log à purger.")
