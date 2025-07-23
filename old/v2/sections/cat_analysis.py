# ============================================================
# Fichier : cat_analysis.py
# Objectif : Analyse des variables catégorielles
# Version enrichie avec meilleures interactions UX et analyse des corrélations
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from config import EDA_STEPS
from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.filters import validate_step_button, get_active_dataframe
from utils.ui_utils import show_header_image, show_icon_header, show_eda_progress

def run_analyse_categorielle():
    # 🎴 En-tête visuel et contexte
    show_header_image("bg_zen_garden.png")
    show_icon_header("📊", "Analyse catégorielle", "Corrélations et croisements avec la variable cible")
    show_eda_progress(EDA_STEPS, st.session_state.get("validation_steps", {}))

    # 🔁 Récupération du fichier actif
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Merci de charger un fichier dans l’onglet Fichiers.")
        return

    # ========== Filtrage des colonnes catégorielles ========== 
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    if len(cat_cols) < 2:
        st.info("❗ Pas assez de variables catégorielles pour réaliser une analyse.")
        return

    # ========== Interface en onglets ==========
    tab1, tab2 = st.tabs(["🔗 Corrélations", "🎯 Cible par variable"])

    # Onglet 1 — Corrélations (Cramér’s V)
    with tab1:
        st.markdown("### 🔗 Corrélations entre variables (Cramér’s V)")
        cramers_df = compute_cramers_v_matrix(df[cat_cols])

        # Filtre des corrélations importantes (valeurs supérieures à 0.3)
        min_corr = st.slider("🔍 Filtrer par corrélation", 0.0, 1.0, 0.3, 0.1)
        filtered_cramers = cramers_df[cramers_df > min_corr].dropna(axis=0, how="all").dropna(axis=1, how="all")
        
        st.dataframe(filtered_cramers.style.background_gradient(cmap="Purples"))

    # Onglet 2 — Croisement avec une variable cible
    with tab2:
        st.markdown("### 🎯 Analyse d’une variable cible")

        cible = st.selectbox("🎯 Variable cible", df.columns.tolist())

        # Filtrage des variables explicatives catégorielles
        cat_cols_filtered = [col for col in cat_cols if len(df[col].unique()) <= 20]
        if not cat_cols_filtered:
            st.warning("❌ Pas de variables catégorielles à analyser.")
            return
        
        explicative = st.selectbox("📂 Variable explicative (catégorielle)", cat_cols_filtered)

        # Vérification de la validité de la variable cible
        if pd.api.types.is_numeric_dtype(df[cible]):
            st.markdown("#### 📉 Boxplot (numérique par catégorie)")
            fig = plot_boxplots(df, cible, explicative)
            st.plotly_chart(fig)
        elif pd.api.types.is_object_dtype(df[cible]):
            st.markdown("#### 📊 Répartition croisée")
            cross_tab = pd.crosstab(df[explicative], df[cible], normalize='index').round(2)
            st.dataframe(cross_tab.style.background_gradient(cmap="Blues"))
        else:
            st.warning("❌ La variable cible sélectionnée n’est pas exploitable ici.")

    # ✅ Validation de l'étape
    validate_step_button("cat")  # Remplacer validate_step par validate_step_button
