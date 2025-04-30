# ============================================================
# Fichier : export.py
# Objectif : Export des données avec sélection de colonnes,
# choix du format, logs, snapshot et téléchargement
# ============================================================

import streamlit as st
import pandas as pd
import os

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.ui_utils import show_header_image

def run_export(df: pd.DataFrame):
    # 🎴 Image décorative
    show_header_image("bg_export_peace.png")

    st.title("💾 Export du fichier final")

    if df is None or df.empty:
        st.warning("❌ Aucune donnée disponible pour l’export.")
        return

    # Aperçu global
    st.markdown(f"🔎 **Fichier actif : `{st.session_state.get('global_df_selector', 'dataframe')}`**")
    st.markdown(f"**{df.shape[0]} lignes × {df.shape[1]} colonnes**")

    # Sélection des colonnes à exporter
    st.markdown("### 🧩 Colonnes à inclure")
    selected_columns = st.multiselect("Sélectionnez les colonnes", df.columns.tolist(), default=df.columns.tolist())

    # Choix du format d’export
    st.markdown("### 📦 Format du fichier")
    file_format = st.selectbox("Format", options=["csv", "xlsx", "json", "parquet"], index=0)

    # Nom du fichier
    file_name = st.text_input("Nom du fichier exporté", value=f"export_final.{file_format}")

    # Génération du fichier exporté
    if st.button("📥 Générer et télécharger le fichier"):
        try:
            df_export = df[selected_columns]

            # Création du répertoire d'exports
            os.makedirs("data/exports", exist_ok=True)
            export_path = os.path.join("data/exports", file_name)

            # Sauvegarde dans le format choisi
            if file_format == "csv":
                df_export.to_csv(export_path, index=False)
            elif file_format == "xlsx":
                df_export.to_excel(export_path, index=False)
            elif file_format == "json":
                df_export.to_json(export_path, orient="records")
            elif file_format == "parquet":
                df_export.to_parquet(export_path, index=False)

            # Log et snapshot
            save_snapshot(df_export, suffix="export")
            log_action("export", f"{file_name} - {len(selected_columns)} colonnes - format {file_format}")

            st.success(f"✅ Fichier exporté : {file_name}")
            st.download_button(
                label="📥 Télécharger maintenant",
                data=open(export_path, "rb").read(),
                file_name=file_name,
                mime="text/csv" if file_format == "csv" else None
            )

        except Exception as e:
            st.error(f"❌ Erreur pendant l’export : {e}")
