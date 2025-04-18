# =============================================================================
# sections/chargement.py
#
# Ce module gère la première étape de l'application Streamlit :
# le chargement des fichiers de données CSV, XLSX ou Parquet.
# Il permet :
# - d'afficher les fichiers disponibles dans le dossier "data/inputs/"
# - de charger dynamiquement un ou plusieurs fichiers
# - de prévisualiser les 10 premières lignes du fichier actif
# - de stocker le fichier chargé dans la session Streamlit
# =============================================================================

import os                       # Pour lister les fichiers dans un dossier
import streamlit as st          # Framework d'interface web
import pandas as pd            # Manipulation de données
from pathlib import Path       # Manipulation robuste de chemins
from utils.log_utils import log_transformation   # Pour logguer le chargement
from utils.snapshot_utils import save_snapshot   # Pour sauvegarder le fichier chargé

# -----------------------------------------------------------------------------
# Fonction utilitaire : récupère les fichiers valides dans le dossier data/inputs
# -----------------------------------------------------------------------------
def get_available_files():
    input_dir = Path("data/inputs")
    input_dir.mkdir(parents=True, exist_ok=True)  # 👈 Crée le dossier s'il n'existe pas
    valid_exts = [".csv", ".xlsx", ".xls", ".parquet"]
    return [f.name for f in input_dir.iterdir() if f.suffix in valid_exts]

# -----------------------------------------------------------------------------
# Fonction principale : gère l’étape de chargement de fichier
# -----------------------------------------------------------------------------
def run_chargement():
    st.markdown("### 📂 Chargement de données")
    st.markdown("Sélectionnez un fichier à charger depuis `data/inputs/` pour démarrer.")

    available_files = get_available_files()

    if not available_files:
        st.warning("Aucun fichier disponible dans `data/inputs/`. Vous pouvez en déposer un manuellement via le menu latéral de Streamlit Cloud ou par Git.")
        return

    selected = st.selectbox("📁 Fichiers disponibles :", available_files)

    if st.button("✅ Valider ce fichier"):
        ext = Path(selected).suffix
        full_path = Path("data/inputs") / selected

        try:
            if ext == ".csv":
                df = pd.read_csv(full_path)
            elif ext == ".xlsx":
                df = pd.read_excel(full_path)
            elif ext == ".parquet":
                df = pd.read_parquet(full_path)
            else:
                st.error("Format non supporté.")
                return

            # Stockage dans la session pour les autres étapes
            st.session_state["df"] = df
            if "dfs" not in st.session_state:
                st.session_state["dfs"] = {}

            st.session_state["dfs"][selected] = df
            st.success(f"✅ Fichier chargé : {selected} ({df.shape[0]} lignes, {df.shape[1]} colonnes)")

            # Logging et snapshot
            log_transformation(f"Fichier {selected} chargé ({df.shape[0]} lignes)")
            save_snapshot("raw_input")

        except Exception as e:
            st.error(f"Erreur lors du chargement : {e}")
            return

    # Affichage du DataFrame si déjà chargé
    if "df" in st.session_state and st.session_state["df"] is not None:
        st.markdown(f"🔍 Fichier sélectionné : `{selected}`")
        st.dataframe(st.session_state["df"].head(10), use_container_width=True)
