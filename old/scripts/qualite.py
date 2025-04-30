# ============================================================
# Fichier : qualite.py
# Objectif : Évaluer et corriger la qualité des données
# Version finale unifiée pour Datalyzer (Streamlit)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import zscore

from utils.eda_utils import detect_constant_columns
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_qualite():
    show_header_image("bg_pagoda_moon.png")
    st.title("🧪 Analyse de la qualité des données")

    if "df" not in st.session_state:
        st.warning("📂 Veuillez charger un fichier.")
        st.stop()

    df = st.session_state.df

    # ========== Score global de qualité ==========
    st.markdown("### 🌸 Score global de qualité")
    na_penalty = df.isna().mean().mean() * 40
    dup_penalty = 20 if df.duplicated().any() else 0
    const_penalty = (df.nunique() <= 1).sum() / df.shape[1] * 40
    score = max(0, int(100 - (na_penalty + dup_penalty + const_penalty)))
    st.subheader(f"🌟 **{score} / 100**")
    st.divider()

    # ========== Anomalies détectées ==========
    st.markdown("### 🧾 Résumé des anomalies")
    nb_const = (df.nunique() <= 1).sum()
    nb_na50 = (df.isna().mean() > 0.5).sum()
    nb_dup = df.duplicated().sum()

    st.markdown(f"""
    - 🔁 **{nb_dup} lignes dupliquées**  
    - 🟨 **{nb_na50} colonnes avec plus de 50% de NA**  
    - 🧊 **{nb_const} colonnes constantes**
    """)
    st.divider()

    # ========== Heatmap des valeurs manquantes ==========
    if st.checkbox("📊 Afficher la heatmap des NA"):
        fig = px.imshow(df.isna(), aspect="auto", color_continuous_scale="Blues",
                        title="Carte des valeurs manquantes")
        st.plotly_chart(fig)
    st.divider()

    # ========== Vérifications supplémentaires ==========
    st.markdown("### 🩺 Vérifications supplémentaires")

    # Nombres stockés en texte
    suspect_numeric_as_str = [
        col for col in df.select_dtypes(include="object")
        if df[col].str.replace(".", "", regex=False).str.replace(",", "", regex=False).str.isnumeric().mean() > 0.8
    ]
    if suspect_numeric_as_str:
        st.warning("🔢 Colonnes typées `object` contenant majoritairement des chiffres :")
        st.code(", ".join(suspect_numeric_as_str))

    # Noms suspects
    suspect_names = [col for col in df.columns if col.startswith("Unnamed") or "id" in col.lower()]
    if suspect_names:
        st.warning("📛 Noms de colonnes suspects :")
        st.code(", ".join(suspect_names))

    # Valeurs placeholder
    placeholder_values = ["unknown", "n/a", "na", "undefined", "none", "missing", "?"]
    placeholder_hits = {
        col: df[col].astype(str).str.lower().isin(placeholder_values).sum()
        for col in df.columns
        if df[col].astype(str).str.lower().isin(placeholder_values).sum() > 0
    }
    if placeholder_hits:
        st.warning("❓ Valeurs placeholders détectées :")
        st.dataframe(pd.DataFrame.from_dict(placeholder_hits, orient="index", columns=["Occurrences"]))

    st.divider()

    # ========== Outliers via Z-score ==========
    st.markdown("### 📉 Valeurs extrêmes (Z-score > 3)")
    z_outliers = {
        col: (np.abs(zscore(df[col].dropna())) > 3).sum()
        for col in df.select_dtypes(include="number").columns
        if df[col].dropna().std() != 0
    }
    z_outliers = {k: v for k, v in z_outliers.items() if v > 0}
    if z_outliers:
        st.warning("🚨 Outliers détectés :")
        st.dataframe(pd.DataFrame.from_dict(z_outliers, orient="index", columns=["Nb outliers"]))
    else:
        st.success("✅ Aucun outlier détecté.")

    st.divider()

    # ========== Colonnes constantes ==========
    const_cols = detect_constant_columns(df)
    if const_cols:
        st.warning(f"⚠️ Colonnes constantes détectées ({len(const_cols)}) :")
        st.code(", ".join(const_cols))
    st.divider()

    # ========== Correction automatique ==========
    st.markdown("### 🧼 Correction automatique des colonnes problématiques")
    if st.button("Corriger maintenant"):
        try:
            to_drop = df.columns[(df.nunique() <= 1) | (df.isna().mean() > 0.5)].tolist()
            df.drop(columns=to_drop, inplace=True)
            st.session_state.df = df

            save_snapshot(df, suffix="qualite_cleaned")
            log_action("qualite_auto_fix", f"{len(to_drop)} colonnes supprimées")

            st.success(f"✅ Correction appliquée : {len(to_drop)} colonnes supprimées.")
        except Exception as e:
            st.error(f"❌ Erreur pendant la correction : {e}")

    st.divider()

    # ========== Validation étape ==========
    validate_step_button(df, step_name="qualite")
