# ============================================================
# Fichier : multivariee.py
# Objectif : ACP, clustering, projection, boxplots, Cramér’s V
# Version enrichie avec validation interactive et fonctionnalités avancées
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from config import EDA_STEPS
from utils.snapshot_utils import save_snapshot
from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.log_utils import log_action
from utils.filters import get_active_dataframe, validate_step_button
from utils.ui_utils import show_header_image, show_icon_header, show_eda_progress


def run_multivariee():
    # En-tête graphique et pédagogique
    show_header_image("bg_sakura_river.png")
    show_icon_header("📊", "Analyse multivariée", "ACP, clustering, boxplots et corrélations catégorielles")
    show_eda_progress(EDA_STEPS, st.session_state.get("validation_steps", {}))

    # 🔁 Fichier actif
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif ou le fichier est vide. Merci de sélectionner un fichier valide dans l’onglet Fichiers.")
        return

    # 📈 Préparation des données numériques
    numeric_cols = df.select_dtypes(include="number").dropna(axis=1).columns.tolist()
    if len(numeric_cols) < 2:
        st.error("❌ Il faut au moins deux variables numériques pour faire une ACP.")
        return

    # 🎯 Nombre de composantes
    n_max = min(len(numeric_cols), 6)  # Correction de la syntaxe
    n_components = st.slider("📉 Nombre de composantes ACP", min_value=2, max_value=n_max, value=2)

    # ⚙️ ACP : réduction de dimensions
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[numeric_cols])
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=[f"PC{i+1}" for i in range(n_components)])

    # 📊 Variance expliquée
    st.markdown("### 🎯 Variance expliquée")
    explained_var = pca.explained_variance_ratio_
    fig_var = px.bar(
        x=[f"PC{i+1}" for i in range(n_components)],
        y=explained_var * 100,
        labels={"x": "Composantes", "y": "% Variance expliquée"},
        title="Variance expliquée par composante"
    )
    st.plotly_chart(fig_var)

    # 🤖 Clustering KMeans (optionnel)
    st.markdown("### 🤖 Clustering KMeans (optionnel)")
    if st.checkbox("Activer le clustering post-ACP"):
        n_clusters = st.slider("Nombre de clusters", min_value=2, max_value=10, value=3)
        model = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        df_pca["Cluster"] = model.fit_predict(X_pca)
        st.success(f"✅ Clustering KMeans effectué avec {n_clusters} clusters.")
        log_action("clustering", f"{n_clusters} clusters sur ACP")

        # Ajouter une évaluation du score de silhouette
        silhouette_avg = silhouette_score(X_pca, df_pca["Cluster"])
        st.info(f"Score de silhouette pour {n_clusters} clusters : {silhouette_avg:.2f}")

        if st.button("💾 Sauvegarder les clusters en snapshot"):
            save_snapshot(df_pca, suffix="acp_clusters")
            st.success("✅ Snapshot ACP + Clusters sauvegardé.")

    # 🌐 Projection 2D
    st.markdown("### 🌐 Projection des composantes principales")
    color_options = [None] + df.select_dtypes(include="object").columns.tolist()
    color_by = st.selectbox("🎨 Colorier par :", options=color_options, index=0)

    # Vérification que les composantes sont présentes avant de tracer
    if "PC1" in df_pca.columns and "PC2" in df_pca.columns:
        fig_proj = px.scatter(
            df_pca,
            x="PC1", y="PC2",
            color=df[color_by] if color_by else df_pca.get("Cluster"),
            title="Projection ACP",
            labels={"PC1": "Composante 1", "PC2": "Composante 2"},
            width=700, height=500
        )
        st.plotly_chart(fig_proj)
    else:
        st.warning("❌ Les composantes principales PC1 et PC2 ne sont pas disponibles pour la projection.")

    # 📦 Boxplots Numérique ↔ Catégories
    st.markdown("### 🧮 Boxplots Numérique ↔ Catégories")
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    if numeric_cols and cat_cols:
        col_num = st.selectbox("🔢 Variable numérique", numeric_cols)
        col_cat = st.selectbox("📁 Variable catégorielle", cat_cols)
        st.plotly_chart(plot_boxplots(df, col_num, col_cat))
    else:
        st.info("❗ Aucune combinaison Num ↔ Catégories disponible.")

    # 📈 Corrélations catégorielles (Cramér’s V)
    st.markdown("### 📈 Corrélations catégorielles (Cramér’s V)")
    if len(cat_cols) >= 2:
        cramers_df = compute_cramers_v_matrix(df[cat_cols])
        st.dataframe(cramers_df.style.background_gradient(cmap="Blues"))
    else:
        st.info("❗ Pas assez de variables catégorielles pour calculer Cramér’s V.")

    # ✅ Validation finale
    st.divider()
    validate_step_button("multivariee")  # Remplacer validate_step par validate_step_button
