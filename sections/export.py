# ============================================================
# Fichier : sections/export.py
# Objectif : Export des données avec sélection de colonnes,
#            format, logs, snapshot et téléchargement
# Version : enrichie, commentée, avec prévisualisation & compression
# Design  : API UI unifiée (section_header, show_footer)
# Auteur  : Xavier Rousseau
# ============================================================

from __future__ import annotations

import os
import re
import time
from typing import Tuple

import pandas as pd
import streamlit as st

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import section_header, show_footer  # ← unifié


# =============================== Helpers ======================================

def _sanitize_filename(name: str) -> str:
    """
    Produit un nom de fichier « sûr » (alphanumérique + '_' + '-' + '.').

    Pourquoi :
      - Évite les caractères problématiques (espaces, guillemets, diacritiques)
        pour des systèmes de fichiers variés et des usages web.

    Paramètres
    ----------
    name : str
        Base proposée par l'utilisateur (peut être vide).

    Retour
    ------
    str
        Nom nettoyé, compacté, sans pré/suffixes '_' ou '.', ou "export" par défaut.
    """
    name = (name or "").strip()
    name = re.sub(r"[^\w\-.]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_.")
    return name or "export"


def _ensure_extension(filename: str, file_format: str) -> str:
    """
    Garantit que le nom se termine par l'extension cohérente avec `file_format`.

    Exemple :
      ("report", "csv")   -> "report.csv"
      ("report.CSV", "csv") -> "report.CSV" (déjà ok, insensible à la casse)
    """
    ext = file_format.lower()
    if not filename.lower().endswith(f".{ext}"):
        return f"{filename}.{ext}"
    return filename


def _mime_for(fmt: str) -> str:
    """
    Retourne le type MIME pour le bouton de téléchargement.

    Remarque :
      - Parquet n'a pas de consensus parfait ; on utilise 'application/octet-stream'
        pour une compat générique (navigateurs/OS).
    """
    return {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "json": "application/json",
        "parquet": "application/octet-stream",
    }.get(fmt, "application/octet-stream")


# =============================== Vue principale ================================

