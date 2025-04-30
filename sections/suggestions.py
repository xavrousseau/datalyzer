# ============================================================
# Fichier : suggestions.py
# Objectif : Identifier les colonnes à encoder ou vectoriser
# Version harmonisée avec suppression et validation propres
# Ajout de prévisualisation, confirmation et meilleure UX
# ============================================================

import streamlit as st
import pandas as pd

from config import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe, validate_step_button
from utils.ui_utils import show_header_image, show_icon_header, show_eda_progress

def run_suggestions():
    # 🎴 En-tête visuel et contexte
    show_header_image("bg_night_serenity.png")
    show_icon_header("💡", "Suggestions", "Colonnes discrètes à encoder ou texte libre à vectoriser")
    show_eda_progress(EDA_STEPS, st.session_state.get("validation_steps_button", {}))

    # 🔁 Sélection dynamique du fichier
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Merci d’en importer un dans l’onglet Fichiers.")
        return

    # 🔎 Recommandations automatiques
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

    # 📋 Affichage des suggestions
    st.markdown("### 🔍 Suggestions détectées")
    if recommandations:
        rec_df = pd.DataFrame.from_dict(recommandations, orient="index", columns=["Suggestion"])
        st.dataframe(rec_df, use_container_width=True)
    else:
        st.success("✅ Aucune variable à encoder ou vectoriser.")

    # 📊 Résumé visuel
    st.markdown("### 📊 Résumé des recommandations")
    col1, col2 = st.columns(2)
    col1.metric("À encoder", nb_encode)
    col2.metric("À vectoriser", nb_vectoriser)

    st.divider()

    # 🗑️ Suppression des colonnes à vectoriser
    to_drop = [col for col, reco in recommandations.items() if "vectoriser" in reco]
    if to_drop:
        st.markdown("### 🗑️ Colonnes candidates à suppression (texte libre)")
        with st.expander("🔎 Détails des colonnes à supprimer"):
            st.code(", ".join(to_drop))

        # Confirmation avant suppression
        if st.button("🚮 Supprimer les colonnes vectorisables"):
            st.warning(f"Vous êtes sur le point de supprimer {len(to_drop)} colonnes contenant du texte libre.")
            if st.button("Confirmer la suppression"):
                df.drop(columns=to_drop, inplace=True)
                st.session_state.df = df
                save_snapshot(df, suffix="suggestions_cleaned")
                log_action("suggestions_cleanup", f"{len(to_drop)} colonnes supprimées")
                st.success("✅ Colonnes supprimées. Snapshot sauvegardé.")
    else:
        st.info("Aucune colonne à supprimer automatiquement.")

    # ✅ Validation de l'étape
    st.divider()
    validate_step_button("suggestions")
