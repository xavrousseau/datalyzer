# ============================================================
# Fichier : suggestions.py
# Objectif : Recommandations sur les variables + suppression simple
# Version harmonisée pour Datalyzer (Streamlit)
# ============================================================

import streamlit as st
import pandas as pd

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_suggestions():
    show_header_image("bg_night_serenity.png")
    st.title("💡 Suggestions automatiques sur les variables")

    # ========== Vérification du DataFrame ==========
    if "df" not in st.session_state:
        st.warning("📂 Veuillez charger un fichier.")
        st.stop()

    df = st.session_state.df
    st.divider()

    # ========== Analyse automatique ==========

    recommandations = {}
    nb_encode, nb_vectoriser = 0, 0

    for col in df.columns:
        unique = df[col].nunique()
        if pd.api.types.is_numeric_dtype(df[col]) and unique < 10:
            recommandations[col] = "🔢 Variable discrète — à encoder"
            nb_encode += 1
        elif pd.api.types.is_string_dtype(df[col]) and unique > 100:
            recommandations[col] = "📝 Texte libre — à vectoriser"
            nb_vectoriser += 1

    # ========== Affichage des recommandations ==========
    st.markdown("### 🔍 Suggestions automatiques")
    if recommandations:
        rec_df = pd.DataFrame.from_dict(recommandations, orient="index", columns=["Suggestion"])
        st.dataframe(rec_df)
    else:
        st.success("✅ Aucune variable à signaler. Tout semble correct.")
    st.divider()

    # ========== Résumé visuel ==========

    st.markdown("### 📊 Résumé rapide")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("À encoder", nb_encode)
    with col2:
        st.metric("Texte à vectoriser", nb_vectoriser)

    st.divider()

    # ========== Suppression automatique (colonnes à vectoriser) ==========
    to_drop = [col for col, reco in recommandations.items() if "vectoriser" in reco]
    if to_drop:
        st.markdown("### 🗑️ Colonnes candidates à suppression (texte libre)")
        st.code(", ".join(to_drop))

        if st.button("🚮 Supprimer les colonnes vectorisables"):
            df.drop(columns=to_drop, inplace=True)
            st.session_state.df = df

            save_snapshot(df, suffix="suggestions_cleaned")
            log_action("suggestions_cleanup", f"{len(to_drop)} colonnes supprimées")

            st.success("✅ Colonnes supprimées. Snapshot enregistré.")
    else:
        st.info("Aucune colonne à supprimer automatiquement.")

    st.divider()

    # ========== Validation étape ==========
    validate_step_button(df, step_name="suggestions")
