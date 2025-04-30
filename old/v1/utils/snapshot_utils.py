# ============================================================
# Fichier : snapshot_utils.py
# Objectif : Gestion centralisée des snapshots dans Datalyzer
# (sauvegarde, chargement, suppression, dernier snapshot)
# Version enrichie avec feedback utilisateur et résumé
# ============================================================

import os
import pandas as pd
from datetime import datetime
import streamlit as st

# Répertoire de base pour stocker les snapshots
SNAPSHOT_DIR = "data/snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

def save_snapshot(df: pd.DataFrame, label: str = None, suffix: str = None) -> str:
    """
    Sauvegarde un DataFrame dans un fichier CSV nommé automatiquement.
    Affiche un message de confirmation dans Streamlit.

    Args:
        df (pd.DataFrame): Données à sauvegarder
        label (str): Nom de base du fichier (optionnel)
        suffix (str): Suffixe à ajouter au nom du fichier

    Returns:
        str: Chemin complet du fichier créé
    """
    base_name = label or datetime.now().strftime("snapshot_%Y%m%d_%H%M%S")
    if suffix:
        base_name += f"_{suffix}"

    path = os.path.join(SNAPSHOT_DIR, f"{base_name}.csv")
    df.to_csv(path, index=False)
    st.success(f"📸 Snapshot sauvegardé : `{base_name}.csv` ({len(df)} lignes)")
    return path

def list_snapshots() -> list:
    """
    Liste tous les fichiers snapshot disponibles (triés par nom).

    Returns:
        list: Noms de fichiers CSV présents dans le répertoire de snapshots
    """
    if not os.path.exists(SNAPSHOT_DIR):
        return []
    return sorted([f for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".csv")])

def load_snapshot_by_name(name: str) -> pd.DataFrame:
    """
    Charge un snapshot par son nom de fichier.

    Args:
        name (str): Nom du fichier (avec .csv)

    Returns:
        pd.DataFrame: Contenu du snapshot
    """
    path = os.path.join(SNAPSHOT_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Snapshot introuvable : {path}")
    return pd.read_csv(path)

def load_latest_snapshot() -> pd.DataFrame:
    """
    Charge automatiquement le dernier snapshot disponible.

    Returns:
        pd.DataFrame: Contenu du fichier le plus récent
    """
    snapshots = list_snapshots()
    if not snapshots:
        raise FileNotFoundError("Aucun snapshot disponible.")
    return load_snapshot_by_name(snapshots[-1])

def delete_snapshot(name: str):
    """
    Supprime un snapshot par son nom de fichier.

    Args:
        name (str): Nom du fichier .csv à supprimer
    """
    path = os.path.join(SNAPSHOT_DIR, name)
    if os.path.exists(path):
        os.remove(path)
        st.info(f"🗑️ Snapshot supprimé : {name}")
    else:
        st.warning(f"⚠️ Fichier non trouvé pour suppression : {name}")

def get_snapshot_info(name: str):
    """
    Affiche un résumé rapide d’un snapshot : nombre de lignes et colonnes.

    Args:
        name (str): Nom du fichier snapshot
    """
    path = os.path.join(SNAPSHOT_DIR, name)
    if not os.path.exists(path):
        st.warning("❌ Snapshot introuvable.")
        return

    df = pd.read_csv(path)
    st.write(f"🗂️ **{name}** — {len(df)} lignes, {len(df.columns)} colonnes")
