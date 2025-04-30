# ============================================================
# Fichier : exploration.py
# Objectif : Analyse exploratoire avancée et interactive
# Version améliorée avec filtres et options d'échantillonnage
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from config import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.eda_utils import (
    summarize_dataframe,
    plot_missing_values,
    detect_constant_columns,
    detect_low_variance_columns,
    get_columns_above_threshold,
    detect_outliers
)
from utils.log_utils import log_action
from utils.filters import validate_step_button, get_active_dataframe
from utils.ui_utils import show_header_image, show_icon_header, show_eda_progress


def run_exploration():
    # === En-tête général et barre de progression EDA ===
    show_header_image("bg_sakura_peaceful.png")
    show_icon_header("🔍", "Exploration", "Analyse des types, valeurs manquantes, distributions, outliers et corrélations")
    show_eda_progress(EDA_STEPS, st.session_state.get("validation_steps", {}))

    # === Chargement du DataFrame actif sélectionné ===
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Merci de charger un fichier dans l'onglet dédié.")
        return

    # === Navigation par onglets pour les étapes EDA ===
    tabs = st.tabs([
        "🧬 Types", "🩹 Manquants", "📊 Distributions", "🚨 Outliers",
        "🧼 Nettoyage auto", "📈 Statistiques", "🔗 Corrélations"
    ])

    # === 🧬 Types de colonnes ===
    with tabs[0]:
        st.subheader("🧬 Types de colonnes")

        summary = summarize_dataframe(df)
        st.dataframe(summary, use_container_width=True)
        st.markdown(f"- Total de colonnes : **{df.shape[1]}**")

        validate_step_button("types", context_prefix="exploration_")

    # === 🩹 Analyse des valeurs manquantes ===
    with tabs[1]:
        st.subheader("🩹 Analyse des valeurs manquantes")

        seuil = st.slider("🎯 Seuil de suppression (%)", 0.1, 1.0, 0.5)
        fig = plot_missing_values(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        cols_na = get_columns_above_threshold(df, seuil)

        if cols_na:
            st.warning(f"{len(cols_na)} colonnes dépassent le seuil de {seuil * 100:.0f}%")
            selected = st.multiselect("Colonnes à supprimer", cols_na, default=cols_na)

            if st.button("🗑️ Supprimer sélection"):
                with st.expander("Colonnes supprimées", expanded=False):
                    st.dataframe(df[selected])

                df.drop(columns=selected, inplace=True)
                st.session_state.df = df

                save_snapshot(df, "missing_dropped")
                log_action("missing_cleanup", f"{len(selected)} colonnes supprimées")
                st.success("✅ Colonnes supprimées avec succès.")
        else:
            st.info("✅ Aucune colonne ne dépasse le seuil défini.")

        validate_step_button("missing", context_prefix="exploration_")

    # === 📊 Analyse des distributions numériques ===
    with tabs[2]:
        st.subheader("📊 Distribution des variables numériques")

        num_cols = df.select_dtypes(include="number").columns.tolist()
        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
        else:
            col = st.selectbox("📈 Variable à visualiser", num_cols)
            fig = px.histogram(df, x=col, nbins=40, title=f"Distribution de {col}")
            st.plotly_chart(fig, use_container_width=True)

            skew = df[col].skew()
            skew_type = "symétrique" if abs(skew) < 0.5 else "asymétrique positive" if skew > 0 else "asymétrique négative"
            st.info(f"Asymétrie de `{col}` : **{skew:.2f}** → *{skew_type}*")

        validate_step_button("histos", context_prefix="exploration_")

    # === 🚨 Détection des outliers ===
    with tabs[3]:
        st.subheader("🚨 Détection d’outliers")

        method = st.radio("Méthode de détection", ["iqr", "zscore"], horizontal=True)
        col = st.selectbox("🔍 Variable à analyser", num_cols, key="outliers_col")

        outliers = detect_outliers(df[[col]], method=method)
        st.info(f"{len(outliers)} outliers détectés sur `{col}` avec la méthode `{method}`")
        st.dataframe(outliers.head(10), use_container_width=True)

        if st.button("💾 Sauvegarder les outliers détectés"):
            save_snapshot(outliers, suffix=f"outliers_{method}")
            log_action("outliers_detected", f"{len(outliers)} détectés sur {col} ({method})")
            st.success("✅ Snapshot des outliers enregistré.")

        validate_step_button("outliers", context_prefix="exploration_")

    # === 🧼 Nettoyage automatique ===
    with tabs[4]:
        st.subheader("🧼 Nettoyage automatique des colonnes peu informatives")

        const_cols = detect_constant_columns(df)
        low_var = detect_low_variance_columns(df)
        na_cols = get_columns_above_threshold(df, seuil=0.5)
        all_to_drop = sorted(set(const_cols + low_var + na_cols))

        st.markdown(f"🔍 Colonnes identifiées à supprimer : **{len(all_to_drop)}**")

        with st.expander("Voir les colonnes candidates", expanded=False):
            st.dataframe(df[all_to_drop])

        if st.button("🧹 Appliquer le nettoyage automatique"):
            df.drop(columns=all_to_drop, inplace=True)
            st.session_state.df = df

            save_snapshot(df, suffix="auto_cleaned")
            log_action("auto_cleanup", f"{len(all_to_drop)} colonnes supprimées")
            st.success("✅ Nettoyage appliqué avec succès.")

        validate_step_button("cleaning", context_prefix="exploration_")

    # === 📈 Statistiques descriptives ===
    with tabs[5]:
        st.subheader("📈 Statistiques descriptives")

        stats = df.describe().T
        st.dataframe(stats, use_container_width=True)

        pct_missing = 100 - stats["count"].sum() / (stats.shape[0] * df.shape[0]) * 100
        st.info(f"Estimation globale de valeurs manquantes : **{pct_missing:.2f}%**")

        validate_step_button("stats", context_prefix="exploration_")

    # === 🔗 Corrélations numériques ===
    with tabs[6]:
        st.subheader("🔗 Corrélations entre variables numériques")

        method = st.radio("Méthode", ["pearson", "spearman", "kendall"], horizontal=True)

        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour une corrélation.")
        else:
            corr = df[num_cols].corr(method=method)

            fig = px.imshow(
                corr, text_auto=".2f", aspect="auto", zmin=-1, zmax=1,
                color_continuous_scale="RdBu_r", title="Matrice de corrélation"
            )
            fig.update_layout(margin=dict(t=40, l=20, r=20, b=60))
            st.plotly_chart(fig, use_container_width=True)
        validate_step_button("correlations", context_prefix="exploration_")