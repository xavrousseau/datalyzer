# ============================================================
# Fichier : cat_analysis.py
# Objectif : Analyse des variables catégorielles
# (corrélations, boxplots, variable cible)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_analyse_categorielle(df: pd.DataFrame):
    # 🎴 Image décorative
    show_header_image("bg_zen_garden.png") 
    st.title("🎛️ Analyse des variables catégorielles")

    # ========== Sélection des colonnes catégorielles ==========
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    if len(cat_cols) < 2:
        st.info("Pas assez de variables catégorielles pour analyser.")
        return

    # ========== Tabs pour séparer les usages ==========
    tab1, tab2 = st.tabs(["Cramér’s V", "Ciblage par variable"])

    # ========== TAB 1 — Corrélations catégorielles ==========
    with tab1:
        st.markdown("### 🔗 Corrélations entre variables catégorielles (Cramér’s V)")
        cramers_df = compute_cramers_v_matrix(df[cat_cols])
        st.dataframe(cramers_df.style.background_gradient(cmap="Purples"))

    # ========== TAB 2 — Analyse par cible ==========
    with tab2:
        st.markdown("### 🎯 Analyse d’une variable cible (catégorielle ou continue)")

        cible = st.selectbox("Variable cible", df.columns.tolist())
        explicative = st.selectbox("Variable explicative (catégorielle)", cat_cols)

        if pd.api.types.is_numeric_dtype(df[cible]):
            # Si variable cible est numérique → Boxplot
            st.markdown("#### 📉 Boxplot Numérique par Catégorie")
            fig = plot_boxplots(df, cible, explicative)
            st.plotly_chart(fig)

        elif pd.api.types.is_object_dtype(df[cible]):
            # Si variable cible est catégorielle → Répartition croisée
            st.markdown("#### 📊 Croisement des modalités")
            croisement = pd.crosstab(df[explicative], df[cible], normalize='index').round(2)
            st.dataframe(croisement.style.background_gradient(cmap="Blues"))

        else:
            st.warning("Variable cible non prise en charge.")

    # ========== Validation étape ==========
    validate_step_button(df, step_name="analyse_cat")
