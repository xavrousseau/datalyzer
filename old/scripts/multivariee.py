# ============================================================
# Fichier : multivariee.py
# Objectif : ACP + Clustering + Visualisations + Cramér’s V
# pour Datalyzer (version Streamlit complète et harmonisée)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from utils.snapshot_utils import save_snapshot
from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.log_utils import log_action
from utils.filters import validate_step_button
from utils.ui_utils import show_header_image

def run_multivariee():
    # Image de fond
    show_header_image("bg_sakura_river.png")

    # Titre et description
    st.title("📊 Analyse multivariée (ACP + Clustering)")
    st.markdown("Réduction de dimension, clustering automatique, corrélations catégorielles.")
    st.divider()

    # Données disponibles ?
    if "df" not in st.session_state:
        st.warning("📂 Veuillez charger un fichier avant d’accéder à l’analyse multivariée.")
        st.stop()

    df = st.session_state.df

    # Sélection des colonnes numériques
    numeric_cols = df.select_dtypes(include="number").dropna(axis=1).columns.tolist()
    if len(numeric_cols) < 2:
        st.error("❌ Il faut au moins 2 colonnes numériques pour lancer une ACP.")
        st.stop()

    n_max = min(len(numeric_cols), 6)
    n_components = st.slider("📉 Nombre de composantes ACP", min_value=2, max_value=n_max, value=2)

    # PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[numeric_cols])
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=[f"PC{i+1}" for i in range(n_components)])

    # Variance expliquée
    st.markdown("### 🎯 Variance expliquée")
    explained_var = pca.explained_variance_ratio_
    for i, var in enumerate(explained_var):
        st.write(f"**PC{i+1}** : {var*100:.2f}%")
    fig_var = px.bar(x=[f"PC{i+1}" for i in range(n_components)], y=explained_var*100,
                     labels={'x': 'Composantes', 'y': '% variance expliquée'},
                     title="Variance expliquée par composante")
    st.plotly_chart(fig_var)

    st.divider()

    # Clustering (optionnel)
    st.markdown("### 🤖 Clustering KMeans (optionnel)")
    if st.checkbox("Activer le clustering post-ACP"):
        n_clusters = st.slider("Nombre de clusters", min_value=2, max_value=10, value=3)
        model = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        df_pca["Cluster"] = model.fit_predict(X_pca)
        st.success(f"✅ Clustering KMeans effectué avec {n_clusters} clusters.")
        log_action("clustering", f"{n_clusters} clusters générés")

        if st.button("💾 Sauvegarder le clustering en snapshot"):
            save_snapshot(df_pca, suffix="acp_clusters")
            st.success("Snapshot 'acp_clusters' sauvegardé avec succès.")

    st.divider()

    # Projection visuelle
    st.markdown("### 🌐 Projection des composantes principales")
    color_options = [None] + df.select_dtypes(include="object").columns.tolist()
    color_by = st.selectbox("Colorier par :", options=color_options, index=0)

    fig_proj = px.scatter(
        df_pca,
        x="PC1", y="PC2",
        color=df[color_by] if color_by else df_pca.get("Cluster", None),
        title="Projection ACP",
        labels={"PC1": "Composante 1", "PC2": "Composante 2"},
        width=700, height=500
    )
    st.plotly_chart(fig_proj)

    st.divider()

    # Boxplots Num ↔ Cat
    st.markdown("### 🧮 Boxplots Num ↔ Catégories")
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    if numeric_cols and cat_cols:
        col_num = st.selectbox("Variable numérique", numeric_cols)
        col_cat = st.selectbox("Variable catégorielle", cat_cols)
        st.plotly_chart(plot_boxplots(df, col_num, col_cat))
    else:
        st.info("Aucune combinaison Num ↔ Catégories disponible.")

    st.divider()

    # Matrice de Cramér’s V
    st.markdown("### 📈 Corrélations catégorielles (Cramér’s V)")
    if len(cat_cols) >= 2:
        cramers_df = compute_cramers_v_matrix(df[cat_cols])
        st.dataframe(cramers_df.style.background_gradient(cmap="Blues"))
    else:
        st.info("Pas assez de variables catégorielles pour calculer Cramér’s V.")

    st.divider()

    # Validation de l’étape
    validate_step_button(df, step_name="multivariee")
