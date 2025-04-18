# sections/chargement.py

import streamlit as st
import pandas as pd
import csv
from io import StringIO
from utils.filters import select_active_dataframe
from utils.log_utils import log_transformation

def run_chargement():
    st.markdown("## 📂 Chargement de fichiers")
    st.markdown("Téléversez un ou plusieurs fichiers de données pour commencer l'analyse.")

    # Choix des extensions supportées
    uploaded_files = st.file_uploader(
        "Sélectionnez un ou plusieurs fichiers",
        type=["csv", "xlsx", "parquet"],
        accept_multiple_files=True
    )

    # Initialisation du dictionnaire de dataframes en session
    if "dfs" not in st.session_state:
        st.session_state["dfs"] = {}

    # Chargement des fichiers
    if uploaded_files:
        for file in uploaded_files:
            name = file.name
            ext = name.split(".")[-1].lower()
            try:
                if ext == "csv":
                    text = file.read().decode("utf-8", errors="ignore")
                    sep = csv.Sniffer().sniff(text[:2048]).delimiter
                    df = pd.read_csv(StringIO(text), sep=sep)
                elif ext == "xlsx":
                    df = pd.read_excel(file)
                elif ext == "parquet":
                    df = pd.read_parquet(file)
                else:
                    st.warning(f"⚠️ Format non supporté : {ext}")
                    continue

                # Sauvegarde dans la session
                st.session_state["dfs"][name] = df
                st.success(f"✅ {name} chargé ({df.shape[0]} lignes × {df.shape[1]} colonnes)")
                log_transformation(f"Chargement : {name} – {df.shape[0]} lignes")

            except Exception as e:
                st.error(f"❌ Erreur de lecture pour {name} : {e}")

    # Affichage de l'aperçu du fichier principal sélectionné
    if st.session_state["dfs"]:
        st.markdown("### 🔍 Fichier sélectionné")
        df, selected_name = select_active_dataframe()
        st.markdown(f"**Fichier actif : `{selected_name}`**")
        st.dataframe(df.head(10), use_container_width=True)
