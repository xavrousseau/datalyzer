# ============================================================
# Fichier : sections/multivariee.py
# Objectif : Analyses multivariées interactives (PCA & K-means)
# Version  : UI unifiée + étapes EDA + snapshots & logs
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from utils.steps import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe, validate_step_button
from utils.ui_utils import section_header, show_eda_progress, show_footer


# =============================== Helpers internes ==============================

def _select_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retourne un sous-DataFrame numérique (float/int) sans NA (listwise),
    pour un usage simple avec PCA/K-means.

    Remarque :
      - On effectue un dropna() pour la clarté pédagogique. Pour de très
        grands datasets, envisager une imputation en amont dans une autre page.
    """
    num = df.select_dtypes(include=["number"]).copy()
    return num.dropna(axis=0, how="any")


def _standardize(X: pd.DataFrame, with_mean: bool = True, with_std: bool = True) -> tuple[pd.DataFrame, StandardScaler]:
    """
    Standardise les colonnes (Z-score) via StandardScaler (sklearn).

    Retour :
      - X_std : DataFrame standardisé avec mêmes index/colonnes
      - scaler : objet StandardScaler pour inversions/exports éventuels
    """
    scaler = StandardScaler(with_mean=with_mean, with_std=with_std)
    Z = scaler.fit_transform(X.values)
    X_std = pd.DataFrame(Z, index=X.index, columns=X.columns)
    return X_std, scaler


def _fit_pca(X: pd.DataFrame, n_components: int) -> tuple[PCA, pd.DataFrame, pd.Series, pd.Series]:
    """
    Ajuste une PCA et renvoie :
      - pca          : modèle PCA sklearn
      - scores (DF)  : projections (composantes principales)
      - exp_var (%)  : variance expliquée par composante (en %)
      - cum_exp_var (%): cumul de variance expliquée (en %)
    """
    pca = PCA(n_components=n_components, random_state=42)
    T = pca.fit_transform(X.values)
    cols = [f"PC{i+1}" for i in range(n_components)]
    scores = pd.DataFrame(T, index=X.index, columns=cols)
    exp = pd.Series(pca.explained_variance_ratio_ * 100, index=cols, name="Explained Var (%)")
    cum = exp.cumsum().rename("Cumulative (%)")
    return pca, scores, exp, cum


def _fit_kmeans(X: pd.DataFrame, k: int, n_init: int = "auto", random_state: int = 42) -> tuple[KMeans, np.ndarray, float]:
    """
    Ajuste un K-means et retourne :
      - modèle KMeans
      - labels (np.ndarray)
      - silhouette (float) si calculable, sinon NaN
    """
    km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state)
    labels = km.fit_predict(X.values)
    sil = float("nan")
    # silhouette_score nécessite au moins 2 clusters non vides
    try:
        if len(set(labels)) > 1:
            sil = float(silhouette_score(X.values, labels))
    except Exception:
        pass
    return km, labels, sil


# ================================== Vue =======================================

def run_multivariee() -> None:
    """
    Page « Analyses multivariées » :

    Modules :
      - PCA (Analyse en Composantes Principales)
        * Standardisation optionnelle
        * Choix du nombre de composantes
        * Scree plot (variance expliquée) + cumul
        * Projection 2D/3D + (mini) biplot chargeings
      - K-means
        * Clustering sur l’espace standardisé OU sur l’espace PCA
        * Évaluation silhouette, sauvegarde des clusters

    Effets :
      - Les projections et labels sont ajoutés au DataFrame actif (colonnes 'PC*' et 'cluster_k').
      - Des snapshots sont créés pour tracer l’historique.
      - Les actions sont loguées.
    """
    # ---------- En-tête + barre compacte ----------
    section_header(
        title="Multivariée",
        subtitle="PCA pour réduire la dimension et K-means pour regrouper les observations.",
        section="analyse",
        emoji="🧩",
    )
    show_eda_progress(EDA_STEPS, compact=True, single_row=True)

    # ---------- DataFrame actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Importez un fichier via **Chargement**.")
        return

    # ---------- Sélection des variables & options globales ----------
    st.markdown("### 🔧 Préparation des données")
    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.empty:
        st.error("❌ Aucune colonne numérique disponible pour l’analyse multivariée.")
        return

    with st.expander("Sélection des variables (numériques)", expanded=True):
        cols_selected = st.multiselect(
            "Variables à inclure",
            options=numeric_df.columns.tolist(),
            default=numeric_df.columns.tolist(),
            help="Retirez les variables hors-sujet ou redondantes avant la PCA/K-means."
        )

    if not cols_selected:
        st.info("Sélectionnez au moins une variable.")
        return

    # Prétraitement simple : sous-ensemble + dropna
    X_raw = df[cols_selected].copy()
    X = _select_numeric(X_raw)  # dropna listwise
    dropped = len(X_raw) - len(X)
    if dropped:
        st.caption(f"ℹ️ {dropped} ligne(s) supprimée(s) pour valeurs manquantes sur les variables retenues.")

    # ============================== PCA =======================================
    st.markdown("## 📉 PCA — Réduction de dimension")

    col_std1, col_std2 = st.columns(2)
    with col_std1:
        do_standardize = st.checkbox("Standardiser (Z-score)", value=True, help="Recommandé si les échelles diffèrent.")
    with col_std2:
        n_comp = st.slider("Nombre de composantes", min_value=2, max_value=min(10, len(cols_selected)), value=2)

    X_std, scaler = _standardize(X) if do_standardize else (X.copy(), None)
    pca, scores, exp, cum = _fit_pca(X_std, n_components=n_comp)

    # Scree plot (variance expliquée)
    scree_df = pd.DataFrame({"Composante": exp.index, "Var (%)": exp.values, "Cumul (%)": cum.values})
    fig_scree = px.bar(scree_df, x="Composante", y="Var (%)", title="Scree plot — Variance expliquée par composante")
    fig_scree.add_scatter(x=scree_df["Composante"], y=scree_df["Cumul (%)"], mode="lines+markers", name="Cumul (%)")
    st.plotly_chart(fig_scree, use_container_width=True)
    st.caption(f"Total expliqué par {n_comp} composantes : **{cum.iloc[-1]:.2f}%**")

    # Projection 2D/3D
    st.markdown("### 🎯 Projection")
    proj_mode = st.radio("Espace de projection", ["2D", "3D"], horizontal=True)
    color_by = st.selectbox("Couleur par", options=["Aucune"] + df.columns.tolist(), index=0)

    proj_df = scores.copy()
    proj_df.index.name = "index"
    if color_by != "Aucune":
        proj_df[color_by] = df.loc[proj_df.index, color_by]

    if proj_mode == "2D":
        fig_proj = px.scatter(
            proj_df, x="PC1", y="PC2",
            color=None if color_by == "Aucune" else color_by,
            hover_data=[proj_df.index],
            title="Projection PCA (PC1 vs PC2)"
        )
    else:
        if "PC3" not in proj_df.columns:
            st.info("ℹ️ Au moins 3 composantes nécessaires pour la projection 3D.")
            fig_proj = None
        else:
            fig_proj = px.scatter_3d(
                proj_df, x="PC1", y="PC2", z="PC3",
                color=None if color_by == "Aucune" else color_by,
                hover_data=[proj_df.index],
                title="Projection PCA (PC1 vs PC2 vs PC3)"
            )
    if fig_proj is not None:
        st.plotly_chart(fig_proj, use_container_width=True)

    # (Mini) biplot : charges des variables sur PC1/PC2
    with st.expander("📎 Biplot (charges variables sur PC1/PC2)", expanded=False):
        if n_comp >= 2:
            loadings = pd.DataFrame(
                pca.components_[:2, :].T,
                index=cols_selected,
                columns=["PC1", "PC2"],
            )
            fig_load = px.scatter(loadings, x="PC1", y="PC2", text=loadings.index, title="Charges (PC1/PC2)")
            fig_load.update_traces(textposition="top center")
            st.plotly_chart(fig_load, use_container_width=True)
            st.caption("Les charges indiquent la contribution directionnelle des variables aux composantes.")
        else:
            st.info("ℹ️ Biplot indisponible avec moins de 2 composantes.")

    # Sauvegarde éventuelle des scores dans le DF actif
    if st.checkbox("➕ Ajouter les scores PCA au DataFrame actif", value=False):
        for c in scores.columns:
            df.loc[scores.index, c] = scores[c]
        st.session_state["df"] = df
        save_snapshot(df, suffix=f"pca_{n_comp}c")
        log_action("pca_add_scores", f"{n_comp} composantes ajoutées")
        st.success("✅ Scores PCA ajoutés au DataFrame actif.")

    st.divider()

    # ============================== K-MEANS ====================================
    st.markdown("## 🧭 K-means — Regroupements")

    use_space = st.radio(
        "Espace de clustering",
        ["Données standardisées", "Scores PCA"],
        horizontal=True,
        help="Le clustering sur les scores PCA peut réduire le bruit et accélérer."
    )
    k = st.slider("Nombre de clusters (k)", min_value=2, max_value=10, value=3)

    # Espace choisi
    if use_space == "Données standardisées":
        X_cluster = X_std
        space_label = "std"
    else:
        X_cluster = scores  # n_comp colonnes
        space_label = f"pca{n_comp}"

    # Ajustement K-means
    if st.button("🚀 Lancer le clustering K-means"):
        try:
            km, labels, sil = _fit_kmeans(X_cluster, k=k)
            st.success(f"✅ Clustering terminé. Silhouette = {sil:.3f}" if np.isfinite(sil) else "✅ Clustering terminé.")

            # Ajouter les labels au DF actif (alignement sur index de X_cluster)
            label_col = f"cluster_k{k}_{space_label}"
            df.loc[X_cluster.index, label_col] = labels
            st.session_state["df"] = df

            # Visualisation dans l’espace choisi
            if use_space == "Scores PCA":
                vis_df = scores.copy()
            else:
                # Si pas de PCA, on projette rapidement en 2D via PCA pour visualisation
                _, vis_scores, _, _ = _fit_pca(X_std, n_components=min(2, X_std.shape[1]))
                vis_df = vis_scores.copy()

            vis_df[label_col] = pd.Series(labels, index=X_cluster.index)
            fig_clusters = px.scatter(
                vis_df,
                x=vis_df.columns[0], y=vis_df.columns[1],
                color=label_col,
                hover_data=[vis_df.index],
                title=f"Clusters K={k} ({'PCA' if use_space=='Scores PCA' else 'PCA(2) pour visualisation'})"
            )
            st.plotly_chart(fig_clusters, use_container_width=True)

            # Sauvegarde
            save_snapshot(df.loc[X_cluster.index, [label_col]], suffix=label_col)
            log_action("kmeans_fit", f"k={k} on {space_label}, silhouette={sil:.3f}")
        except Exception as e:
            st.error(f"❌ Erreur K-means : {e}")

    st.divider()

    # ---------- Validation étape EDA ----------
    # Choix : on valide une étape dédiée 'multivariate' (si présente dans EDA_STEPS)
    validate_step_button("multivariate", context_prefix="multi_")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
