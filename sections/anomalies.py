# ============================================================
# Fichier : sections/anomalies.py
# Objectif : Détection d’anomalies (z-score, IQR, MAD) sur colonnes numériques
# Version  : robuste (garde-fous NaN/Inf, std=0, UI paramétrable)
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe 
from utils.ui_utils import section_header, show_footer


# ------------------------------- Helpers numériques -------------------------------

def _numeric_cols(df: pd.DataFrame) -> list[str]:
    """Renvoie la liste ACTUELLE des colonnes numériques."""
    return df.select_dtypes(include="number").columns.tolist()


def _to_numeric_series(s: pd.Series) -> pd.Series:
    """Convertit la série en numérique (coerce), utile si la dtype est object/nullable."""
    if pd.api.types.is_numeric_dtype(s):
        return s
    return pd.to_numeric(s, errors="coerce")


def _finite_std(s: pd.Series) -> float:
    """
    Écart-type robuste : renvoie un sigma fini (float) ou 0.0 si non défini.
    - Ignore NaN
    - Vérifie finitude via numpy.isfinite (et pas pandas)
    """
    sigma = float(s.std(skipna=True)) if len(s) else 0.0
    if sigma == 0.0 or not np.isfinite(sigma):
        return 0.0
    return sigma


# ------------------------------- Méthodes d’anomalies -------------------------------

def anomalies_zscore(s: pd.Series, threshold: float = 3.0) -> pd.Series:
    """
    Z-score classique : outliers si |z| > threshold.
    Renvoie un booléen par ligne (True = anomalie).
    """
    s = _to_numeric_series(s)
    mu = float(s.mean(skipna=True)) if len(s) else 0.0
    sigma = _finite_std(s)
    if sigma == 0.0:  # garde-fou : aucune dispersion -> pas d’anomalies par z-score
        return pd.Series([False] * len(s), index=s.index)

    z = (s - mu) / sigma
    # np.isfinite pour gérer divisions, NaN/Inf
    mask = np.abs(z) > threshold
    mask = mask & np.isfinite(z.to_numpy())  # filter NaN/Inf
    return pd.Series(mask, index=s.index)


def anomalies_iqr(s: pd.Series, k: float = 1.5) -> pd.Series:
    """
    Méthode IQR : outliers si < Q1 - k*IQR ou > Q3 + k*IQR.
    Renvoie un booléen par ligne.
    """
    s = _to_numeric_series(s).dropna()
    if s.empty:
        return pd.Series([False] * len(s), index=s.index)

    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    if not np.isfinite(iqr) or iqr == 0:
        # Pas de dispersion en IQR => pas d’anomalies IQR
        return pd.Series([False] * len(s), index=s.index)

    low, high = q1 - k * iqr, q3 + k * iqr
    base_mask = (s < low) | (s > high)
    # Reprojetter sur l’index original (alignement avec NaN initiaux)
    mask = pd.Series([False] * len(base_mask.index.union(s.index)), index=base_mask.index)
    mask.loc[base_mask.index] = base_mask
    # Réindexer à la taille initiale de la colonne (avec NaN → False)
    return mask.reindex_like(_to_numeric_series(s)).fillna(False)


def anomalies_mad(s: pd.Series, threshold: float = 3.5) -> pd.Series:
    """
    Méthode MAD (Median Absolute Deviation), plus robuste que z-score si distribution non gaussienne.
    Score ≈ 0.6745 * (x - median) / MAD ; outliers si |score| > threshold.
    """
    x = _to_numeric_series(s)
    med = x.median(skipna=True)
    abs_dev = (x - med).abs()
    mad = float(abs_dev.median(skipna=True)) if len(x) else 0.0

    if mad == 0.0 or not np.isfinite(mad):
        return pd.Series([False] * len(x), index=x.index)

    score = 0.6745 * (x - med) / mad
    mask = np.abs(score) > threshold
    mask = mask & np.isfinite(score.to_numpy())
    return pd.Series(mask, index=x.index)


