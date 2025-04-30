# ============================================================
# Fichier : exploration.py
# Objectif : Analyse exploratoire avancée et interactive
# pour Datalyzer (version Streamlit)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.eda_utils import (
    summarize_dataframe,
    plot_missing_values,
    detect_constant_columns,
    detect_low_variance_columns,
    get_columns_above_threshold,
    detect_outliers_iqr
)
from utils.snapshot_utils import save_snapshot, list_snapshots, load_snapshot_by_name
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_exploration(df: pd.DataFrame):
    # 🎴 Image d’introduction
    show_header_image("bg_sakura_peaceful.png")

    st.title("🔍 Analyse exploratoire des données")

    # ========== Sidebar : Sélection du snapshot ==========
    st.sidebar.header("📁 Snapshot")
    snapshots = list_snapshots()
    selected_snapshot = st.sidebar.selectbox("Sélectionnez un snapshot", snapshots, index=0)
    if selected_snapshot:
        df = load_snapshot_by_name(selected_snapshot)
        st.session_state.df = df
        st.success(f"✅ Snapshot chargé : {selected_snapshot}")

    # ========== Tabs principaux ==========
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Types", "Valeurs manquantes", "Distributions", "Outliers",
        "Nettoyage auto", "Analyse avancée"
    ])

    # Onglet 1 — Types
    with tab1:
        st.subheader("🧬 Types de colonnes")
        st.dataframe(df.dtypes.reset_index().rename(columns={"index": "Colonne", 0: "Type"}))

    # Onglet 2 — Valeurs manquantes
    with tab2:
        st.subheader("🩹 Analyse des valeurs manquantes")

        seuil = st.slider("Seuil de suppression (en %)", min_value=0.1, max_value=1.0, step=0.05, value=0.5)
        df_na_ratio = df.isna().mean()
        cols_to_drop = df_na_ratio[df_na_ratio > seuil].index.tolist()

        st.markdown(f"🔎 Colonnes avec plus de {seuil*100:.0f}% de NA : **{len(cols_to_drop)}**")
        st.dataframe(df[cols_to_drop].isna().mean().to_frame("Taux de NA"))

        fig = plot_missing_values(df)
        st.plotly_chart(fig)

        if st.button("🚮 Supprimer les colonnes sélectionnées"):
            df.drop(columns=cols_to_drop, inplace=True)
            st.session_state.df = df
            save_snapshot(df, suffix="missing_cleaned")
            st.success("Colonnes supprimées. Nouveau snapshot enregistré.")
            log_action("missing_cleanup", f"{len(cols_to_drop)} colonnes supprimées")

    # Onglet 3 — Distributions
    with tab3:
        st.subheader("📊 Distributions des variables numériques")
        numeric_cols = df.select_dtypes(include="number").columns

        if len(numeric_cols) == 0:
            st.warning("Aucune colonne numérique trouvée.")
        else:
            for col in numeric_cols:
                fig = px.histogram(df, x=col, nbins=30, title=f"Distribution de {col}")
                st.plotly_chart(fig)

    # Onglet 4 — Outliers
    with tab4:
        st.subheader("🚨 Détection d’outliers (méthode IQR)")

        outliers_df = detect_outliers_iqr(df)
        if not outliers_df.empty:
            st.markdown(f"🔎 Nombre de lignes détectées comme outliers : **{len(outliers_df)}**")
            st.dataframe(outliers_df.head(10))

            if st.button("💾 Sauvegarder les outliers détectés"):
                save_snapshot(outliers_df, suffix="outliers")
                st.success("Snapshot des outliers sauvegardé.")
                log_action("outliers_detected", f"{len(outliers_df)} lignes")
        else:
            st.info("✅ Aucun outlier détecté sur les variables numériques.")

    # Onglet 5 — Nettoyage automatique
    with tab5:
        st.subheader("🧹 Nettoyage automatique des colonnes")

        constant_cols = detect_constant_columns(df)
        low_var_cols = detect_low_variance_columns(df)
        na_cols = get_columns_above_threshold(df, seuil=0.5)

        all_cols_to_drop = list(set(constant_cols + low_var_cols + na_cols))
        st.markdown(f"🔍 Colonnes candidates à suppression : **{len(all_cols_to_drop)}**")
        st.write(all_cols_to_drop)

        if st.button("🧼 Appliquer le nettoyage auto"):
            df.drop(columns=all_cols_to_drop, inplace=True)
            st.session_state.df = df
            save_snapshot(df, suffix="auto_cleaned")
            st.success("Colonnes supprimées. Snapshot sauvegardé.")
            log_action("auto_cleanup", f"{len(all_cols_to_drop)} colonnes supprimées")

    # Onglet 6 — Analyse avancée
    with tab6:
        st.subheader("🔬 Score qualité & redondances")

        duplicated_rows = df[df.duplicated()]
        unique_vals = df.nunique().reset_index()
        unique_vals.columns = ["Colonne", "Valeurs uniques"]

        score = max(0, 100 - (
            df.isna().mean().mean() * 40 +
            (1 if not duplicated_rows.empty else 0) * 20 +
            (unique_vals["Valeurs uniques"] <= 1).sum() / df.shape[1] * 40
        ))

        st.markdown(f"🌸 **Score qualité global : {score:.0f} / 100**")

        if not duplicated_rows.empty:
            st.markdown("🔁 Lignes dupliquées")
            st.dataframe(duplicated_rows.head(10))
        else:
            st.success("✅ Aucun doublon trouvé.")

        st.markdown("🧮 Nombre de valeurs uniques par colonne")
        st.dataframe(unique_vals)

        validate_step_button(df, step_name="exploration")
