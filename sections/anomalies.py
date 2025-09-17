# ============================================================
# Fichier : anomalies.py
# Objectif : Détection d’outliers (Z-score / IQR) par variable
# Version : alignée avec utils.eda_utils, barre compacte et étape EDA "extremes"
# ============================================================

import os
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.steps import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header
from utils.eda_utils import detect_outliers  # 🔁 source unique pour la détection


def run_anomalies():
    # === En-tête visuel + barre compacte =====================
    show_header_image_safe("bg_moon_trail.png")
    show_icon_header("🚨", "Anomalies", "Détection de valeurs extrêmes via Z-score ou IQR")
 

    # === Sélection du DataFrame actif ========================
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Sélectionne/charge un fichier dans l’onglet « Chargement ».")
        return

    # Variables numériques disponibles
    numerical_cols = df.select_dtypes(include="number").columns.tolist()
    if not numerical_cols:
        st.error("❌ Aucune variable numérique détectée dans le fichier.")
        return

    # === Paramètres d'analyse =================================
    col = st.selectbox("📈 Variable à analyser", numerical_cols, key="anom_col")
    method = st.radio("🧮 Méthode de détection", ["zscore", "iqr"], horizontal=True, key="anom_method")
    threshold = st.slider("Seuil de détection", 1.0, 5.0, 3.0, step=0.5, key="anom_thr")

    serie = df[col].dropna()

    # Garde-fous pour bornes et messages
    mu = float(serie.mean()) if not serie.empty else 0.0
    sigma = float(serie.std(ddof=0)) if not serie.empty else 0.0
    q1, q3 = (float(serie.quantile(0.25)) if not serie.empty else 0.0,
              float(serie.quantile(0.75)) if not serie.empty else 0.0)
    iqr = q3 - q1

    # === Détection via utilitaire commun ======================
    # detect_outliers s’attend à un DF (même une seule colonne)
    try:
        outliers = detect_outliers(df[[col]], method=method if method != "zscore" else "zscore", threshold=threshold)
        # on obtient soit un DataFrame des lignes outliers, soit un index — on harmonise :
        if isinstance(outliers, pd.Index):
            outliers_df = df.loc[outliers].copy()
        elif isinstance(outliers, pd.DataFrame):
            # si l’outil renvoie juste la colonne, on la recolle à df :
            if list(outliers.columns) == [col]:
                outliers_df = df.loc[outliers.index].copy()
            else:
                outliers_df = outliers.copy()
        else:
            # cas de repli (shouldn’t happen)
            outliers_df = df.loc[df.index.intersection(serie.index)].iloc[0:0].copy()
    except Exception as e:
        st.error(f"❌ Erreur dans la détection des outliers : {e}")
        return

    outliers_df["__outlier_sur__"] = col

    # === Résultats & visuels ==================================
    n_out = len(outliers_df)
    st.markdown(f"### 🔎 Résultats : **{n_out} outlier(s)** détecté(s) sur `{col}` (méthode : **{method}**)")
    if n_out:
        with st.expander("🔎 Détails des outliers détectés"):
            st.dataframe(outliers_df.head(10), use_container_width=True)

    # Histogramme + bornes claires (plutôt que des centaines de vlines)
    fig = px.histogram(df, x=col, nbins=40, title=f"Distribution de {col}")
    # Ajout des bornes selon la méthode choisie
    if method == "zscore":
        if sigma == 0:
            st.info("ℹ️ σ = 0 (distribution dégénérée) : pas de bornes Z-score tracées.")
        else:
            lower = mu - threshold * sigma
            upper = mu + threshold * sigma
            fig.add_vline(x=lower, line_color="red", line_dash="dash")
            fig.add_vline(x=upper, line_color="red", line_dash="dash")
            st.caption(f"Bornes Z-score : [{lower:.3g}, {upper:.3g}]  (μ={mu:.3g}, σ={sigma:.3g}, z={threshold})")
    else:  # IQR
        if iqr == 0:
            st.info("ℹ️ IQR = 0 (Q1=Q3) : pas de bornes IQR tracées.")
        else:
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            fig.add_vline(x=lower, line_color="red", line_dash="dash")
            fig.add_vline(x=upper, line_color="red", line_dash="dash")
            st.caption(f"Bornes IQR : [{lower:.3g}, {upper:.3g}]  (Q1={q1:.3g}, Q3={q3:.3g}, IQR={iqr:.3g}, k={threshold})")

    st.plotly_chart(fig, use_container_width=True)

    # === Export / snapshot des anomalies ======================
    if n_out and st.button("💾 Exporter les anomalies détectées", key="anom_export"):
        save_snapshot(outliers_df, suffix=f"outliers_{method}")
        log_action("anomalies_export", f"{n_out} outliers sur {col} via {method} (seuil={threshold})")
        st.success("✅ Snapshot des outliers sauvegardé.")

    # === Sélection & correction (suppression) =================
    if n_out:
        st.subheader("🔧 Sélection et correction des outliers")
        # multiselect sur l’index des lignes outliers
        selected_idx = st.multiselect(
            "Lignes à supprimer (index du DataFrame)",
            options=outliers_df.index.tolist(),
            key="anom_sel_idx"
        )
        if selected_idx:
            df_corrected = df.drop(index=selected_idx)
            st.session_state.df = df_corrected
            st.success(f"✅ {len(selected_idx)} outlier(s) supprimé(s).")

            # Impact avant/après sur la variable cible
            with st.expander("📊 Impact des suppressions", expanded=False):
                before = df[col]
                after = df_corrected[col]
                st.write("Avant :", before.describe())
                st.write("Après  :", after.describe())

    else:
        st.success("✅ Aucun outlier détecté sur cette variable.")

 
