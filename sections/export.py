# ============================================================
# Fichier : sections/export.py
# Objectif : Export des données avec sélection de colonnes,
#            format, logs, snapshot et téléchargement
# Version : enrichie, commentée, avec prévisualisation & compression
# ============================================================

from __future__ import annotations

import os
import re
import time
import base64
from io import BytesIO
from typing import Tuple

import pandas as pd
import streamlit as st
from PIL import Image

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_icon_header, show_footer

# =============================== Header visuel =================================
def _render_header_image() -> None:
    """
    Affiche une bannière en-tête centrée, avec fallback informatif en cas d'absence.
    Conserve l'approche base64 (style custom) pour éviter les chemins statiques relatifs
    cassés en prod (CDN) — alternative simple : st.image(..., use_container_width=True).
    """
    image_path = "static/images/headers/header_cherry_gateway.png"  
    try:
        img = Image.open(image_path).resize((900, 220))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        base64_img = base64.b64encode(buffer.getvalue()).decode("utf-8")

        st.markdown(
            f"""
            <div style='display:flex;justify-content:center;margin-bottom:1.5rem;'>
              <img src="data:image/png;base64,{base64_img}" alt="Bannière Datalyzer"
                   style="border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.2);" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        # On informe sans bloquer l'app (image décorative)
        st.info("Aucune image d’en-tête trouvée.")
        st.caption(f"(Détail : {e})")

# =============================== Helpers ======================================
def _sanitize_filename(name: str) -> str:
    """Rend un nom de fichier sûr (alphanumérique + _ - .)."""
    name = (name or "").strip()
    name = re.sub(r"[^\w\-.]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_.")
    return name or "export"

def _ensure_extension(filename: str, file_format: str) -> str:
    """Ajoute l'extension si manquante, en cohérence avec le format choisi."""
    ext = file_format.lower()
    if not filename.lower().endswith(f".{ext}"):
        return f"{filename}.{ext}"
    return filename

def _mime_for(fmt: str) -> str:
    """Type MIME par format."""
    return {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "parquet": "application/octet-stream",
    }.get(fmt, "application/octet-stream")

# =============================== Vue principale ================================
def run_export() -> None:
    """
    Page d'export :
      - Sélection du DataFrame actif
      - Choix des colonnes & format
      - Options (index, encodage, compression)
      - Écriture disque + téléchargement
      - Log + snapshot
    """
    # --- En-tête visuel (bannière base64 + titre) ---
    _render_header_image()
    show_icon_header(
        "💾", "Export du fichier final",
        "Choisissez les colonnes, le format et téléchargez votre fichier propre."
    )

    # --- Récupération du DF actif ---
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucune donnée disponible pour l’export.")
        return

    st.markdown(f"🔎 **Fichier actif : `{nom}`**")
    st.markdown(f"**{df.shape[0]} lignes × {df.shape[1]} colonnes**")

    # --- Sélection des colonnes ---
    st.markdown("### 🧩 Colonnes à inclure")
    selected_columns = st.multiselect(
        "Sélectionnez les colonnes à exporter",
        options=df.columns.tolist(),
        default=df.columns.tolist(),
        help="Décochez les colonnes inutiles pour un export plus léger."
    )
    st.write(f"🔢 **{len(selected_columns)} colonne(s) sélectionnée(s)**")
    if not selected_columns:
        st.info("Sélectionnez au moins une colonne pour poursuivre.")
        return

    with st.expander("🔍 Aperçu des colonnes sélectionnées", expanded=False):
        st.dataframe(df[selected_columns].head(50), use_container_width=True)

    # --- Options de base ---
    include_index = st.checkbox("Inclure l’index dans le fichier exporté", value=False)

    st.markdown("### 📦 Format du fichier")
    file_format = st.selectbox("Format", options=["csv", "xlsx", "json", "parquet"], index=0)

    col_enc, col_comp = st.columns(2)
    with col_enc:
        encoding = st.selectbox(
            "Encodage (CSV/JSON)",
            options=["utf-8", "utf-8-sig", "latin-1"],
            index=0,
            help="UTF-8 recommandé. 'utf-8-sig' ajoute BOM (utile pour Excel ancien)."
        ) if file_format in {"csv", "json"} else "utf-8"

    with col_comp:
        compression = st.selectbox(
            "Compression",
            options=["aucune", "gzip"],
            index=0,
            help="CSV/JSON/Parquet supportent gzip. XLSX est déjà compressé."
        ) if file_format in {"csv", "json", "parquet"} else "aucune"

    # --- Nom de fichier proposé ---
    ts = int(time.time())
    default_base = _sanitize_filename(f"export_final_{ts}")
    file_name_input = st.text_input(
        "Nom du fichier exporté (sans extension ou avec extension correspondante)",
        value=default_base
    )
    file_name_input = _sanitize_filename(file_name_input)
    file_name = _ensure_extension(file_name_input, file_format)

    # --- Action d'export ---
    st.markdown("### ⬇️ Génération du fichier")
    if st.button("📥 Générer et télécharger le fichier", type="primary"):
        try:
            df_export = df[selected_columns]

            export_dir = os.path.join("data", "exports")
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, file_name)

            if file_format == "csv":
                comp = "gzip" if compression == "gzip" else None
                df_export.to_csv(
                    export_path,
                    index=include_index,
                    encoding=encoding,
                    lineterminator="\n",
                    compression=comp
                )
            elif file_format == "xlsx":
                df_export.to_excel(export_path, index=include_index, engine="openpyxl")
            elif file_format == "json":
                if compression == "gzip":
                    df_export.to_json(export_path, orient="records", force_ascii=False, compression="gzip")
                else:
                    df_export.to_json(export_path, orient="records", force_ascii=False)
            elif file_format == "parquet":
                comp = "gzip" if compression == "gzip" else None
                df_export.to_parquet(export_path, index=include_index, compression=comp)
            else:
                raise ValueError(f"Format non géré : {file_format}")

            # --- Log + snapshot (lisible, non compressé) ---
            save_snapshot(df_export, label="export_final", suffix=file_format)
            log_action(
                "export",
                f"{file_name} — {len(selected_columns)} colonnes — format={file_format} — comp={compression}"
            )

            # --- Téléchargement ---
            with open(export_path, "rb") as f:
                payload = f.read()

            st.success(f"✅ Fichier exporté : **{file_name}**")
            st.download_button(
                label="📥 Télécharger maintenant",
                data=payload,
                file_name=file_name,
                mime=_mime_for(file_format)
            )
            st.caption(f"Fichier enregistré sur disque : `{export_path}`")

        except Exception as e:
            st.error(f"❌ Erreur pendant l’export : {e}")

    # --- Pied de page ---
    show_footer("Xavier Rousseau", "xavier-data")
