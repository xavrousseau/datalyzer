# ============================================================
# Fichier : export.py
# Objectif : Export des données avec sélection de colonnes,
# format, logs, snapshot et téléchargement
# Version enrichie avec personnalisation, prévisualisation et compression
# ============================================================

import streamlit as st
import pandas as pd
import os
import time

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image, show_icon_header, show_footer

def run_export():
    # === En-tête visuel ===
    show_header_image("bg_export_peace.png")
    show_icon_header("💾", "Export du fichier final",
                     "Choisissez les colonnes, le format et téléchargez votre fichier propre.")

    # 🔁 Récupération du fichier actif
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucune donnée disponible pour l’export.")
        return

    st.markdown(f"🔎 **Fichier actif : `{nom}`**")
    st.markdown(f"**{df.shape[0]} lignes × {df.shape[1]} colonnes**")

    # === Sélection des colonnes à inclure ===
    st.markdown("### 🧩 Colonnes à inclure")
    selected_columns = st.multiselect(
        "Sélectionnez les colonnes à exporter",
        options=df.columns.tolist(),
        default=df.columns.tolist()
    )
    st.write(f"🔢 **{len(selected_columns)} colonne(s) sélectionnée(s)**")

    # Option pour inclure l'index
    include_index = st.checkbox("Inclure l’index dans le fichier exporté", value=False)

    # Choix du format d’export
    st.markdown("### 📦 Format du fichier")
    file_format = st.selectbox("Format", options=["csv", "xlsx", "json", "parquet"], index=0)

    # Nom du fichier exporté
    default_name = f"export_final_{int(time.time())}.{file_format}"
    file_name = st.text_input("Nom du fichier exporté", value=default_name)

    # === Export ===
    if st.button("📥 Générer et télécharger le fichier"):
        try:
            df_export = df[selected_columns]
            os.makedirs("data/exports", exist_ok=True)
            export_path = os.path.join("data/exports", file_name)

            # Sauvegarde selon format
            if file_format == "csv":
                df_export.to_csv(export_path, index=include_index)
            elif file_format == "xlsx":
                df_export.to_excel(export_path, index=include_index)
            elif file_format == "json":
                df_export.to_json(export_path, orient="records")
            elif file_format == "parquet":
                df_export.to_parquet(export_path, index=include_index, compression="gzip")

            # Log + snapshot
            save_snapshot(df_export, suffix="export")
            log_action("export", f"{file_name} - {len(selected_columns)} colonnes - format {file_format}")

            # Détection du type MIME
            mime_types = {
                "csv": "text/csv",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "json": "application/json",
                "parquet": "application/octet-stream"
            }
            mime = mime_types.get(file_format, "application/octet-stream")

            st.success(f"✅ Fichier exporté : {file_name}")
            st.download_button(
                label="📥 Télécharger maintenant",
                data=open(export_path, "rb").read(),
                file_name=file_name,
                mime=mime
            )

        except Exception as e:
            st.error(f"❌ Erreur pendant l’export : {e}")

    # Footer
    show_footer("Xavier Rousseau", "xavier-data")