# ------------------------------- UI principale -------------------------------

def run_anomalies() -> None:
    """
    Page de détection d’anomalies :
      - Choix de la colonne numérique
      - Choix de la méthode (z-score, IQR, MAD)
      - Paramétrage des seuils
      - Aperçu table + histogramme
      - Snapshot exportable + logs
    """
    section_header(
        title="Anomalies",
        subtitle="Détecter des valeurs atypiques par z-score, IQR ou MAD.",
        section="exploration",  # réutilise la bannière de l’exploration si tu veux
        emoji="",
    )

    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucune donnée active. Importez un fichier dans **Chargement**.")
        return

    num_cols = _numeric_cols(df)
    if not num_cols:
        st.warning("⚠️ Pas de colonnes numériques détectées. Convertissez des colonnes via **Typage**.")
        show_footer(author="Xavier Rousseau", site_url="https://xavrousseau.github.io/", version="1.0")
        return

    # ---- Sélecteurs ----
    col = st.selectbox("🔢 Colonne à analyser", num_cols, key="anom_col")

    method = st.radio(
        "Méthode",
        ["z-score", "iqr", "mad"],
        horizontal=True,
        help=(
            "• z-score : adapté aux distributions ~gaussiennes\n"
            "• IQR : robuste aux extrêmes, simple\n"
            "• MAD : très robuste (distributions asymétriques/heavy-tailed)"
        ),
    )

    # Paramètres dynamiques selon la méthode
    if method == "z-score":
        thr = st.slider("Seuil |z|", min_value=2.0, max_value=6.0, value=3.0, step=0.1)
    elif method == "iqr":
        thr = st.slider("Facteur k (IQR)", min_value=1.0, max_value=5.0, value=1.5, step=0.1)
    else:  # mad
        thr = st.slider("Seuil MAD", min_value=2.0, max_value=7.0, value=3.5, step=0.1)

    # ---- Calcul anomalies avec garde-fous ----
    s = df[col]
    try:
        if method == "z-score":
            mask = anomalies_zscore(s, float(thr))
        elif method == "iqr":
            mask = anomalies_iqr(s, float(thr))
        else:
            mask = anomalies_mad(s, float(thr))
    except Exception as e:
        st.error(f"Erreur pendant la détection : {e}")
        return

    n_anom = int(mask.sum())
    st.info(f"🔎 Anomalies détectées sur **{col}** (méthode **{method}**) : **{n_anom}**")

    # ---- Aperçu table (top 10) ----
    if n_anom > 0:
        anomalies_df = df.loc[mask].copy()
        anomalies_df["_score_info"] = method  # marqueur léger
        st.dataframe(anomalies_df.head(10), use_container_width=True)
    else:
        st.success("✅ Aucune anomalie détectée avec ces paramètres.")

    # ---- Histogramme avec surlignage (simple) ----
    # On montre la distribution + une transparence sur les points outliers si z-score (sinon simple histo).
    with st.expander("📊 Visualisation"):
        try:
            xnum = _to_numeric_series(s)
            fig = px.histogram(xnum, nbins=40, title=f"Distribution de {col}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.warning("Impossible d’afficher l’histogramme pour cette colonne.")

    # ---- Actions (snapshot/export) ----
    col1, col2 = st.columns(2)
    with col1:
        if n_anom > 0 and st.button("💾 Snapshot des anomalies"):
            save_snapshot(df.loc[mask], suffix=f"anomalies_{method}_{col}")
            log_action("anomalies_snapshot", f"{n_anom} anomalies sur {col} via {method}")
            st.success("✅ Snapshot enregistré.")
    with col2:
        if st.button("📝 Journaliser l’analyse"):
            log_action("anomalies_run", f"col={col}, method={method}, param={thr}, n={n_anom}")
            st.toast("🗒️ Analyse journalisée.")


    # ---- Footer ----
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
