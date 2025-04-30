# ============================================================
# Fichier : typage.py
# Objectif : Détection, suggestion et correction des types
# pour Datalyzer (version Streamlit)
# ============================================================

import streamlit as st
import pandas as pd

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_typage():
    show_header_image("bg_japanese_room.png")
    st.title("🧾 Correction interactive des types")
    st.markdown("_Suggestions automatiques de typage avec possibilité de modifier chaque colonne._")

    # ========== Vérification du DataFrame ==========
    if "df" not in st.session_state:
        st.warning("📂 Veuillez charger un fichier.")
        st.stop()

    df = st.session_state.df
    st.divider()

    # ========== Types suggérés automatiquement ==========
    @st.cache_data
    def suggérer_types(df: pd.DataFrame) -> dict:
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

    types_suggérés = suggérer_types(df)

    # ========== Interface de sélection ==========

    options = ["int", "float", "string", "bool", "datetime"]
    corrections = {}

    st.markdown("### ✏️ Choisissez le type cible pour chaque colonne")
    for col, guess in types_suggérés.items():
        selected = st.selectbox(f"Type pour `{col}`", options, index=options.index(guess))
        corrections[col] = selected
    st.divider()

    # ========== Application des corrections ==========
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

        st.session_state.df = df
        save_snapshot(df, suffix="typage")
        log_action("typage", f"Correction sur {len(corrections)} colonnes")

        if erreurs:
            st.warning("⚠️ Erreurs sur certaines colonnes :")
            for col, msg in erreurs:
                st.error(f"{col} → {msg}")
        else:
            st.success("✅ Typage appliqué et snapshot enregistré.")

    # ========== Validation de l'étape ==========
    st.divider()
    validate_step_button(df, step_name="typage")
