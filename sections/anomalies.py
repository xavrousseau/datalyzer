# ============================================================
# Fichier : sections/anomalies.py
# Objectif : Détection d’outliers (Z-score / IQR) par variable
# Version  : UI unifiée + barre compacte + étape EDA "outliers"
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.steps import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe, validate_step_button
from utils.ui_utils import section_header, show_eda_progress, show_footer
from utils.eda_utils import detect_outliers  # source unique pour la détection


def run_anomalies() -> None:
    """
    Atelier « Anomalies » (outliers univariés).

    Méthodes proposées :
      - zscore : valeurs dont |(x - μ) / σ| > seuil (par défaut 3).
      - iqr    : valeurs hors [Q1 - k*IQR ; Q3 + k*IQR] (k = seuil, par défaut 3).

    Parcours :
      1) Sélectionner une variable numérique.
      2) Choisir méthode + seuil (interprétation adaptée à la méthode).
      3) Visualiser histogramme + bornes, lister les outliers.
      4) Exporter le sous-ensemble (snapshot) et/ou supprimer des lignes.

    Robustesse :
      - Ignore les NaN et non-finis pour les stats (remplacés par NaN).
      - Gère σ=0 (distribution plate) et IQR=0 (Q1=Q3) sans tracer de bornes.
    """
    # ---------- En-tête unifié ----------
    section_header(
        title="Anomalies",
        subtitle="Détection de valeurs extrêmes via Z-score ou IQR.",
        section="analyse",   # → image depuis config.SECTION_BANNERS["analyse"]
        emoji="🚨",
    )

    # ---------- Barre de progression (visuelle) ----------
    show_eda_progress(EDA_STEPS, compact=True, single_row=True)

    # ---------- DataFrame actif ----------
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Sélectionnez/chargez un fichier dans l’onglet **Chargement**.")
        return

    # Colonnes numériques uniquement (zscore/iqr supposent des quantités)
    numerical_cols = df.select_dtypes(include="number").columns.tolist()
    if not numerical_cols:
        st.error("❌ Aucune variable numérique détectée dans le fichier.")
        return

    # ---------- Paramètres d'analyse ----------
    col = st.selectbox("📈 Variable à analyser", numerical_cols, key="anom_col")
    method = st.radio(
        "🧮 Méthode de détection",
        ["zscore", "iqr"],
        horizontal=True,
        key="anom_method",
        help=(
            "Z-score : |(x-μ)/σ| > seuil (ex. 3). "
            "IQR : hors [Q1 - k·IQR ; Q3 + k·IQR] (k = seuil, ex. 1.5 ou 3)."
        ),
    )
    # Par convention : z=3 (classique) ; pour IQR, k=1.5 ou 3 sont courants.
    default_thr = 3.0 if method == "zscore" else 1.5
    threshold = st.slider(
        "Seuil de détection",
        min_value=0.5, max_value=5.0, value=default_thr, step=0.5, key="anom_thr",
        help="Z-score : seuil en écart-types ; IQR : multiplicateur de l’intervalle inter-quartile."
    )

    # Série nettoyée pour les statistiques (NaN/±inf -> NaN)
    serie = pd.to_numeric(df[col], errors="coerce")
    finite_mask = pd.Series(pd.notna(serie) & ~pd.isna(serie))
    serie = serie[finite_mask]

    # Stats utiles pour bornes & annotations
    mu = float(serie.mean()) if not serie.empty else 0.0
    sigma = float(serie.std(ddof=0)) if not serie.empty else 0.0
    q1 = float(serie.quantile(0.25)) if not serie.empty else 0.0
    q3 = float(serie.quantile(0.75)) if not serie.empty else 0.0
    iqr = q3 - q1

    # ---------- Détection via utilitaire commun ----------
    try:
        outliers = detect_outliers(df[[col]], method=method, threshold=threshold)
        # Harmonisation du retour (Index ou DataFrame) en DataFrame complet :
        if isinstance(outliers, pd.Index):
            outliers_df = df.loc[outliers].copy()
        elif isinstance(outliers, pd.DataFrame):
            # Si l’outil renvoie un DF filtré avec la seule colonne, on remonte les lignes complètes
            outliers_df = df.loc[outliers.index].copy() if list(outliers.columns) == [col] else outliers.copy()
        else:
            outliers_df = df.iloc[0:0].copy()
    except Exception as e:
        st.error(f"❌ Erreur dans la détection des outliers : {e}")
        return

    # Marqueur visuel (facilite l’export/filtrage)
    if not outliers_df.empty:
        outliers_df["__outlier_sur__"] = col

    # ---------- Résultats & visuels ----------
    n_out = len(outliers_df)
    st.markdown(f"### 🔎 Résultats : **{n_out} outlier(s)** détecté(s) sur `{col}` (méthode : **{method}**)")

    if n_out:
        with st.expander("🔎 Détails des outliers détectés"):
            st.dataframe(outliers_df.head(10), use_container_width=True)

    # Histogramme global avec bornes selon la méthode choisie
    fig = px.histogram(df, x=col, nbins=40, title=f"Distribution de {col}")

    if method == "zscore":
        if sigma == 0 or not pd.isfinite(sigma):
            st.info("ℹ️ σ = 0 (ou non défini) : pas de bornes Z-score tracées.")
        else:
            lower = mu - threshold * sigma
            upper = mu + threshold * sigma
            fig.add_vline(x=lower, line_color="red", line_dash="dash")
            fig.add_vline(x=upper, line_color="red", line_dash="dash")
            st.caption(f"Bornes Z-score : [{lower:.3g}, {upper:.3g}]  (μ={mu:.3g}, σ={sigma:.3g}, z={threshold})")
    else:  # IQR
        if iqr == 0 or not pd.isfinite(iqr):
            st.info("ℹ️ IQR = 0 (Q1=Q3) : pas de bornes IQR tracées.")
        else:
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            fig.add_vline(x=lower, line_color="red", line_dash="dash")
            fig.add_vline(x=upper, line_color="red", line_dash="dash")
            st.caption(f"Bornes IQR : [{lower:.3g}, {upper:.3g}]  (Q1={q1:.3g}, Q3={q3:.3g}, IQR={iqr:.3g}, k={threshold})")

    st.plotly_chart(fig, use_container_width=True)

    # ---------- Export / snapshot des anomalies ----------
    if n_out and st.button("💾 Exporter les anomalies détectées", key="anom_export"):
        save_snapshot(outliers_df, suffix=f"outliers_{method}")
        log_action("anomalies_export", f"{n_out} outliers sur {col} via {method} (seuil={threshold})")
        st.success("✅ Snapshot des outliers sauvegardé.")

    # ---------- Sélection & correction (suppression) ----------
    if n_out:
        st.subheader("🔧 Sélection et correction des outliers")
        selected_idx = st.multiselect(
            "Lignes à supprimer (index du DataFrame)",
            options=outliers_df.index.tolist(),
            key="anom_sel_idx",
            help="Vous pouvez sélectionner un sous-ensemble d’outliers à retirer."
        )
        if selected_idx:
            df_corrected = df.drop(index=selected_idx)
            st.session_state["df"] = df_corrected
            save_snapshot(df_corrected, suffix=f"{col}_outliers_removed")
            log_action("anomalies_removed", f"{len(selected_idx)} supprimés sur {col}")
            st.success(f"✅ {len(selected_idx)} outlier(s) supprimé(s).")

            with st.expander("📊 Impact des suppressions", expanded=False):
                before = df[col]
                after = df_corrected[col]
                st.write("Avant :", before.describe())
                st.write("Après  :", after.describe())
    else:
        st.success("✅ Aucun outlier détecté sur cette variable.")

    # ---------- Validation d’étape (cohérente avec config.EDA_STEPS) ----------
    validate_step_button("outliers", context_prefix="anomalies_")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
