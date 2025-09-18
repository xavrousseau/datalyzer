# ============================================================
# Fichier : sections/fichiers.py
# Objectif : Multi-chargement (CSV, Excel, Parquet, TXT)
#            + Snapshots, aperçu, résumé analytique
# Design   : API UI unifiée (section_header, show_footer)
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import os
import re
from typing import List

import pandas as pd
import streamlit as st

from utils.snapshot_utils import (
    save_snapshot, list_snapshots, load_snapshot_by_name, delete_snapshot
)
from utils.log_utils import log_action
from utils.ui_utils import section_header, show_footer  # <— API UI unifiée


# ============================ Constantes & utilitaires =========================

# Clés de session centralisées :
# - KEY_DFS : tous les DataFrames téléversés (nom_fichier -> df)
# - KEY_DF  : DataFrame « actif » (utilisé par d'autres pages/outils)
KEY_DFS = "dfs"   # dict[str, pd.DataFrame]
KEY_DF = "df"     # pd.DataFrame

# Extensions supportées (et ordre d’affichage stable dans l’uploader).
SUPPORTED_EXTS = [".csv", ".txt", ".xlsx", ".xls", ".parquet"]

# Nombre maximal de lignes affichées dans l’aperçu pour préserver la réactivité.
PREVIEW_ROWS = 100


def _ensure_state() -> None:
    """Assure l'initialisation des clés de session nécessaires."""
    st.session_state.setdefault(KEY_DFS, {})


def _sanitize_key(s: str) -> str:
    """
    Transforme un libellé libre en *clé* Streamlit stable (sans espaces/accents).
    Exemple : "Mon Fichier (v1).csv" -> "mon_fichier_v1_csv"
    """
    s = s.strip().lower()
    return re.sub(r"[^\w\-\.]+", "_", s)


