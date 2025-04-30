# =============================================================================
# sections/chargement.py
#
# Ce module gère la première étape de l'application Streamlit :
# le chargement de fichiers de données CSV, Excel ou Parquet.
# Il permet :
# - de charger dynamiquement un fichier utilisateur (glisser-déposer)
# - de prévisualiser les 10 premières lignes du fichier actif
# - de stocker le fichier chargé dans la session Streamlit
# =============================================================================

import streamlit as st
import pandas as pd
from pathlib import Path
from utils.log_utils import log_transformation
from utils.snapshot_utils import save_snapshot

# -----------------------------------------------------------------------------
# Fonction principale : chargement interactif d’un fichier utilisateur
# -----------------------------------------------------------------------------
def run_chargement():
    st.markdown("### 📂 Chargement de données")
    st.markdown("Chargez un fichier **CSV**, **Excel** ou **Parquet** à analyser.")

    uploaded_file = st.file_uploader("📤 Déposez un fichier ou cliquez ici :", type=["csv", "xlsx", "xls", "parquet"])

    if uploaded_file:
        try:
            ext = Path(uploaded_file.name).suffix
            if ext == ".csv":
                df = pd.read_csv(uploaded_file)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(uploaded_file)
            elif ext == ".parquet":
                df = pd.read_parquet(uploaded_file)
            else:
                st.error("❌ Format non supporté.")
                return

            # Stockage dans la session
            st.session_state["df"] = df
            if "dfs" not in st.session_state:
                st.session_state["dfs"] = {}
            st.session_state["dfs"][uploaded_file.name] = df

            # Feedback
            st.success(f"✅ Fichier chargé : `{uploaded_file.name}` ({df.shape[0]} lignes, {df.shape[1]} colonnes)")
            log_transformation(f"Fichier {uploaded_file.name} chargé ({df.shape[0]} lignes)")
            save_snapshot("raw_input")

            # Aperçu
            st.dataframe(df.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"❌ Erreur lors du chargement : {e}")
    else:
        st.info("💡 Déposez un fichier ci-dessus pour commencer.")
