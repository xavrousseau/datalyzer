# ============================================================
# Fichier : fichiers.py
# Objectif : Chargement de plusieurs fichiers + snapshots
# Version corrigée Streamlit
# ============================================================

import streamlit as st
import pandas as pd
import os

from utils.snapshot_utils import save_snapshot, list_snapshots, load_snapshot_by_name, delete_snapshot
from utils.log_utils import log_action
from utils.ui_utils import show_header_image


def run_chargement():
    show_header_image("bg_upload_file.png")
    st.title("📂 Chargement et gestion des fichiers")

    tab1, tab2 = st.tabs(["📥 Charger un fichier", "🕰️ Snapshots existants"])

    # ========== Onglet 1 : Chargement ==========
    with tab1:
        st.markdown("### 📥 Import de fichiers CSV ou Excel")

        uploaded_files = st.file_uploader("Sélectionnez un ou plusieurs fichiers", type=["csv", "xlsx"], accept_multiple_files=True)

        if "dfs" not in st.session_state:
            st.session_state["dfs"] = {}

        if uploaded_files:
            for file in uploaded_files:
                try:
                    if file.name.endswith(".csv"):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)

                    st.session_state["dfs"][file.name] = df
                    st.session_state["df"] = df  # dernière sélection par défaut
                    save_snapshot(df, label=os.path.splitext(file.name)[0])
                    log_action("import", f"{file.name} chargé")

                    st.success(f"✅ Fichier **{file.name}** chargé avec succès ({df.shape[0]} lignes).")

                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement de {file.name} : {e}")

        # Choix du fichier actif
        if st.session_state["dfs"]:
            selected = st.selectbox("📄 Fichier à analyser", options=list(st.session_state["dfs"].keys()))
            st.session_state["df"] = st.session_state["dfs"][selected]
            st.dataframe(st.session_state["df"].head(), use_container_width=True)

    # ========== Onglet 2 : Snapshots ==========
    with tab2:
        st.markdown("### 📜 Snapshots sauvegardés")
        snapshots = list_snapshots()

        if not snapshots:
            st.info("Aucun snapshot enregistré pour l’instant.")
        else:
            for snap in snapshots:
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.write(f"📄 {snap}")
                with col2:
                    if st.button("🔄 Charger", key=f"load_{snap}"):
                        df = load_snapshot_by_name(snap)
                        st.session_state.df = df
                        st.success(f"Snapshot **{snap}** chargé ({df.shape[0]} lignes).")
                        log_action("load_snapshot", snap)
                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_{snap}"):
                        delete_snapshot(snap)
                        log_action("delete_snapshot", snap)
                        st.success(f"Snapshot **{snap}** supprimé.")
                        st.experimental_rerun()