def _read_uploaded_file(file) -> pd.DataFrame:
    """
    Lit un fichier téléversé (Streamlit UploadedFile) en DataFrame selon l’extension.

    - CSV/TXT : sep=None + engine="python" → *sniff* automatique de ; , \t …
    - Excel   : via pandas (engine openpyxl recommandé en requirements).
    - Parquet : via pyarrow/fastparquet selon dispo.
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

    return df


def _summarize_dataframe(name: str, df: pd.DataFrame) -> dict[str, object]:
    """
    Résumé synthétique :
      - Lignes, Colonnes
      - % de valeurs manquantes
      - 3 types dominants
    """
    rows, cols = df.shape
    total_cells = rows * cols
    na_pct = round((df.isna().sum().sum() / total_cells) * 100, 2) if total_cells else 0.0
    type_counts = df.dtypes.value_counts()
    top_types = ", ".join(type_counts.head(3).index.astype(str))
    return {"Fichier": name, "Lignes": rows, "Colonnes": cols, "NA (%)": na_pct, "Types dominants": top_types}


def _attach_as_active(df: pd.DataFrame, name: str) -> None:
    """
    Ajoute le DataFrame dans KEY_DFS et le définit comme actif (KEY_DF).
    """
    st.session_state[KEY_DFS][name] = df
    st.session_state[KEY_DF] = df


# === Cache léger pour éviter de recharger un snapshot plusieurs fois durant la session ===
@st.cache_data(show_spinner=False)
def _load_snapshot_cached(snap_name: str) -> pd.DataFrame:
    df = load_snapshot_by_name(snap_name)
    # On ne retourne jamais None ici : si problème, on lève pour affichage propre côté UI
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError("Snapshot introuvable ou vide.")
    return df


# ============================== Vue principale ================================

def run_chargement() -> None:
    """
    Page « Chargement & snapshots ».

    Onglets :
      1) Import multi-fichiers (CSV/XLSX/XLS/Parquet/TXT)
         - Résumé des fichiers chargés
         - Sélection du fichier actif
         - Aperçu borné
      2) Gestion des snapshots
         - Lister, prévisualiser, activer, supprimer
         - Résumé optionnel de tous les snapshots
    """
    _ensure_state()

    # ---------- En-tête unifié ----------
    section_header(
        title="Chargement & snapshots",
        subtitle="Importez vos fichiers, sélectionnez le fichier actif, gérez les versions sauvegardées.",
        section="chargement",
        emoji="",
    )
    tab1, tab2 = st.tabs(["📥 Charger un fichier", "🕰️ Snapshots existants"])

    # -------------------------------------------------------------------------
    # Onglet 1 : Import de fichiers utilisateur
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("📥 Import de fichiers CSV, Excel, Parquet ou texte")

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
                snap_key = f"snap_name_{_sanitize_key(name)}"
                snapshot_name = st.text_input(
                    f"Nom du snapshot pour {name}",
                    value=default_snap,
                    key=snap_key,
                    help="Nom lisible pour retrouver cette version (sans l’extension).",
                ) or default_snap

                save_snapshot(df, suffix=snapshot_name)
                log_action("import", f"{name} chargé")
                st.success(f"✅ Fichier **{name}** chargé ({df.shape[0]} lignes). Snapshot : {snapshot_name}")

                _attach_as_active(df, name)

            except RuntimeError as e:
                st.error(f"❌ {e}")
            except ValueError as e:
                st.warning(f"⚠️ {e}")
            except Exception as e:
                st.error(f"❌ Erreur inattendue lors du chargement de {name} : {e}")

        # Résumé des fichiers chargés
        if st.session_state[KEY_DFS]:
            st.subheader("🧾 Résumé des fichiers chargés")

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

            # Aperçu
            with st.expander(f"🔍 Aperçu du fichier : {selected}", expanded=True):
                df_active = st.session_state[KEY_DF]
                st.write(f"Dimensions : {df_active.shape[0]} lignes × {df_active.shape[1]} colonnes")
                st.dataframe(df_active.head(PREVIEW_ROWS), use_container_width=True)
        else:
            st.info("Aucun fichier chargé pour l’instant. Déposez des fichiers dans la zone ci-dessus.")

    # -------------------------------------------------------------------------
    # Onglet 2 : Snapshots enregistrés
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("📜 Snapshots sauvegardés")
        st.info("📘 Un snapshot est une copie horodatée d’un fichier importé. Il peut être rechargé à tout moment.")

        snapshots: List[str] = list_snapshots()

        if not snapshots:
            st.info("Aucun snapshot enregistré pour l’instant.")
        else:
            # --- Résumé global optionnel (peut être coûteux si > nombreux snapshots) ---
            if st.checkbox("Afficher un résumé de tous les snapshots (peut être long)"):
                summaries = []
                for snap in snapshots:
                    try:
                        df_snap = _load_snapshot_cached(snap)
                        summaries.append(_summarize_dataframe(snap, df_snap))
                    except Exception as e:
                        summaries.append({"Fichier": snap, "Lignes": "—", "Colonnes": "—", "NA (%)": "—", "Types dominants": f"Erreur: {e}"})
                st.dataframe(pd.DataFrame(summaries), use_container_width=True)

            st.markdown("### 🔎 Prévisualiser et activer un snapshot")
            col_sel, col_act, col_del = st.columns([4, 1, 1], vertical_alignment="center")

            with col_sel:
                selected_snap = st.selectbox("Sélectionnez un snapshot", options=snapshots, key="select_snapshot")

            with col_act:
                # Le bouton d'activation est géré plus bas après l'aperçu pour un meilleur feedback
                st.write("")

            with col_del:
                if st.button("🗑️ Supprimer", key="btn_delete_selected"):
                    try:
                        delete_snapshot(selected_snap)
                        log_action("delete_snapshot", selected_snap)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la suppression : {e}")

            # --- Aperçu & activation du snapshot sélectionné ---
            if selected_snap:
                try:
                    df_snap = _load_snapshot_cached(selected_snap)

                    # Résumé rapide
                    st.markdown(f"**Snapshot sélectionné :** `{selected_snap}`")
                    summary = _summarize_dataframe(selected_snap, df_snap)
                    st.caption(f"Dimensions : {summary['Lignes']} lignes × {summary['Colonnes']} colonnes — NA : {summary['NA (%)']}% — Types : {summary['Types dominants']}")

                    # Aperçu comme pour un fichier importé
                    with st.expander(f"🔍 Aperçu du snapshot : {selected_snap}", expanded=True):
                        st.dataframe(df_snap.head(PREVIEW_ROWS), use_container_width=True)

                    # Activation (ajoute dans KEY_DFS et le met actif)
                    if st.button("🔄 Activer ce snapshot", type="primary", key="btn_activate_snapshot"):
                        _attach_as_active(df_snap, name=f"[SNAP] {selected_snap}")
                        log_action("load_snapshot", selected_snap)
                        st.success(f"✅ Snapshot **{selected_snap}** activé ({df_snap.shape[0]} lignes). Il est maintenant le fichier actif.")
                except Exception as e:
                    st.error(f"❌ Erreur lors du chargement du snapshot « {selected_snap} » : {e}")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
