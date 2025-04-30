# ============================================================
# Fichier : cible.py
# Objectif : Analyse autour d’une ou deux variables cibles
# Corrélations, regroupements, boxplots, nuage de points
# Version améliorée avec filtres dynamiques et options d'export
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from config import EDA_STEPS
from utils.filters import validate_step_button, get_active_dataframe
from utils.ui_utils import show_header_image, show_icon_header, show_eda_progress

def run_cible():
    # === En-tête visuel ===
    show_header_image("bg_night_serenity.png")
    show_icon_header("🎯", "Analyse cible", "Corrélations, regroupements, visualisation des cibles")
    show_eda_progress(EDA_STEPS, st.session_state.get("validation_steps", {}))

    # 🔁 Récupération du fichier actif
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Merci de sélectionner un fichier dans l’onglet Fichiers.")
        return

    # === Préparation des colonnes numériques et catégorielles ===
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée dans le fichier.")
        return

    # === Sélection des variables cibles ===
    target_1 = st.selectbox("🎯 Variable cible principale", num_cols, key="target1")
    target_2 = st.selectbox("🎯 Variable cible secondaire (optionnel)", [None] + num_cols, key="target2")

    # === Interface en onglets ===
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Corrélations", "📈 Groupes par cible", "📦 Boxplots", "🧮 Nuage de points"
    ])

    # Onglet 1 — Corrélations
    with tab1:
        st.markdown("### 📊 Corrélations avec la cible principale")
        corr = df[num_cols].corr()[target_1].drop(target_1).sort_values(ascending=False)
        st.dataframe(corr)
        fig_corr = px.bar(corr.reset_index(), x="index", y=target_1, title="Corrélations avec la cible")
        st.plotly_chart(fig_corr, use_container_width=True)

        # Affichage de la heatmap des corrélations pour une vue globale
        st.markdown("### 🔥 Heatmap des corrélations entre variables numériques")
        fig_heatmap = px.imshow(df[num_cols].corr(), title="Matrice des Corrélations")
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # Onglet 2 — Moyennes par groupe catégoriel
    with tab2:
        if not cat_cols:
            st.info("Aucune variable catégorielle disponible pour les regroupements.")
        else:
            group_col = st.selectbox("📁 Variable de regroupement (catégorielle)", cat_cols, key="groupcol")
            st.markdown("#### 📈 Moyenne par groupe")
            avg_target1 = df.groupby(group_col)[target_1].mean().sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(avg_target1, x=group_col, y=target_1), use_container_width=True)

            if target_2:
                st.markdown("#### 📈 Moyenne secondaire par groupe")
                avg_target2 = df.groupby(group_col)[target_2].mean().sort_values(ascending=False).reset_index()
                st.plotly_chart(px.bar(avg_target2, x=group_col, y=target_2), use_container_width=True)

    # Onglet 3 — Boxplots Num ↔ Cat
    with tab3:
        if not cat_cols:
            st.warning("Pas de variable catégorielle pour créer un boxplot.")
        else:
            cat_col = st.selectbox("📁 Variable catégorielle (X)", cat_cols, key="box_cat")
            num_col = st.selectbox("🔢 Variable numérique (Y)", num_cols, key="box_num")
            st.plotly_chart(px.box(df, x=cat_col, y=num_col), use_container_width=True)

    # Onglet 4 — Nuage de points
    with tab4:
        x = st.selectbox("🧭 Axe X", num_cols, key="xscatter")
        y = st.selectbox("🧭 Axe Y", num_cols, key="yscatter")
        color = st.selectbox("🎨 Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")
        st.plotly_chart(px.scatter(df, x=x, y=y, color=color), use_container_width=True)

    # ✅ Validation
    validate_step_button(df, step_name="cible")

    # Option d'export pour les résultats (par exemple, pour les moyennes par groupe)
    if st.button("📤 Exporter les résultats de l'analyse"):
        # Exporter les résultats sous forme de fichier CSV ou autre format
        result_df = df.groupby([group_col])[target_1].mean() if group_col else df[[target_1]]
        result_df.to_csv(f"{target_1}_analysis.csv")
        st.success("✅ Résultats exportés avec succès.")
