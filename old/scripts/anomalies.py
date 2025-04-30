# ============================================================
# Fichier : anomalies.py
# Objectif : Détection d’outliers (Z-score / IQR) sur une variable
# avec export, visualisation et snapshot
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_anomalies(df: pd.DataFrame):
    # 🎴 Image décorative
    show_header_image("bg_moon_trail.png")

    st.title("🚨 Détection d’anomalies (Outliers)")
    st.markdown("Analyse automatique via méthode Z-score ou IQR sur une variable numérique.")

    # ========== Sélection d'une variable numérique ==========
    numerical_cols = df.select_dtypes(include="number").columns.tolist()
    if not numerical_cols:
        st.error("❌ Aucune variable numérique disponible.")
        return

    colonne = st.selectbox("📈 Variable à analyser", numerical_cols)
    methode = st.radio("🧮 Méthode", ["z-score", "iqr"], horizontal=True)
    seuil = st.slider("Seuil (Z ou IQR)", min_value=1.0, max_value=5.0, step=0.5, value=3.0)

    # ========== Détection des outliers ==========
    outliers = pd.DataFrame()
    mask = None
    serie = df[colonne].dropna()

    if methode == "z-score":
        z = np.abs((serie - serie.mean()) / serie.std())
        mask = z > seuil
    elif methode == "iqr":
        q1 = serie.quantile(0.25)
        q3 = serie.quantile(0.75)
        iqr = q3 - q1
        mask = (serie < q1 - seuil * iqr) | (serie > q3 + seuil * iqr)

    outliers = df.loc[mask.index[mask], :].copy()
    outliers["__outlier_sur__"] = colonne

    st.markdown(f"### 🔎 Résultats : {len(outliers)} outliers détectés")

    # ========== Affichage et export ==========
    if not outliers.empty:
        st.dataframe(outliers.head(10))

        fig = px.histogram(df, x=colonne, nbins=40, title=f"Distribution de {colonne} avec outliers")
        fig.add_vlines(outliers[colonne], line_color="red", line_dash="dot")
        st.plotly_chart(fig)

        if st.button("💾 Exporter les anomalies détectées"):
            save_snapshot(outliers, suffix="anomalies")
            log_action("anomalies_export", f"{len(outliers)} lignes détectées sur {colonne} via {methode}")
            st.success("✅ Snapshot des outliers sauvegardé.")
    else:
        st.success("✅ Aucun outlier détecté.")

    # ========== Validation de l'étape ==========
    validate_step_button(df, step_name="anomalies")
