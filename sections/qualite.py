# sections/qualite.py

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import zscore
from utils.eda_utils import detect_constant_columns


def run_qualite(df):
    st.subheader("🚨 Problèmes potentiels de qualité des données")
    st.markdown(f"🔎 **Fichier sélectionné : `{df.shape[0]} lignes × {df.shape[1]} colonnes`**")

    # -------------------------------------------------------------------------
    st.markdown("### 🔍 Colonnes mal typées")
    suspect_numeric_as_str = [
        col for col in df.select_dtypes(include="object")
        if df[col].str.replace(".", "", regex=False).str.replace(",", "", regex=False).str.isnumeric().mean() > 0.8
    ]
    if suspect_numeric_as_str:
        st.warning("📌 Ces colonnes semblent contenir des valeurs numériques mais sont typées comme 'object' :")
        st.code(", ".join(suspect_numeric_as_str))
    else:
        st.success("✅ Aucun champ suspect détecté parmi les variables 'object'.")

    # -------------------------------------------------------------------------
    st.markdown("### 📛 Noms suspects ou non normalisés")
    suspect_names = [col for col in df.columns if col.startswith("Unnamed") or "id" in col.lower()]
    if suspect_names:
        st.warning("⚠️ Colonnes avec noms suspects :")
        st.code(", ".join(suspect_names))
    else:
        st.success("✅ Aucun nom de colonne suspect détecté.")

    # -------------------------------------------------------------------------
    st.markdown("### 🧩 Valeurs suspectes ou placeholders")
    placeholder_values = ["unknown", "n/a", "na", "undefined", "None", "missing", "?"]
    placeholder_hits = {
        col: df[col].astype(str).str.lower().isin(placeholder_values).sum()
        for col in df.columns
        if df[col].astype(str).str.lower().isin(placeholder_values).sum() > 0
    }
    if placeholder_hits:
        st.warning("🔍 Valeurs suspectes trouvées (placeholders) :")
        st.write(pd.DataFrame.from_dict(placeholder_hits, orient="index", columns=["Occurrences"]))
    else:
        st.success("✅ Aucune valeur placeholder détectée.")

    # -------------------------------------------------------------------------
    st.markdown("### 🧪 Valeurs extrêmes (Z-score simplifié)")
    z_outlier_summary = {
        col: (np.abs(zscore(df[col].dropna())) > 3).sum()
        for col in df.select_dtypes(include="number").columns
        if df[col].dropna().std() != 0
    }
    z_outlier_summary = {col: count for col, count in z_outlier_summary.items() if count > 0}
    if z_outlier_summary:
        st.warning("🚨 Valeurs extrêmes détectées (Z-score > 3) :")
        st.write(pd.DataFrame.from_dict(z_outlier_summary, orient="index", columns=["Nb outliers"]))
    else:
        st.success("✅ Pas de valeurs extrêmes détectées via Z-score.")

    # -------------------------------------------------------------------------
    st.markdown("### 📌 Colonnes constantes")
    const_cols = detect_constant_columns(df)
    if const_cols:
        st.warning(f"⚠️ Colonnes constantes détectées ({len(const_cols)}) :")
        st.code(", ".join(const_cols))
    else:
        st.success("✅ Aucune colonne constante détectée.")
