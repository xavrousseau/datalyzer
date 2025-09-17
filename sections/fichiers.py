# ============================================================
# Fichier : fichiers.py
# Objectif : Multi-chargement de fichiers (CSV, Excel, Parquet, TXT)
#            + Snapshots, aperçu, résumé analytique
# ============================================================

from __future__ import annotations

import os
import re
import base64
from io import BytesIO
from typing import Dict, List

import pandas as pd
import streamlit as st
from PIL import Image

from utils.snapshot_utils import (
    save_snapshot, list_snapshots, load_snapshot_by_name, delete_snapshot
)
from utils.log_utils import log_action
from utils.ui_utils import show_icon_header, show_footer

# ============================ Constantes & utilitaires =========================

KEY_DFS = "dfs"   # dict[str, pd.DataFrame] : fichiers chargés (tous)
KEY_DF = "df"     # pd.DataFrame : fichier actif

SUPPORTED_EXTS = [".csv", ".txt", ".xlsx", ".xls", ".parquet"]  # ordre stable pour l'uploader
PREVIEW_ROWS = 100


def _ensure_state() -> None:
    """Assure l'initialisation des clés de session nécessaires."""
    st.session_state.setdefault(KEY_DFS, {})


def _sanitize_key(s: str) -> str:
    """Transforme un nom libre en clé Streamlit stable (sans espaces/accents)."""
    s = s.strip().lower()
    return re.sub(r"[^\w\-\.]+", "_", s)


def _read_uploaded_file(file) -> pd.DataFrame:
    """
    Lit un fichier téléversé Streamlit (UploadedFile) vers un DataFrame selon son extension.
    - CSV/TXT : sep=None + engine='python' => sniff auto ; gère ; ; \t
    - Excel   : via pandas (openpyxl conseillé)
    - Parquet : via pyarrow/fastparquet
    """
    name = getattr(file, "name", "fichier_sans_nom")
    ext = os.path.splitext(name)[1].lower()

    if ext not in SUPPORTED_EXTS:
        raise ValueError(f"Format non pris en charge : {ext} (fichier {name})")

    try:
        if ext in {".csv", ".txt"}:
            df = pd.read_csv(file, sep=None, engine="python")
        elif ext in {".xlsx", ".xls"}:
            df = pd.read_excel(file)
        elif ext == ".parquet":
            df = pd.read_parquet(file)
        else:
            raise ValueError(f"Extension inattendue : {ext}")
    except Exception as e:
        raise RuntimeError(f"Erreur de lecture de {name} ({ext}) : {e}") from e

    # Optionnel : dédupliquer les colonnes si besoin
    # df = df.loc[:, ~df.columns.duplicated()]
    return df


def _summarize_dataframe(name: str, df: pd.DataFrame) -> Dict[str, object]:
    """Résumé synthétique : lignes, colonnes, % NA, top types."""
    rows, cols = df.shape
    total_cells = rows * cols
    na_pct = round((df.isna().sum().sum() / total_cells) * 100, 2) if total_cells else 0.0
    type_counts = df.dtypes.value_counts()
    top_types = ", ".join(type_counts.head(3).index.astype(str))
    return {"Fichier": name, "Lignes": rows, "Colonnes": cols, "NA (%)": na_pct, "Types dominants": top_types}


def _render_header_image() -> None:
    """Bannière décorative (base64). Fallback informatif si image absente."""
    image_path = "static/images/headers/header_waves_blossoms.png"
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
    except Exception:
        st.info("Aucune image d’en-tête trouvée.")


def _attach_as_active(df: pd.DataFrame, name: str) -> None:
    """
    Place le DataFrame dans le state :
      - l’ajoute à la liste des fichiers (`dfs`)
      - le définit comme actif (`df`)
    """
    st.session_state[KEY_DFS][name] = df
    st.session_state[KEY_DF] = df


# ============================== Vue principale ================================

