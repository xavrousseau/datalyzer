# ============================================================
# Fichier : anomalies.py
# Objectif : Détection d’outliers (Z-score / IQR) par variable
# Version refactorée avec améliorations UX et options supplémentaires
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from config import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe, validate_step_button  # Import de validate_step_button
from utils.ui_utils import show_header_image, show_icon_header, show_eda_progress


def run_anomalies():
    # === En-tête visuel et barre de progression ===
    show_header_image("bg_moon_trail.png")
    show_icon_header("🚨", "Anomalies", "Détection de valeurs extrêmes via Z-score ou IQR")
    show_eda_progress(EDA_STEPS, st.session_state.get("validation_steps", {}))

    # === Sélection du fichier actif ===
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Merci de sélectionner un fichier dans l’onglet Chargement.")
        return

    # === Sélection de variable numérique ===
    numerical_cols = df.select_dtypes(include="number").columns.tolist()
    if not numerical_cols:
        st.error("❌ Aucune variable numérique détectée dans le fichier.")
        return

    colonne = st.selectbox("📈 Variable à analyser", numerical_cols)
    methode = st.radio("🧮 Méthode de détection", ["z-score", "iqr"], horizontal=True)
    seuil = st.slider("Seuil de détection", 1.0, 5.0, 3.0, step=0.5)

    # === Détection d’anomalies selon la méthode choisie ===
    serie = df[colonne].dropna()

    if methode == "z-score":
        z = np.abs((serie - serie.mean()) / serie.std())
        mask = z > seuil
    else:
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        mask = (serie < q1 - seuil * iqr) | (serie > q3 + seuil * iqr)

    outliers = df.loc[mask.index[mask], :].copy()
    outliers["__outlier_sur__"] = colonne

    # === Affichage des résultats ===
    st.markdown(f"### 🔎 Résultats : **{len(outliers)} outliers détectés**")

    if not outliers.empty:
        # Afficher les 10 premiers outliers
        with st.expander("🔎 Détails des outliers détectés"):
            st.dataframe(outliers.head(10), use_container_width=True)

        # Histogramme avec superposition des outliers
        fig = px.histogram(df, x=colonne, nbins=40, title=f"Distribution de {colonne} avec outliers")
        fig.add_vlines(outliers[colonne], line_color="red", line_dash="dot")
        st.plotly_chart(fig, use_container_width=True)

        # Export des résultats
        if st.button("💾 Exporter les anomalies détectées"):
            save_snapshot(outliers, suffix="anomalies")
            log_action("anomalies_export", f"{len(outliers)} outliers détectés sur {colonne} via {methode}")
            st.success("✅ Snapshot des outliers sauvegardé.")

        # Sélection interactive des outliers
        st.subheader("🔧 Sélection et correction des outliers")
        selected_outliers = st.multiselect("Sélectionnez les outliers à corriger ou supprimer", outliers.index.tolist())
        if selected_outliers:
            df_corrected = df.drop(index=selected_outliers)
            st.session_state.df = df_corrected
            st.success(f"✅ {len(selected_outliers)} outliers supprimés.")

            # Analyse de l'impact avant/après suppression
            st.markdown("### 📊 Analyse de l'impact des corrections")
            before = serie[serie.index.isin(selected_outliers)]
            after = serie[~serie.index.isin(selected_outliers)]
            st.write(f"Avant correction : {before.describe()}")
            st.write(f"Après correction : {after.describe()}")

    else:
        st.success("✅ Aucun outlier détecté sur cette variable.")

    # === Validation finale de l'étape ===
    validate_step_button("anomalies")  # Remplacement de validate_step par validate_step_button
