# ============================================================
# Fichier : fichiers.py
# Objectif : Multi-chargement de fichiers CSV, Excel, Parquet, Texte
#            + Snapshots, aperçu, résumé analytique
# Version améliorée avec filtres, personnalisation et gestion des erreurs
# ============================================================

import streamlit as st
import pandas as pd
import os

from utils.snapshot_utils import (
    save_snapshot,
    list_snapshots,
    load_snapshot_by_name,
    delete_snapshot
)
from utils.log_utils import log_action
from utils.ui_utils import show_header_image, show_icon_header, show_footer

def run_chargement():
    # === En-tête visuel principal ===
    show_header_image("bg_upload_file.png")
    show_icon_header(
        "📂", "Chargement & snapshots",
        "Importez vos fichiers, sélectionnez le fichier actif, gérez les versions sauvegardées."
    )

    tab1, tab2 = st.tabs(["📥 Charger un fichier", "🕰️ Snapshots existants"])

    # ============================================================
    # Onglet 1 : Import de fichiers utilisateur
    # ============================================================
    with tab1:
        st.markdown("### 📥 Import de fichiers CSV, Excel, Parquet ou texte")
        uploaded_files = st.file_uploader(
            "Sélectionnez un ou plusieurs fichiers",
            type=["csv", "xlsx", "xls", "parquet", "txt"],
            accept_multiple_files=True
        )

        # Initialisation si besoin
        st.session_state.setdefault("dfs", {})

        for file in uploaded_files or []:
            try:
                ext = os.path.splitext(file.name)[1].lower()

                if ext in [".csv", ".txt"]:
                    df = pd.read_csv(file, sep=None, engine="python")
                elif ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file)
                elif ext == ".parquet":
                    df = pd.read_parquet(file)
                else:
                    st.warning(f"❌ Format non pris en charge : {file.name}")
                    continue

                # Demander un nom de snapshot personnalisé
                snapshot_name = st.text_input(f"Nom du snapshot pour {file.name}", value=file.name)
                if not snapshot_name:
                    snapshot_name = os.path.splitext(file.name)[0]

                # Mise à jour des données dans le session state
                st.session_state["dfs"][file.name] = df
                st.session_state["df"] = df  # Dernière sélection active

                # Sauvegarder un snapshot
                save_snapshot(df, label=snapshot_name)
                log_action("import", f"{file.name} chargé")
                st.success(f"✅ Fichier **{file.name}** chargé ({df.shape[0]} lignes).")

            except Exception as e:
                st.error(f"❌ Erreur lors du chargement de {file.name} : {e}")

        # === Résumé des fichiers chargés ===
        if st.session_state["dfs"]:
            st.markdown("### 🧾 Résumé des fichiers chargés")
            resume_data = []
            for name, df in st.session_state["dfs"].items():
                na_pct = (df.isna().sum().sum() / (df.shape[0] * df.shape[1])) * 100 if df.size > 0 else 0
                types = ", ".join(df.dtypes.value_counts().head(3).index.astype(str))
                resume_data.append({
                    "Fichier": name,
                    "Lignes": df.shape[0],
                    "Colonnes": df.shape[1],
                    "NA (%)": round(na_pct, 2),
                    "Types dominants": types
                })

            st.dataframe(pd.DataFrame(resume_data), use_container_width=True)

            # Choix du fichier actif
            selected = st.selectbox(
                "📄 Sélectionner un fichier pour l’analyse détaillée",
                options=list(st.session_state["dfs"].keys())
            )
            st.session_state["df"] = st.session_state["dfs"][selected]

            with st.expander(f"🔍 Aperçu du fichier : {selected}", expanded=True):
                st.write(f"Dimensions : {st.session_state['df'].shape[0]} lignes × {st.session_state['df'].shape[1]} colonnes")
                st.dataframe(st.session_state["df"].head(100), use_container_width=True)

    # ============================================================
    # Onglet 2 : Snapshots enregistrés
    # ============================================================
    with tab2:
        st.markdown("### 📜 Snapshots sauvegardés")
        st.info("📘 Un snapshot est une copie horodatée d’un fichier importé. Il peut être rechargé à tout moment.")

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

    # === Footer personnalisé ===
    show_footer("Xavier Rousseau", "xavier-data")
