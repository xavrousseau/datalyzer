# ============================================================
# Fichier : cat_analysis.py
# Objectif : Analyse des variables catégorielles
# Statut   : Module avancé — HORS barre de progression EDA
# Points :
#   - Matrice de Cramér’s V avec seuil et limite de cardinalité
#   - Croisements cible↔explicative (num→boxplot, cat→crosstab + bar empilée)
#   - Garde-fous sur colonnes disponibles et matrices vides
# ============================================================

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header


def run_analyse_categorielle():
    # 🎴 En-tête visuel et contexte (pas de barre de progression ici)
    show_header_image_safe("bg_zen_garden.png")
    show_icon_header("📊", "Analyse catégorielle", "Corrélations et croisements avec une cible")

    # 🔁 Récupération du fichier actif
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Merci de charger un fichier dans l’onglet Fichiers.")
        return

    # ========== Filtrage des colonnes catégorielles ==========
    # On inclut object, category et string pour être large
    cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    if len(cat_cols) < 1:
        st.info("❗ Aucune variable catégorielle détectée.")
        return

    # ========== Interface en onglets ==========
    tab1, tab2 = st.tabs(["🔗 Corrélations (Cramér’s V)", "🎯 Cible par variable"])

    # ------------------------------------------------------------------
    # Onglet 1 — Corrélations (Cramér’s V)
    # ------------------------------------------------------------------
    with tab1:
        st.markdown("### 🔗 Corrélations entre variables catégorielles (Cramér’s V)")

        with st.expander("⚙️ Paramètres"):
            c1, c2 = st.columns(2)
            min_corr = c1.slider("Seuil d'affichage (Cramér ≥)", 0.0, 1.0, 0.3, 0.05)
            max_levels = c2.number_input("Max modalités par variable (pour crosstabs)", min_value=2, max_value=200, value=50, step=1)
            show_full = st.checkbox("Afficher la matrice complète (non filtrée)", value=False)

        # Calcul (utilise le cache côté utils)
        cramers_df = compute_cramers_v_matrix(df[cat_cols], max_levels=max_levels)

        if cramers_df.empty:
            st.info("Aucune matrice exploitable (trop peu de colonnes ou cardinalités trop élevées).")
        else:
            if show_full:
                st.dataframe(cramers_df.style.background_gradient(cmap="Purples"), use_container_width=True)
            else:
                # Filtre par seuil ; on retire lignes/colonnes entièrement NaN
                filtered = cramers_df.where(cramers_df >= min_corr)
                filtered = filtered.dropna(axis=0, how="all").dropna(axis=1, how="all")
                if filtered.empty:
                    st.info(f"Aucune paire avec Cramér’s V ≥ {min_corr}.")
                else:
                    st.dataframe(filtered.style.background_gradient(cmap="Purples"), use_container_width=True)

            # Heatmap optionnelle pour un coup d’œil global
            if st.checkbox("Afficher une heatmap (aperçu global)"):
                fig = px.imshow(
                    cramers_df, color_continuous_scale="Purples",
                    zmin=0, zmax=1, aspect="auto", origin="lower",
                    title="Matrice de Cramér’s V (aperçu)"
                )
                fig.update_layout(margin=dict(t=40, l=20, r=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Onglet 2 — Croisement avec une variable cible
    # ------------------------------------------------------------------
    with tab2:
        st.markdown("### 🎯 Analyse d’une variable cible")
        cible = st.selectbox("🎯 Variable cible", df.columns.tolist())

        # Variables explicatives catégorielles à cardinalité raisonnable
        cat_cols_filtered = [c for c in cat_cols if df[c].nunique(dropna=False) <= 20 and c != cible]
        if not cat_cols_filtered:
            st.warning("❌ Pas de variables catégorielles 'explicatives' disponibles (≤ 20 modalités).")
            return

        explicative = st.selectbox("📂 Variable explicative (catégorielle)", cat_cols_filtered)

        # Cas 1 : cible numérique → boxplot num↔cat
        if pd.api.types.is_numeric_dtype(df[cible]):
            st.markdown("#### 📉 Boxplot (cible numérique par catégorie explicative)")
            fig = plot_boxplots(df, cible, explicative)
            if fig is None:
                st.info("Impossible de tracer le boxplot (cible vide après coercition).")
            else:
                st.plotly_chart(fig, use_container_width=True)

        # Cas 2 : cible catégorielle → crosstab normalisée + bar empilée
        elif pd.api.types.is_object_dtype(df[cible]) or str(df[cible].dtype).startswith("category"):
            st.markdown("#### 📊 Répartition croisée normalisée (par ligne)")
            cross = pd.crosstab(df[explicative], df[cible], normalize="index").round(3)
            st.dataframe(cross, use_container_width=True)

            # Barres empilées pour visualiser la répartition
            st.markdown("#### 📊 Répartition empilée")
            cross_plot = (cross * 100).reset_index().melt(id_vars=explicative, var_name=str(cible), value_name="Part (%)")
            fig_stack = px.bar(
                cross_plot, x=explicative, y="Part (%)", color=str(cible),
                title=f"Répartition de {cible} par {explicative} (normalisée %)",
                barmode="stack"
            )
            st.plotly_chart(fig_stack, use_container_width=True)

        else:
            st.warning("❌ La variable cible sélectionnée n’est pas exploitable ici (ni numérique, ni catégorielle).")

 
