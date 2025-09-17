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
from typing import Dict, List

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
    """
    Assure l'initialisation des clés de session nécessaires.

    Pourquoi :
      - Évite les KeyError et garantit que KEY_DFS existe avant usage.
    """
    st.session_state.setdefault(KEY_DFS, {})


def _sanitize_key(s: str) -> str:
    """
    Transforme un libellé libre en *clé* Streamlit stable (sans espaces/accents).

    Exemple :
      "Mon Fichier (v1).csv" -> "mon_fichier_v1_csv"
    """
    s = s.strip().lower()
    return re.sub(r"[^\w\-\.]+", "_", s)


def _read_uploaded_file(file) -> pd.DataFrame:
    """
    Lit un fichier téléversé (Streamlit UploadedFile) en DataFrame selon l’extension.

    Stratégie :
      - CSV/TXT : sep=None + engine="python" → *sniff* automatique de ; , \t …
      - Excel   : via pandas (engine openpyxl recommandé en requirements).
      - Parquet : via pyarrow/fastparquet selon dispo.

    Robustesse :
      - Soulève des erreurs explicites (ValueError/RuntimeError) avec le nom du fichier.
    """
    name = getattr(file, "name", "fichier_sans_nom")
    ext = os.path.splitext(name)[1].lower()

    if ext not in SUPPORTED_EXTS:
        raise ValueError(f"Format non pris en charge : {ext} (fichier {name})")

    try:
        if ext in {".csv", ".txt"}:
            # engine="python" + sep=None : robustesse aux séparateurs variés.
            df = pd.read_csv(file, sep=None, engine="python")
        elif ext in {".xlsx", ".xls"}:
            df = pd.read_excel(file)
        elif ext == ".parquet":
            df = pd.read_parquet(file)
        else:
            raise ValueError(f"Extension inattendue : {ext}")
    except Exception as e:
        # Erreur packagée pour l’UI (lisible côté utilisateur).
        raise RuntimeError(f"Erreur de lecture de {name} ({ext}) : {e}") from e

    # Option : dédupliquer d’éventuelles colonnes homonymes.
    # df = df.loc[:, ~df.columns.duplicated()]
    return df


def _summarize_dataframe(name: str, df: pd.DataFrame) -> Dict[str, object]:
    """
    Produit un résumé synthétique pour affichage tabulaire.

    Contenu :
      - Lignes, Colonnes
      - % de valeurs manquantes (NA %)
      - 3 types les plus fréquents (Types dominants)
    """
    rows, cols = df.shape
    total_cells = rows * cols
    na_pct = round((df.isna().sum().sum() / total_cells) * 100, 2) if total_cells else 0.0
    type_counts = df.dtypes.value_counts()
    top_types = ", ".join(type_counts.head(3).index.astype(str))
    return {
        "Fichier": name,
        "Lignes": rows,
        "Colonnes": cols,
        "NA (%)": na_pct,
        "Types dominants": top_types,
    }


def _attach_as_active(df: pd.DataFrame, name: str) -> None:
    """
    Place le DataFrame dans l’état Streamlit :
      - l’ajoute au dictionnaire des fichiers (KEY_DFS)
      - le définit comme actif (KEY_DF)

    Remarque :
      - Le *nom* sert de clé d’accès dans KEY_DFS et d’étiquette dans l’UI.
    """
    st.session_state[KEY_DFS][name] = df
    st.session_state[KEY_DF] = df


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
         - Lister, recharger, supprimer

    Dépendances attendues :
      - utils.snapshot_utils : save_snapshot, list_snapshots, load_snapshot_by_name, delete_snapshot
      - utils.log_utils.log_action : traçabilité des actions
      - utils.ui_utils.section_header/show_footer : habillage cohérent
    """
    _ensure_state()

    # ---------- En-tête unifié : bannière + titre + baseline ----------
    section_header(
        title="Chargement & snapshots",
        subtitle="Importez vos fichiers, sélectionnez le fichier actif, gérez les versions sauvegardées.",
        section="chargement",   # → image depuis config.SECTION_BANNERS["chargement"]
        emoji="📥",
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

                # Sauvegarde snapshot + logs
                save_snapshot(df, suffix=snapshot_name)  # NB : on utilise le param `suffix`
                log_action("import", f"{name} chargé")
                st.success(f"✅ Fichier **{name}** chargé ({df.shape[0]} lignes). Snapshot : {snapshot_name}")

                # Ajout / activation dans le state
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
                                _attach_as_active(df, name=f"[SNAP] {snap}")
                                st.success(f"Snapshot **{snap}** chargé ({df.shape[0]} lignes).")
                                log_action("load_snapshot", snap)
                        except Exception as e:
                            st.error(f"❌ Erreur lors du chargement du snapshot « {snap} » : {e}")

                with col3:
                    if st.button("🗑️ Supprimer", key=f"del_{safe}", help="Supprime définitivement ce snapshot"):
                        try:
                            delete_snapshot(snap)
                            log_action("delete_snapshot", snap)
                            st.rerun()  # Rafraîchir la liste après suppression
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la suppression : {e}")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
