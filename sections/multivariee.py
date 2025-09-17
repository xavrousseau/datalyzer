# ============================================================
# Fichier : multivariee.py
# Objectif : ACP, clustering, projection, boxplots, Cramér’s V
# Statut : Module avancé (hors barre de progression EDA)
# Points forts :
#   - Imputation douce (moyenne) + standardisation
#   - Index conservé pour recoller aux données d’origine
#   - Couleur : Cluster OU une colonne catégorielle (optionnelle)
#   - Garde-fous NaN / dimensions / perf (downsample pour le scatter)
# ============================================================

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from utils.snapshot_utils import save_snapshot
from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header

# ------------------------------ Helpers ------------------------------

def _safe_numeric_matrix(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Convertit -> numeric, puis impute par la moyenne (imputation douce)."""
    X = df[cols].apply(pd.to_numeric, errors="coerce")
    # si une colonne est full-NaN, on la droppe (KMeans/PCA ne tolèrent pas ça)
    full_nan = [c for c in X.columns if X[c].isna().all()]
    if full_nan:
        X = X.drop(columns=full_nan)
    # imputation moyenne
    X = X.fillna(X.mean(numeric_only=True))
    return X

def _downsample(df: pd.DataFrame, n: int = 10000) -> pd.DataFrame:
    """Évite d’envoyer trop de points au scatter (perf UI)."""
    if len(df) <= n:
        return df
    return df.sample(n, random_state=42)

# ------------------------------ Page ------------------------------

def run_multivariee():
    # En-tête graphique et pédagogique
    show_header_image_safe("bg_sakura_river.png")
    show_icon_header("📊", "Analyse multivariée", "ACP, clustering, boxplots et corrélations catégorielles")

    # 🔁 Fichier actif
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif ou fichier vide. Sélectionnez un fichier dans l’onglet Fichiers.")
        return

    # 📈 Préparation des colonnes
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        st.error("❌ Il faut au moins deux variables numériques pour faire une ACP.")
        return

    # Paramètres de l’analyse
    st.markdown("### ⚙️ Paramètres ACP")
    c1, c2 = st.columns(2)
    n_max = min(len(numeric_cols), 6)
    n_components = c1.slider("📉 Nombre de composantes", min_value=2, max_value=n_max, value=2, step=1)
    do_clustering = c2.checkbox("🤖 Activer le clustering post-ACP")

    # Matrice numérique (imputation + standardisation)
    X = _safe_numeric_matrix(df, numeric_cols)
    if X.shape[1] < 2:
        st.error("❌ Après nettoyage (NaN / colonnes vides), il reste < 2 colonnes numériques.")
        return

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ⚙️ ACP
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    # DataFrame ACP : conserver l’index d’origine pour aligner avec df
    df_pca = pd.DataFrame(X_pca, index=df.index, columns=[f"PC{i+1}" for i in range(n_components)])

    # 📊 Variance expliquée
    st.markdown("### 🎯 Variance expliquée")
    explained_var = pca.explained_variance_ratio_
    var_df = pd.DataFrame({
        "Composante": [f"PC{i+1}" for i in range(n_components)],
        "Variance (%)": explained_var * 100,
        "Variance cumulée (%)": np.cumsum(explained_var) * 100
    })
    fig_var = px.bar(
        var_df, x="Composante", y="Variance (%)",
        title="Variance expliquée par composante",
        text_auto=".1f"
    )
    st.plotly_chart(fig_var, use_container_width=True)
    st.caption(f"Variance cumulée (PC1→PC{n_components}) : **{var_df['Variance cumulée (%)'].iloc[-1]:.1f}%**")

    # 🤖 Clustering KMeans (optionnel)
    if do_clustering:
        st.markdown("### 🤖 Clustering KMeans (post-ACP)")
        n_clusters = st.slider("Nombre de clusters", min_value=2, max_value=10, value=3, step=1)
        km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = km.fit_predict(X_pca)
        df_pca["Cluster"] = pd.Series(labels, index=df_pca.index, dtype="int64")
        st.success(f"✅ Clustering KMeans effectué ({n_clusters} clusters).")
        log_action("clustering", f"{n_clusters} clusters sur ACP ({n_components} PCs)")

        # Silhouette (défini pour n_clusters >= 2)
        try:
            sil = silhouette_score(X_pca, labels)
            st.info(f"Score de silhouette : **{sil:.3f}**")
        except Exception as e:
            st.warning(f"Silhouette non calculable : {e}")

        if st.button("💾 Sauvegarder ACP + Clusters"):
            save_snapshot(df_pca, suffix="acp_clusters")
            st.success("✅ Snapshot ACP + Clusters sauvegardé.")

    # 🌐 Projection 2D (PC1 vs PC2)
    st.markdown("### 🌐 Projection des composantes principales (PC1 vs PC2)")
    if n_components < 2:
        st.info("Ajoutez une deuxième composante pour projeter en 2D.")
    else:
        # Options de couleur : aucun, Cluster (si dispo), ou une variable catégorielle de df
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        color_opts = ["(Aucune)"]
        if "Cluster" in df_pca.columns:
            color_opts.append("Cluster")
        color_opts += cat_cols

        color_choice = st.selectbox("🎨 Colorier par :", options=color_opts, index=0)

        plot_df = df_pca[["PC1", "PC2"]].copy()
        color_series = None
        if color_choice == "Cluster":
            color_series = df_pca["Cluster"]
        elif color_choice != "(Aucune)" and color_choice in df.columns:
            # on aligne par index pour éviter tout décalage
            color_series = df[color_choice].reindex(plot_df.index)

        plot_df = _downsample(plot_df.join(color_series, how="left") if color_series is not None else plot_df, n=10000)

        fig_proj = px.scatter(
            plot_df,
            x="PC1", y="PC2",
            color=color_series.name if color_series is not None else None,
            title="Projection ACP (PC1 vs PC2)",
            labels={"PC1": "Composante 1", "PC2": "Composante 2"}
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    # 📦 Boxplots Numérique ↔ Catégories
    st.markdown("### 🧮 Boxplots Numérique ↔ Catégories")
    cat_cols_all = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if len(numeric_cols) and len(cat_cols_all):
        col_num = st.selectbox("🔢 Variable numérique", numeric_cols, key="mv_box_num")
        col_cat = st.selectbox("📁 Variable catégorielle", cat_cols_all, key="mv_box_cat")
        st.plotly_chart(plot_boxplots(df, col_num, col_cat), use_container_width=True)
    else:
        st.info("❗ Aucune combinaison Num ↔ Catégories disponible.")

    # 📈 Corrélations catégorielles (Cramér’s V)
    st.markdown("### 📈 Corrélations catégorielles (Cramér’s V)")
    if len(cat_cols_all) >= 2:
        cramers_df = compute_cramers_v_matrix(df[cat_cols_all])
        st.dataframe(cramers_df.style.background_gradient(cmap="Blues"), use_container_width=True)
    else:
        st.info("❗ Pas assez de variables catégorielles pour calculer Cramér’s V.")

    # 📤 Export ACP seule (sans clusters)
    with st.expander("📤 Exporter les scores ACP (PCs)"):
        if st.button("💾 Snapshot des composantes (PCs)"):
            save_snapshot(df_pca.drop(columns=["Cluster"], errors="ignore"), suffix="acp_scores")
            st.success("✅ Snapshot des composantes sauvegardé.")
 