def run_chargement() -> None:
    """
    Page 'Chargement & snapshots' :
      - Onglet 1 : téléversement multi-fichiers (CSV/XLSX/XLS/Parquet/TXT),
                   résumé des fichiers chargés, sélection d’un actif, aperçu.
      - Onglet 2 : gestion des snapshots (charger/supprimer).
    """
    _ensure_state()

    # En-tête visuel + titre
    _render_header_image()
    show_icon_header(
        "📂", "Chargement & snapshots",
        "Importez vos fichiers, sélectionnez le fichier actif, gérez les versions sauvegardées."
    )

    tab1, tab2 = st.tabs(["📥 Charger un fichier", "🕰️ Snapshots existants"])

    # -------------------------------------------------------------------------
    # Onglet 1 : Import de fichiers utilisateur
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("### 📥 Import de fichiers CSV, Excel, Parquet ou texte")

        uploaded_files = st.file_uploader(
            "Sélectionnez un ou plusieurs fichiers",
            type=[ext.strip(".") for ext in SUPPORTED_EXTS],
            accept_multiple_files=True,
        )

        for file in uploaded_files or []:
            name = getattr(file, "name", "fichier_sans_nom")
            try:
                df = _read_uploaded_file(file)

                # Nom de snapshot par défaut = nom de fichier sans extension
                default_snap = os.path.splitext(name)[0]
                snap_key = f"snap_name_{_sanitize_key(name)}"  # clé stable pour le widget
                snapshot_name = st.text_input(
                    f"Nom du snapshot pour {name}",
                    value=default_snap,
                    key=snap_key,
                    help="Nom lisible pour retrouver cette version (sans l’extension).",
                ) or default_snap

                # 🔧 Correction clé : on utilise bien "suffix", pas "label"
                save_snapshot(df, suffix=snapshot_name)
                log_action("import", f"{name} chargé")
                st.success(f"✅ Fichier **{name}** chargé ({df.shape[0]} lignes). Snapshot: {snapshot_name}")

                # Ajout/activation dans le state
                _attach_as_active(df, name)

            except RuntimeError as e:
                st.error(f"❌ {e}")
            except ValueError as e:
                st.warning(f"⚠️ {e}")
            except Exception as e:
                st.error(f"❌ Erreur inattendue lors du chargement de {name} : {e}")

        # Résumé des fichiers chargés
        if st.session_state[KEY_DFS]:
            st.markdown("### 🧾 Résumé des fichiers chargés")

            resume_rows = [
                _summarize_dataframe(fname, fdf)
                for fname, fdf in st.session_state[KEY_DFS].items()
            ]
            st.dataframe(pd.DataFrame(resume_rows), use_container_width=True)

            # Choix du fichier actif
            selected = st.selectbox(
                "📄 Sélectionner un fichier pour l’analyse détaillée",
                options=list(st.session_state[KEY_DFS].keys()),
                key="select_active_file",
                help="Le fichier actif est celui utilisé par les autres onglets/outils.",
            )
            st.session_state[KEY_DF] = st.session_state[KEY_DFS][selected]

            # Aperçu (expander)
            with st.expander(f"🔍 Aperçu du fichier : {selected}", expanded=True):
                df = st.session_state[KEY_DF]
                st.write(f"Dimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")
                st.dataframe(df.head(PREVIEW_ROWS), use_container_width=True)
        else:
            st.info("Aucun fichier chargé pour l’instant. Déposez des fichiers dans la zone ci-dessus.")

    # -------------------------------------------------------------------------
    # Onglet 2 : Snapshots enregistrés
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("### 📜 Snapshots sauvegardés")
        st.info("📘 Un snapshot est une copie horodatée d’un fichier importé. Il peut être rechargé à tout moment.")

        snapshots: List[str] = list_snapshots()

        if not snapshots:
            st.info("Aucun snapshot enregistré pour l’instant.")
        else:
            for snap in snapshots:
                safe = _sanitize_key(snap)
                col1, col2, col3 = st.columns([4, 1, 1], vertical_alignment="center")

                with col1:
                    st.write(f"📄 {snap}")

                with col2:
                    if st.button("🔄 Charger", key=f"load_{safe}", help="Remplace le fichier actif par ce snapshot"):
                        try:
                            df = load_snapshot_by_name(snap)
                            if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                                st.error("❌ Snapshot introuvable ou vide.")
                            else:
                                # On ajoute ce snapshot à la liste + on l’active
                                _attach_as_active(df, name=f"[SNAP] {snap}")
                                st.success(f"Snapshot **{snap}** chargé ({df.shape[0]} lignes).")
                                log_action("load_snapshot", snap)
                        except Exception as e:
                            st.error(f"❌ Erreur lors du chargement du snapshot '{snap}' : {e}")

                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_{safe}", help="Supprime définitivement ce snapshot"):
                        try:
                            delete_snapshot(snap)
                            log_action("delete_snapshot", snap)
                            st.rerun()  # rafraîchir la liste après suppression
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la suppression : {e}")

    # Footer
    show_footer("Xavier Rousseau", "xavier-data")
