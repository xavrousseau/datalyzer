# ============================================================
# Fichier : sections/exploration.py
# Objectif : Analyse exploratoire avancée et interactive
# Version  : harmonisée avec l’UI unifiée et les étapes EDA
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.steps import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.eda_utils import (
    summarize_dataframe,
    plot_missing_values,
    detect_constant_columns,
    detect_low_variance_columns,
    get_columns_above_threshold,
    detect_outliers,
    compute_correlation_matrix,
)
from utils.log_utils import log_action
from utils.filters import validate_step_button, get_active_dataframe
from utils.ui_utils import section_header, show_eda_progress, show_footer
from utils.sql_bridge import expose_to_sql_lab


def run_exploration() -> None:
    """
    Tableau de bord d’EDA (Analyse de Données Exploratoire).

    Onglets :
      1) Types         — résumé structurel + dtypes par colonne.
      2) Manquants     — visualisation NA, suppression au-dessus d’un seuil.
      3) Statistiques  — describe() complet + taux NA global.
      4) Distributions — histogramme interactif + asymétrie (skew).
      5) Outliers      — détection simple (IQR ou Z-score) par variable.
      6) Corrélations  — matrice corrélation (Pearson, Spearman, Kendall).
      7) Nettoyage auto— drop de colonnes constantes, quasi-constantes, NA élevés.

    Effets :
      - Certaines actions modifient le DataFrame actif in-place
        (suppression de colonnes), mettent à jour `st.session_state["df"]`,
        créent un snapshot, et loguent l’action.

    Notes UX/Perf :
      - Les affichages tabulaires sont bornés par l’UI Streamlit (dataframe).
      - Les graphiques utilisent Plotly pour l’interactivité et l’accessibilité.
      - Les seuils (NA, variance) sont exposés à l’utilisateur quand pertinent.
    """
    # ---------- En-tête unifié ----------
    section_header(
        title="Exploration",
        subtitle="Analyse des types, valeurs manquantes, distributions, outliers et corrélations.",
        section="exploration",  # ← utilise SECTION_BANNERS["exploration"]
        emoji="",
    )

    # ---------- Barre de progression ----------
    show_eda_progress(EDA_STEPS, compact=True, single_row=True)

    # ---------- Fichier actif ----------
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Importez un fichier via l’onglet **Chargement**.")
        return


    # Colonnes numériques détectées (utile dans plusieurs onglets)
    num_cols = df.select_dtypes(include="number").columns.tolist()

    # ---------- Navigation par onglets ----------
    tabs = st.tabs([
        "🧬 Types", "🩹 Manquants", "📈 Statistiques",
        "📊 Distributions", "🚨 Outliers", "🔗 Corrélations", "🧼 Nettoyage auto"
    ])

    # ---------------------------------------------------------
    # 🧬 Types
    # ---------------------------------------------------------
    with tabs[0]:
        st.subheader("🧬 Types de colonnes")

        # Résumé structurel (délégué à utils.eda_utils.summarize_dataframe)
        summary = summarize_dataframe(df)
        st.dataframe(summary, use_container_width=True)

        with st.expander("🔎 Détails des types par colonne", expanded=False):
            dtypes_df = pd.DataFrame({
                "Colonne": df.columns,
                "dtype": [str(t) for t in df.dtypes],
            })
            st.dataframe(dtypes_df, use_container_width=True)

        st.info(
            "ℹ️ Ceci est un **aperçu**. Pour corriger finement les types "
            "(conversions, datetime, booléens, etc.), utilisez la page **Typage**."
        )

        validate_step_button("typing", context_prefix="exploration_")

    # ---------------------------------------------------------
    # 🩹 Valeurs manquantes
    # ---------------------------------------------------------
    with tabs[1]:
        st.subheader("🩹 Analyse des valeurs manquantes")

        # Slider en pourcentage entier (0 → 100 %), puis conversion en proportion [0,1]
        seuil_pct = st.slider(
            "🎯 Seuil de suppression (%)",
            min_value=0, max_value=100, value=50, step=1,
            help="Colonnes dont le pourcentage de valeurs manquantes est supérieur à ce seuil seront candidates à la suppression."
        )
        threshold = seuil_pct / 100.0  # ← proportion pour le calcul

        # Heatmap/bar manquants
        fig = plot_missing_values(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # Colonnes dépassant le seuil (en proportion)
        cols_na = get_columns_above_threshold(df, threshold)

        if cols_na:
            st.warning(f"{len(cols_na)} colonnes dépassent {seuil_pct:.0f}% de NA.")
            selected = st.multiselect(
                "Colonnes à supprimer",
                options=cols_na,
                default=cols_na,
                help="Désélectionnez ce que vous souhaitez conserver malgré tout."
            )
            if selected and st.button("🗑️ Supprimer sélection"):
                # Modif in-place + mise à jour du state
                df.drop(columns=selected, inplace=True, errors="ignore")
                st.session_state["df"] = df
                save_snapshot(df, "missing_dropped")
                expose_to_sql_lab(f"{nom}__missing_dropped", df, make_active=True)
                log_action("missing_cleanup", f"{len(selected)} colonnes supprimées (> {seuil_pct:.0f}% NA)")
                st.success("✅ Colonnes supprimées avec succès.")
        else:
            st.info("✅ Aucune colonne ne dépasse le seuil défini.")

        validate_step_button("missing", context_prefix="exploration_")
    # ---------------------------------------------------------
    # 📈 Statistiques descriptives
    # ---------------------------------------------------------
    with tabs[2]:
        st.subheader("📈 Statistiques descriptives")

        # describe(include="all") essaye de couvrir tous les types.
        # datetime_is_numeric=True (pandas >= 1.5) : stats numériques sur dates (comptage, min, max) utiles.
        try:
            stats = df.describe(include="all", datetime_is_numeric=True).T
        except TypeError:
            # Compat anciennes versions de pandas
            stats = df.describe(include="all").T

        st.dataframe(stats, use_container_width=True)

        pct_missing = df.isna().mean().mean() * 100
        st.info(f"Taux global de valeurs manquantes : **{pct_missing:.2f}%**")

        validate_step_button("stats", context_prefix="exploration_")


    # ---------------------------------------------------------
    # 📊 Distributions
    # ---------------------------------------------------------
    with tabs[3]:
        st.subheader("📊 Distribution des variables numériques")

        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
        else:
            col = st.selectbox("📈 Variable à visualiser", num_cols, key="hist_col")
            # Histogramme simple (nbins=40 : compromis lisibilité / lissage)
            fig = px.histogram(df, x=col, nbins=40, title=f"Distribution de {col}")
            st.plotly_chart(fig, use_container_width=True)

            # Skewness (asymétrie) : indicateur rapide de symétrie de la distribution
            skew = df[col].skew()
            skew_type = (
                "symétrique" if abs(skew) < 0.5
                else "asymétrique positive" if skew > 0
                else "asymétrique négative"
            )
            st.info(f"Asymétrie de `{col}` : **{skew:.2f}** → *{skew_type}*")

        validate_step_button("distributions", context_prefix="exploration_")


    # ---------------------------------------------------------
    # 🚨 Outliers
    # ---------------------------------------------------------
    with tabs[4]:
        st.subheader("🚨 Détection d’outliers")

        if not num_cols:
            st.warning("⚠️ Pas de variable numérique pour détecter des outliers.")
        else:
            method = st.radio(
                "Méthode",
                ["iqr", "zscore"],
                horizontal=True,
                help=(
                    "IQR : valeurs hors [Q1 - 1.5*IQR ; Q3 + 1.5*IQR]. "
                    "Z-score : |z| au-delà d’un seuil (généralement 3)."
                ),
            )
            col = st.selectbox("🔍 Variable à analyser", num_cols, key="outliers_col")

            # On récupère ses index pour ré-extraire TOUTES les colonnes depuis le DF d'origine.
            out_idx = detect_outliers(df[[col]], method=method).index
            outliers = df.loc[out_idx].copy()

            st.info(f"{len(outliers)} outliers détectés sur `{col}` (méthode {method}).")
            st.dataframe(outliers.head(10), use_container_width=True)

            if st.button("💾 Sauvegarder les outliers détectés"):
                save_snapshot(outliers, suffix=f"outliers_{method}_{col}")
                log_action("outliers_detected", f"{len(outliers)} sur {col} ({method})")
                expose_to_sql_lab(f"{nom}__outliers_{method}_{col}", outliers)
                st.success("✅ Snapshot des outliers enregistré.")

        validate_step_button("extremes", context_prefix="exploration_")


    # ---------------------------------------------------------
    # 🔗 Corrélations
    # ---------------------------------------------------------
    with tabs[5]:
        st.subheader("🔗 Corrélations")

        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour une corrélation.")
        else:
            method = st.radio(
                "Méthode",
                ["pearson", "spearman", "kendall"],
                horizontal=True,
                help=(
                    "Pearson : corrélation linéaire (variables quantitatives). "
                    "Spearman : rangs (monotone, robuste aux non-linéarités). "
                    "Kendall : rangs, plus conservateur (petits échantillons)."
                ),
            )
            corr = compute_correlation_matrix(df[num_cols], method=method)

            if corr.empty:
                st.info(f"Aucune corrélation exploitable pour **{method}**.")
            else:
                # Heatmap à gamme [-1, 1], étiquette de cellule avec 2 décimales
                fig = px.imshow(
                    corr,
                    text_auto=".2f",
                    aspect="auto",
                    zmin=-1, zmax=1,
                    color_continuous_scale="RdBu_r",
                    title=f"Matrice de corrélation ({method})",
                )
                fig.update_layout(margin=dict(t=40, l=20, r=20, b=60))
                st.plotly_chart(fig, use_container_width=True)

        validate_step_button("correlations", context_prefix="exploration_")


    # ---------------------------------------------------------
    # 🧼 Nettoyage auto
    # ---------------------------------------------------------
    with tabs[6]:
        st.subheader("🧼 Nettoyage automatique")

        # Règles simples : constantes, faible variance, forte proportion de NA
        const_cols = detect_constant_columns(df)
        low_var = detect_low_variance_columns(df)
        na_cols = get_columns_above_threshold(df, 0.5)  # 50% NA par défaut
        all_to_drop = sorted(set(const_cols + low_var + na_cols))

        st.markdown(f"🔍 Colonnes identifiées : **{len(all_to_drop)}**")

        if all_to_drop:
            with st.expander("Voir les colonnes candidates"):
                st.write(all_to_drop)

            if st.button("🧹 Appliquer le nettoyage auto"):
                df.drop(columns=all_to_drop, inplace=True, errors="ignore")
                st.session_state["df"] = df
                save_snapshot(df, suffix="auto_cleaned")
                expose_to_sql_lab(f"{nom}__auto_cleaned", df, make_active=True)
                log_action("auto_cleanup", f"{len(all_to_drop)} colonnes supprimées (const/faible var/NA élevés)")
                st.success("✅ Nettoyage appliqué.")
        else:
            st.info("Rien à nettoyer selon ces règles simples.")

        validate_step_button("cleaning", context_prefix="exploration_")

    
    # ---------------------------------------------------------
    # Footer 
    # ---------------------------------------------------------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
