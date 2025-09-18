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
 
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe 
from utils.ui_utils import section_header, show_footer



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


def _fit_kmeans(
    X: pd.DataFrame,
    k: int,
    n_init: int = 10,           # ← compat versions < 1.4 (au lieu de "auto")
    random_state: int = 42,
) -> tuple[KMeans, np.ndarray, float]:
    """
    Ajuste un K-means et retourne :
      - modèle KMeans
      - labels (np.ndarray)
      - silhouette (float) si calculable, sinon NaN
    """
    km = KMeans(n_clusters=k, n_init=n_init, random_state=random_state)
    labels = km.fit_predict(X.values)

    sil = float("nan")
    try:
        # silhouette dispo si au moins 2 clusters non vides et ≥ 2 observations
        if len(set(labels)) > 1 and X.shape[0] >= 2:
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
    # ---------- En-tête ----------
    section_header(
        title="Multivariée",
        subtitle="PCA pour réduire la dimension et K-means pour regrouper les observations.",
        section="multivariee",  # ← bannières : SECTION_BANNERS["multivariee"]
        emoji="",
    )

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

    # Prétraitement : imputation douce (par défaut) ou dropna listwise
    X_raw = df[cols_selected].copy()
    do_impute = st.checkbox(
        "Imputer les valeurs manquantes (moyenne)",
        value=True,
        help="Évite de perdre toutes les lignes si des NA sont présents."
    )

    if do_impute:
        X = X_raw.apply(pd.to_numeric, errors="coerce")

        # Colonnes 100% NA après coercition -> on les retire
        all_nan_cols = X.columns[X.isna().all()]
        if len(all_nan_cols):
            st.caption("⚠️ Colonnes 100% NA après coercition supprimées : " + ", ".join(map(str, all_nan_cols)))
            X = X.drop(columns=all_nan_cols, errors="ignore")

        # Imputation moyenne (numérique uniquement)
        X = X.fillna(X.mean(numeric_only=True))
        dropped = 0
    else:
        X = X_raw.dropna(axis=0, how="any")
        dropped = len(X_raw) - len(X)
        if dropped:
            st.caption(f"ℹ️ {dropped} ligne(s) supprimée(s) pour valeurs manquantes sur les variables retenues.")

    # Variables retirées par la préparation (ex. 100% NA)
    removed_vars = [c for c in cols_selected if c not in X.columns]
    if removed_vars:
        st.caption("⚠️ Variables retirées pendant la préparation : " + ", ".join(map(str, removed_vars)))

    # (Optionnel) Alerte sur les colonnes à variance nulle (peu utiles en PCA)
    zero_var_cols = X.std(numeric_only=True) == 0
    zero_var_cols = [c for c, z in zero_var_cols.items() if z]
    if zero_var_cols:
        st.caption("ℹ️ Colonnes à variance nulle (faible apport en PCA) : " + ", ".join(map(str, zero_var_cols)))

    # Garde-fous
    if X.shape[0] == 0 or X.shape[1] == 0:
        st.error("❌ Aucune donnée exploitable après préparation. Activez l’imputation ou réduisez la sélection.")
        return

    # ============================== PCA =======================================
    st.markdown("## 📉 PCA — Réduction de dimension")

    col_std1, col_std2 = st.columns(2)
    with col_std1:
        do_standardize = st.checkbox("Standardiser (Z-score)", value=True, help="Recommandé si les échelles diffèrent.")
    with col_std2:
        # n_components <= min(n_samples, n_features)
        max_pcs = int(max(1, min(10, X.shape[0], X.shape[1])))
        n_comp = st.slider(
            "Nombre de composantes",
            min_value=1 if max_pcs == 1 else 2,
            max_value=max_pcs,
            value=min(2, max_pcs),
        )

    # Standardisation robuste
    try:
        X_std, scaler = _standardize(X) if do_standardize else (X.copy(), None)
    except ValueError as e:
        st.error(f"Standardisation impossible : {e}")
        return

    # PCA
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

    fig_proj = None
    if proj_mode == "2D":
        if proj_df.shape[1] >= 2:
            fig_proj = px.scatter(
                proj_df, x="PC1", y="PC2",
                color=None if color_by == "Aucune" else color_by,
                hover_data=[proj_df.index],
                title="Projection PCA (PC1 vs PC2)"
            )
        else:
            st.info("ℹ️ Au moins 2 composantes nécessaires pour la 2D.")
    else:  # 3D
        if {"PC1","PC2","PC3"}.issubset(proj_df.columns):
            fig_proj = px.scatter_3d(
                proj_df, x="PC1", y="PC2", z="PC3",
                color=None if color_by == "Aucune" else color_by,
                hover_data=[proj_df.index],
                title="Projection PCA (PC1 vs PC2 vs PC3)"
            )
        else:
            st.info("ℹ️ Au moins 3 composantes nécessaires pour la 3D.")

    if fig_proj is not None:
        st.plotly_chart(fig_proj, use_container_width=True)

    # (Mini) biplot : charges des variables sur PC1/PC2
    with st.expander("📎 Biplot (charges variables sur PC1/PC2)", expanded=False):
        if n_comp >= 2:
            # ⚠️ Utiliser les colonnes réellement passées à la PCA (après nettoyage)
            feature_names = list(X_std.columns)  # pas cols_selected !
            comps = pca.components_[:2, :]       # shape = (2, n_features)

            # Garde-fou (au cas où) : s'assurer que le nb de features colle
            if comps.shape[1] != len(feature_names):
                min_feats = min(comps.shape[1], len(feature_names))
                comps = comps[:, :min_feats]
                feature_names = feature_names[:min_feats]

            loadings = pd.DataFrame(comps.T, index=feature_names, columns=["PC1", "PC2"])

            fig_load = px.scatter(
                loadings, x="PC1", y="PC2",
                text=loadings.index,
                title="Charges (PC1/PC2)"
            )
            fig_load.update_traces(textposition="top center")
            st.plotly_chart(fig_load, use_container_width=True)
            st.caption("Les charges indiquent la contribution directionnelle des variables aux composantes.")
        else:
            st.info("ℹ️ Biplot indisponible avec moins de 2 composantes.")


    # ============================== K-MEANS ====================================
    # ✅ Section K-means (UI) robuste + typage Int64 des labels
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
        # Garde-fous avant fit
        if X_cluster is None or X_cluster.shape[0] == 0:
            st.error("❌ Aucune observation disponible pour le clustering.")
        elif X_cluster.shape[0] < k:
            st.error(f"❌ {X_cluster.shape[0]} observation(s) seulement, inférieur à k={k}. Réduisez k.")
        else:
            try:
                km, labels, sil = _fit_kmeans(X_cluster, k=k)
                st.success(f"✅ Clustering terminé. Silhouette = {sil:.3f}" if np.isfinite(sil) else "✅ Clustering terminé.")

                # Ajouter les labels au DF actif (index aligné) avec dtype nullable
                label_col = f"cluster_k{k}_{space_label}"
                df.loc[X_cluster.index, label_col] = pd.Series(labels, index=X_cluster.index, dtype="Int64")
                st.session_state["df"] = df

                # Visualisation : 2D si possible
                if use_space == "Scores PCA":
                    vis_df = scores.copy()
                    can_plot = vis_df.shape[1] >= 2
                else:
                    # Si pas de PCA affichable, crée une 2D de visu via PCA(2) si ≥2 features
                    if X_std.shape[1] >= 2:
                        _, vis_scores, _, _ = _fit_pca(X_std, n_components=2)
                        vis_df = vis_scores.copy()
                        can_plot = True
                    else:
                        can_plot = False

                if can_plot:
                    vis_df[label_col] = pd.Series(labels, index=X_cluster.index)
                    fig_clusters = px.scatter(
                        vis_df,
                        x=vis_df.columns[0], y=vis_df.columns[1],
                        color=label_col,
                        hover_data=[vis_df.index],
                        title=f"Clusters K={k} ({'PCA' if use_space=='Scores PCA' else 'PCA(2) pour visualisation'})"
                    )
                    st.plotly_chart(fig_clusters, use_container_width=True)
                else:
                    st.info("Visualisation 2D indisponible (moins de deux dimensions).")

                # Sauvegarde (snapshot des labels uniquement)
                save_snapshot(df.loc[X_cluster.index, [label_col]], suffix=label_col)
                log_action("kmeans_fit", f"k={k} on {space_label}, silhouette={sil:.3f}")
            except Exception as e:
                st.error(f"❌ Erreur K-means : {e}")


    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
