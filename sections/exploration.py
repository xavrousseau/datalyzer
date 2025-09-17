# ============================================================
# Fichier : exploration.py
# Objectif : Analyse exploratoire avancée et interactive
# Version : corrigée, alignée avec les étapes EDA et commentée
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

 
from utils.steps import EDA_STEPS
 
from utils.snapshot_utils import save_snapshot
from utils.eda_utils import (
    summarize_dataframe,
    plot_missing_values,
    detect_constant_columns,
    detect_low_variance_columns,
    get_columns_above_threshold,
    detect_outliers,
)
from utils.log_utils import log_action
from utils.filters import validate_step_button, get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header, show_eda_progress


def run_exploration():
    # === En-tête + barre de progression ======================
    show_header_image_safe("bg_sakura_peaceful.png")
    show_icon_header("🔍", "Exploration",
                     "Analyse des types, valeurs manquantes, distributions, outliers et corrélations")

    show_eda_progress(EDA_STEPS, compact=True, single_row=True)

    # === DataFrame actif =====================================
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Charge un fichier dans l’onglet « Chargement ».")
        return

    # Colonnes numériques calculées UNE FOIS pour les onglets concernés
    num_cols = df.select_dtypes(include="number").columns.tolist()

    # === Navigation par onglets ==============================
    tabs = st.tabs([
        "🧬 Types", "🩹 Manquants", "📈 Statistiques",
        "📊 Distributions", "🚨 Outliers", "🔗 Corrélations", "🧼 Nettoyage auto"
    ])

    # ---------------------------------------------------------
    # 🧬 0) Types de colonnes
    # ---------------------------------------------------------

    with tabs[0]:
        st.subheader("🧬 Types de colonnes")

        # Résumé express (lignes, colonnes, %NA, etc.)
        from utils.eda_utils import summarize_dataframe  # (déjà importé plus haut chez toi, ok si en double)
        summary = summarize_dataframe(df)
        st.dataframe(summary, use_container_width=True)

        # Détails des dtypes (optionnels mais pratiques)
        with st.expander("🔎 Détails des dtypes par colonne", expanded=False):
            dtypes_df = (
                pd.DataFrame({"Colonne": df.columns, "dtype": [str(t) for t in df.dtypes]})
                .reset_index(drop=True)
            )
            st.dataframe(dtypes_df, use_container_width=True)

        # Message d’orientation vers la page atelier
        st.info(
            "ℹ️ Ceci est un **aperçu**. Pour **corriger finement les types** "
            "(conversions, datetime, booléens, etc.), utilisez la page **Typage** "
            "dans le menu. L’atelier n’affecte pas la barre de progression."
        )

        # Validation de l’étape "typing" (progression officielle)
        validate_step_button("typing", context_prefix="exploration_")


    # ---------------------------------------------------------
    # 🩹 1) Valeurs manquantes
    # ---------------------------------------------------------
    with tabs[1]:
        st.subheader("🩹 Analyse des valeurs manquantes")

        # seuil en [0..1]
        threshold = st.slider("🎯 Seuil de suppression (%)", 0.1, 1.0, 0.5)
        fig = plot_missing_values(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        cols_na = get_columns_above_threshold(df, threshold)  # seuil positionnel/clair

        if cols_na:
            st.warning(f"{len(cols_na)} colonnes dépassent le seuil de {threshold * 100:.0f}% de NA.")
            selected = st.multiselect("Colonnes à supprimer", cols_na, default=cols_na)

            if selected and st.button("🗑️ Supprimer sélection"):
                with st.expander("Colonnes supprimées", expanded=False):
                    st.write(selected)

                # ⚠️ In-place : ok ici, puis on reflète dans l'état
                df.drop(columns=selected, inplace=True, errors="ignore")
                st.session_state.df = df

                save_snapshot(df, "missing_dropped")
                log_action("missing_cleanup", f"{len(selected)} colonnes supprimées")
                st.success("✅ Colonnes supprimées avec succès.")
        else:
            st.info("✅ Aucune colonne ne dépasse le seuil défini.")

        validate_step_button("missing", context_prefix="exploration_")

    # ---------------------------------------------------------
    # 📈 2) Statistiques descriptives
    # ---------------------------------------------------------
    with tabs[2]:
        st.subheader("📈 Statistiques descriptives")

        # .describe() ne couvre que les colonnes numériques par défaut
        try:
            # Pour pandas ≥ 1.1
            stats = df.describe(include="all", datetime_is_numeric=True).T
        except TypeError:
            # Pour versions plus anciennes
            stats = df.describe(include="all").T

        st.dataframe(stats, use_container_width=True)

        # Pourcentage global de valeurs manquantes (toutes colonnes)
        pct_missing = df.isna().mean().mean() * 100
        st.info(f"Estimation globale de valeurs manquantes : **{pct_missing:.2f}%**")

        validate_step_button("stats", context_prefix="exploration_")

    # ---------------------------------------------------------
    # 📊 3) Distributions numériques
    # ---------------------------------------------------------
    with tabs[3]:
        st.subheader("📊 Distribution des variables numériques")

        if not num_cols:
            st.warning("⚠️ Aucune variable numérique détectée.")
        else:
            col = st.selectbox("📈 Variable à visualiser", num_cols, key="hist_col")
            fig = px.histogram(df, x=col, nbins=40, title=f"Distribution de {col}")
            st.plotly_chart(fig, use_container_width=True)

            skew = df[col].skew()
            skew_type = ("symétrique" if abs(skew) < 0.5
                         else "asymétrique positive" if skew > 0
                         else "asymétrique négative")
            st.info(f"Asymétrie de `{col}` : **{skew:.2f}** → *{skew_type}*")

        validate_step_button("distributions", context_prefix="exploration_")

    # ---------------------------------------------------------
    # 🚨 4) Outliers
    # ---------------------------------------------------------
    with tabs[4]:
        st.subheader("🚨 Détection d’outliers")

        if not num_cols:
            st.warning("⚠️ Pas de variable numérique pour détecter des outliers.")
        else:
            method = st.radio("Méthode de détection", ["iqr", "zscore"], horizontal=True, key="outliers_method")
            col = st.selectbox("🔍 Variable à analyser", num_cols, key="outliers_col")

            outliers = detect_outliers(df[[col]], method=method)
            st.info(f"{len(outliers)} outliers détectés sur `{col}` avec la méthode `{method}`")
            st.dataframe(outliers.head(10), use_container_width=True)

            if st.button("💾 Sauvegarder les outliers détectés", key="save_outliers"):
                save_snapshot(outliers, suffix=f"outliers_{method}")
                log_action("outliers_detected", f"{len(outliers)} détectés sur {col} ({method})")
                st.success("✅ Snapshot des outliers enregistré.")

        validate_step_button("extremes", context_prefix="exploration_")

    # ---------------------------------------------------------
    # 🔗 5) Corrélations
    # ---------------------------------------------------------
 
    with tabs[5]:
        st.subheader("🔗 Corrélations entre variables numériques")

        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour une corrélation.")
        else:
            # Choix de la méthode (radio = une seule à la fois)
            method = st.radio(
                "Méthode",
                ["pearson", "spearman", "kendall"],
                horizontal=True,
                key="corr_method"
            )

            # Calcul uniquement avec la méthode choisie
            from utils.eda_utils import compute_correlation_matrix
            corr = compute_correlation_matrix(df[num_cols], method=method)

            if corr.empty:
                st.info(f"Aucune corrélation exploitable pour la méthode **{method}**.")
            else:
                fig = px.imshow(
                    corr,
                    text_auto=".2f",
                    aspect="auto",
                    zmin=-1, zmax=1,
                    color_continuous_scale="RdBu_r",
                    title=f"Matrice de corrélation ({method})"
                )
                fig.update_layout(margin=dict(t=40, l=20, r=20, b=60))
                st.plotly_chart(fig, use_container_width=True)

        # Validation de l’étape
        validate_step_button("correlations", context_prefix="exploration_")

    # ---------------------------------------------------------
    # 🧼 6) Nettoyage automatique
    # ---------------------------------------------------------
    with tabs[6]:
        st.subheader("🧼 Nettoyage automatique des colonnes peu informatives")

        const_cols = detect_constant_columns(df)
        low_var = detect_low_variance_columns(df)
        na_cols = get_columns_above_threshold(df, 0.5)  # 50% NA
        all_to_drop = sorted(set(const_cols + low_var + na_cols))

        st.markdown(f"🔍 Colonnes identifiées à supprimer : **{len(all_to_drop)}**")

        if all_to_drop:
            with st.expander("Voir les colonnes candidates", expanded=False):
                # On n’affiche que les noms pour éviter d’ouvrir des DF énormes
                st.write(all_to_drop)

            if st.button("🧹 Appliquer le nettoyage automatique", key="auto_clean"):
                df.drop(columns=all_to_drop, inplace=True, errors="ignore")
                st.session_state.df = df

                save_snapshot(df, suffix="auto_cleaned")
                log_action("auto_cleanup", f"{len(all_to_drop)} colonnes supprimées")
                st.success("✅ Nettoyage appliqué avec succès.")
        else:
            st.info("Rien à nettoyer selon ces règles simples.")

        validate_step_button("cleaning", context_prefix="exploration_")