def run_export() -> None:
    """
    Affiche la page « Export du fichier final ».

    Parcours utilisateur :
      1) Récupération du DataFrame actif (source de vérité).
      2) Sélection des colonnes à inclure (prévisualisation bornée).
      3) Choix du format (CSV/XLSX/JSON/Parquet), index, encodage, compression.
      4) Génération du fichier sur disque (data/exports) + payload mémoire.
      5) Snapshot + log + bouton de téléchargement.

    Dépendances attendues :
      - `get_active_dataframe()` -> (df: pd.DataFrame | None, nom: str)
      - `save_snapshot(df, suffix=...)` pour archivage léger
      - `log_action(event, details)` pour la traçabilité
      - `section_header(...)` / `show_footer(...)` pour l’UX unifiée

    Sécurité & perf :
      - Prévisualisation limitée (head(50)).
      - Encodage explicite pour CSV/JSON (UTF-8 par défaut).
      - Compression 'gzip' optionnelle (CSV/JSON/Parquet).
    """
    # ---------- En-tête unifié : bannière + titre + baseline ----------
    section_header(
        title="Export du fichier final",
        subtitle="Choisissez les colonnes, le format et téléchargez votre fichier propre.",
        section="export",   # → config.SECTION_BANNERS["export"]
        emoji="💾",
    )

    # ---------- Récupération du DF actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucune donnée disponible pour l’export.")
        return

    st.markdown(f"🔎 **Fichier actif : `{nom}`**")
    st.markdown(f"**{df.shape[0]} lignes × {df.shape[1]} colonnes**")

    # ---------- Sélection des colonnes ----------
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

    # ---------- Options de base ----------
    include_index = st.checkbox("Inclure l’index dans le fichier exporté", value=False)

    st.markdown("### 📦 Format du fichier")
    file_format = st.selectbox("Format", options=["csv", "xlsx", "json", "parquet"], index=0)

    col_enc, col_comp = st.columns(2)

    # Encodage : pertinent pour CSV/JSON uniquement
    with col_enc:
        encoding = (
            st.selectbox(
                "Encodage (CSV/JSON)",
                options=["utf-8", "utf-8-sig", "latin-1"],
                index=0,
                help=(
                    "UTF-8 recommandé. 'utf-8-sig' ajoute un BOM (utile pour Excel ancien) ; "
                    "'latin-1' seulement si vous ciblez un outil qui ne lit pas l’UTF-8."
                ),
            )
            if file_format in {"csv", "json"}
            else "utf-8"
        )

    # Compression : XLSX est déjà zippé par nature (format OOXML)
    with col_comp:
        compression = (
            st.selectbox(
                "Compression",
                options=["aucune", "gzip"],
                index=0,
                help="CSV/JSON/Parquet supportent gzip. XLSX est déjà compressé.",
            )
            if file_format in {"csv", "json", "parquet"}
            else "aucune"
        )

    # ---------- Nom de fichier proposé ----------
    ts = int(time.time())
    default_base = _sanitize_filename(f"export_final_{ts}")
    file_name_input = st.text_input(
        "Nom du fichier exporté (sans extension ou avec extension correspondante)",
        value=default_base,
    )
    file_name_input = _sanitize_filename(file_name_input)
    file_name = _ensure_extension(file_name_input, file_format)

    # ---------- Action d'export ----------
    st.markdown("### ⬇️ Génération du fichier")
    if st.button("📥 Générer et télécharger le fichier", type="primary"):
        try:
            # 1) Sous-ensemble de colonnes
            df_export = df[selected_columns]

            # 2) Prépare le répertoire cible (persistant pour audit)
            export_dir = os.path.join("data", "exports")
            os.makedirs(export_dir, exist_ok=True)
            export_path = os.path.join(export_dir, file_name)

            # 3) Écriture selon format
            if file_format == "csv":
                comp = "gzip" if compression == "gzip" else None
                # lineterminator '\n' : compatible Unix/Win, évite '\r\n\r\n'
                df_export.to_csv(
                    export_path,
                    index=include_index,
                    encoding=encoding,
                    lineterminator="\n",
                    compression=comp,
                )

            elif file_format == "xlsx":
                # Remarque : engine="openpyxl" → coherent avec requirements.
                # Si taille très grande, xlsxwriter peut être plus rapide.
                df_export.to_excel(export_path, index=include_index, engine="openpyxl")

            elif file_format == "json":
                comp = "gzip" if compression == "gzip" else None
                # orient="records" : JSON lisible pour ingestion/outils BI.
                # force_ascii=False : préserver les accents.
                df_export.to_json(
                    export_path,
                    orient="records",
                    force_ascii=False,
                    compression=comp,
                )

            elif file_format == "parquet":
                comp = "gzip" if compression == "gzip" else None
                # Parquet : typage préservé, stockage colonne, idéal gros volumes.
                df_export.to_parquet(export_path, index=include_index, compression=comp)

            else:
                raise ValueError(f"Format non géré : {file_format}")

            # 4) Log + snapshot (suffix = format ; lisible dans l’historique)
            save_snapshot(df_export, suffix=file_format)
            log_action(
                "export",
                f"{file_name} — {len(selected_columns)} colonnes — format={file_format} — comp={compression}",
            )

            # 5) Prépare le payload pour le bouton de téléchargement
            with open(export_path, "rb") as f:
                payload = f.read()

            st.success(f"✅ Fichier exporté : **{file_name}**")
            st.download_button(
                label="📥 Télécharger maintenant",
                data=payload,
                file_name=file_name,
                mime=_mime_for(file_format),
            )
            st.caption(f"Fichier enregistré sur disque : `{export_path}`")

        except Exception as e:
            # Message concis côté UI ; détails supplémentaires possibles côté logs serveur.
            st.error(f"❌ Erreur pendant l’export : {e}")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
