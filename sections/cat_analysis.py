# ============================================================
# Fichier : sections/cat_analysis.py
# Objectif : Analyse des variables catégorielles
# Statut   : Module avancé — HORS barre de progression EDA
# Points   :
#   - Matrice de Cramér’s V avec seuil et limite de cardinalité
#   - Croisements cible↔explicative (num→boxplot, cat→crosstab + bar empilée)
#   - Garde-fous sur colonnes disponibles et matrices vides
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.filters import get_active_dataframe
from utils.ui_utils import section_header, show_footer


def run_analyse_categorielle() -> None:
    """
    Atelier « Analyse catégorielle ».

    Volet 1 — Corrélations catégorielles :
      - Calcule la matrice de Cramér’s V sur les colonnes catégorielles.
      - Permet de filtrer par seuil et de borner la cardinalité (max_levels)
        pour éviter des crosstabs démesurées.

    Volet 2 — Croisement avec une cible :
      - Si la cible est numérique → boxplot (num ↔ cat) via `plot_boxplots`.
      - Si la cible est catégorielle → crosstab normalisée + barres empilées (répartition %).

    Garde-fous :
      - Avertit si aucune colonne catégorielle.
      - Gère les matrices vides (après filtrage seuil/cardinalité).
      - Filtre les variables explicatives à ≤ 20 modalités pour la lisibilité.
    """
    # ---------- En-tête unifiée ----------
    section_header(
        title="Analyse catégorielle",
        subtitle="Corrélations et croisements avec une cible.",
        section="analyse",
        emoji="📊",
    )

    # ---------- Fichier actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Merci de charger un fichier dans l’onglet **Fichiers**.")
        return

    # ---------- Colonnes catégorielles ----------
    cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    if len(cat_cols) < 1:
        st.info("❗ Aucune variable catégorielle détectée.")
        return

    # ---------- Onglets ----------
    tab1, tab2 = st.tabs(["🔗 Corrélations (Cramér’s V)", "🎯 Cible par variable"])

    # ========================================================
    # Onglet 1 — Corrélations (Cramér’s V)
    # ========================================================
    with tab1:
        st.markdown("### 🔗 Corrélations entre variables catégorielles (Cramér’s V)")

        # Paramètres de calcul/affichage
        with st.expander("⚙️ Paramètres"):
            c1, c2 = st.columns(2)
            min_corr = c1.slider("Seuil d'affichage (Cramér ≥)", 0.0, 1.0, 0.3, 0.05)
            max_levels = c2.number_input(
                "Max modalités par variable (pour crosstabs)",
                min_value=2, max_value=200, value=50, step=1,
                help="Les colonnes au-delà de ce seuil sont ignorées pour éviter des tables trop volumineuses."
            )
            show_full = st.checkbox("Afficher la matrice complète (non filtrée)", value=False)

        # Calcul de la matrice (utils.eda_utils)
        cramers_df = compute_cramers_v_matrix(df[cat_cols], max_levels=max_levels)

        if cramers_df.empty:
            st.info("Aucune matrice exploitable (trop peu de colonnes ou cardinalités trop élevées).")
        else:
            if show_full:
                st.dataframe(
                    cramers_df.style.background_gradient(cmap="Purples"),
                    use_container_width=True
                )
            else:
                # Masque sous le seuil puis suppression des lignes/colonnes vides
                filtered = cramers_df.where(cramers_df >= min_corr)
                filtered = filtered.dropna(axis=0, how="all").dropna(axis=1, how="all")
                if filtered.empty:
                    st.info(f"Aucune paire avec Cramér’s V ≥ {min_corr}.")
                else:
                    st.dataframe(
                        filtered.style.background_gradient(cmap="Purples"),
                        use_container_width=True
                    )

            # Heatmap optionnelle (aperçu global)
            if st.checkbox("Afficher une heatmap (aperçu global)"):
                fig = px.imshow(
                    cramers_df, color_continuous_scale="Purples",
                    zmin=0, zmax=1, aspect="auto", origin="lower",
                    title="Matrice de Cramér’s V (aperçu)"
                )
                fig.update_layout(margin=dict(t=40, l=20, r=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

    # ========================================================
    # Onglet 2 — Croisement avec une variable cible
    # ========================================================
    with tab2:
        st.markdown("### 🎯 Analyse d’une variable cible")

        # Cible (numérique OU catégorielle)
        cible = st.selectbox("🎯 Variable cible", df.columns.tolist())

        # Variables explicatives catégorielles à cardinalité raisonnable
        cat_cols_filtered = [c for c in cat_cols if df[c].nunique(dropna=False) <= 20 and c != cible]
        if not cat_cols_filtered:
            st.warning("❌ Pas de variables catégorielles 'explicatives' disponibles (≤ 20 modalités).")
            return

        explicative = st.selectbox("📂 Variable explicative (catégorielle)", cat_cols_filtered)

        # Cible numérique → boxplot num↔cat
        if pd.api.types.is_numeric_dtype(df[cible]):
            st.markdown("#### 📉 Boxplot (cible numérique par catégorie explicative)")
            fig = plot_boxplots(df, cible, explicative)
            if fig is None:
                st.info("Impossible de tracer le boxplot (cible vide après coercition).")
            else:
                st.plotly_chart(fig, use_container_width=True)

        # Cible catégorielle → crosstab normalisée + bar empilée
        elif pd.api.types.is_object_dtype(df[cible]) or str(df[cible].dtype).startswith("category"):
            st.markdown("#### 📊 Répartition croisée normalisée (par ligne)")
            cross = pd.crosstab(df[explicative], df[cible], normalize="index").round(3)
            st.dataframe(cross, use_container_width=True)

            st.markdown("#### 📊 Répartition empilée")
            cross_plot = (cross * 100).reset_index().melt(
                id_vars=explicative, var_name=str(df[cible].name), value_name="Part (%)"
            )
            fig_stack = px.bar(
                cross_plot, x=explicative, y="Part (%)", color=str(df[cible].name),
                title=f"Répartition de {df[cible].name} par {explicative} (normalisée %)",
                barmode="stack"
            )
            st.plotly_chart(fig_stack, use_container_width=True)

        else:
            st.warning("❌ La variable cible sélectionnée n’est pas exploitable ici (ni numérique, ni catégorielle).")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
