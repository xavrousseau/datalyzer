# ============================================================
# Fichier : typage.py
# Objectif : Suggestions et corrections interactives des types
# Version harmonisée avec sélection dynamique du fichier actif
# Corrigée pour rester un atelier indépendant (hors progression)
# ============================================================

import streamlit as st
import pandas as pd

from utils.steps import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header, show_eda_progress


def run_typage():
    # === En-tête visuel (sans validation progression) =========
    show_header_image_safe("bg_japanese_room.png")
    show_icon_header(
        "🧾", "Typage",
        "Suggestions automatiques et corrections interactives des types"
    )

    # Ici on affiche la barre uniquement pour le contexte visuel,
    # mais on ne coche/décoche rien → compact=True
    show_eda_progress(EDA_STEPS, compact=True, max_cols=3)

    # === Sélection du fichier actif ==========================
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Merci d’en sélectionner un dans l’onglet Fichiers.")
        return

    # === Suggestion automatique de typage ====================
    @st.cache_data
    def suggerer_types(df: pd.DataFrame) -> dict:
        """
        Propose un type cible pour chaque colonne selon son dtype actuel.
        Utilise les heuristiques pandas de base.
        """
        suggestions = {}
        for col in df.columns:
            if pd.api.types.is_integer_dtype(df[col]):
                suggestions[col] = "int"
            elif pd.api.types.is_float_dtype(df[col]):
                suggestions[col] = "float"
            elif pd.api.types.is_bool_dtype(df[col]):
                suggestions[col] = "bool"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                suggestions[col] = "datetime"
            else:
                suggestions[col] = "string"
        return suggestions

    types_suggeres = suggerer_types(df)
    type_options = ["int", "float", "string", "bool", "datetime"]
    corrections = {}

    st.markdown("### ✏️ Choisissez le type cible pour chaque colonne")
    with st.expander("Afficher les suggestions de typage", expanded=True):
        for col, suggestion in types_suggeres.items():
            current_type = str(df[col].dtype)
            st.caption(f"🔎 `{col}` : type détecté → `{current_type}`")
            selected = st.selectbox(
                f"Type cible pour `{col}`",
                type_options,
                index=type_options.index(suggestion),
                key=f"type_{col}"
            )
            corrections[col] = selected

    st.divider()

    # === Application des corrections =========================
    if st.button("⚙️ Appliquer les corrections de typage"):
        erreurs = []
        for col, t in corrections.items():
            try:
                if t == "int":
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                elif t == "float":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif t == "bool":
                    df[col] = df[col].astype("boolean")
                elif t == "datetime":
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                else:
                    df[col] = df[col].astype("string")
            except Exception as e:
                erreurs.append((col, str(e)))

        # Mise à jour du state global
        st.session_state.df = df

        # Sauvegarde snapshot
        save_snapshot(df, suffix="typage_auto")
        log_action("typage", f"Typage appliqué sur {len(corrections)} colonnes")

        # Feedback utilisateur
        if erreurs:
            st.warning("⚠️ Des erreurs sont survenues lors de la conversion :")
            for col, msg in erreurs:
                st.error(f"`{col}` → {msg}")
        else:
            st.success("✅ Typage appliqué avec succès. Snapshot enregistré.")

    st.divider()

    # === Fin de page (pas de validation progression) =========
    st.info(
        "ℹ️ Cette page est un **atelier de typage**. "
        "La validation de l’étape *Types de variables* se fait via l’onglet "
        "**Exploration → Types**."
    )
