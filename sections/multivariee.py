# sections/multivariee.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import chi2_contingency


def cramers_v(x, y):
    confusion_matrix = pd.crosstab(x, y)
    chi2 = chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum().sum()
    phi2 = chi2 / n
    r, k = confusion_matrix.shape
    phi2corr = max(0, phi2 - ((k - 1)*(r - 1)) / (n - 1))
    rcorr = r - ((r - 1)**2) / (n - 1)
    kcorr = k - ((k - 1)**2) / (n - 1)
    return np.sqrt(phi2corr / min((kcorr - 1), (rcorr - 1)))


def run_multivariee(df):
    st.subheader("🧪 Analyse multivariée et interactions")
    st.markdown(f"🔎 **Fichier sélectionné : `{df.shape[0]} lignes × {df.shape[1]} colonnes`**")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    tab1, tab2, tab3 = st.tabs([
        "📉 ACP (PCA)",
        "📊 Interactions num ↔ cat",
        "📚 Corrélation catégorielle"
    ])

    # ------------------------ ACP ------------------------
    with tab1:
        st.markdown("### 📉 Analyse en Composantes Principales (ACP / PCA)")
        st.info("Réduction des dimensions tout en conservant un maximum d'information.")

        if len(num_cols) < 2:
            st.warning("⚠️ Pas assez de variables numériques pour l'ACP.")
        else:
            df_pca = df[num_cols].dropna()
            if df_pca.empty:
                st.error("❌ Pas assez de lignes complètes pour effectuer une ACP. Veuillez nettoyer ou imputer les données.")
            else:
                df_scaled = StandardScaler().fit_transform(df_pca)

                n_comp = st.slider("Nombre de composantes", 2, min(10, len(num_cols)), 2)
                pca = PCA(n_components=n_comp)
                components = pca.fit_transform(df_scaled)

                pca_df = pd.DataFrame(components, columns=[f"PC{i+1}" for i in range(n_comp)], index=df_pca.index)

                color_cat = st.selectbox("Colorer par (optionnel)", [None] + cat_cols)
                if color_cat:
                    pca_df[color_cat] = df.loc[pca_df.index, color_cat]

                st.markdown("#### 🌈 Projection des données (PC1 vs PC2)")
                fig = px.scatter(pca_df, x="PC1", y="PC2", color=color_cat if color_cat else None)
                st.plotly_chart(fig, use_container_width=True)

                explained = pd.DataFrame({
                    "Composante": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
                    "Variance expliquée (%)": (pca.explained_variance_ratio_ * 100).round(2)
                })
                st.markdown("#### 📈 Variance expliquée")
                st.dataframe(explained)

    # ------------------ Num ↔ Cat interactions ------------------
    with tab2:
        st.markdown("### 📊 Analyse croisée numérique / catégorielle")
        if not cat_cols or not num_cols:
            st.warning("⚠️ Il faut au moins une variable catégorielle et une numérique.")
        else:
            cat_var = st.selectbox("Variable catégorielle", cat_cols, key="group_cat")
            num_var = st.selectbox("Variable numérique", num_cols, key="group_num")
            st.plotly_chart(px.box(df, x=cat_var, y=num_var), use_container_width=True)

    # ----------------- Corrélations catégorielles -----------------
    with tab3:
        st.markdown("### 📚 Corrélations entre variables catégorielles (Cramér's V)")
        st.info("Mesure la force d'association entre deux variables catégorielles.")

        if len(cat_cols) < 2:
            st.warning("⚠️ Pas assez de colonnes catégorielles.")
        else:
            matrix = pd.DataFrame(index=cat_cols, columns=cat_cols)
            for col1 in cat_cols:
                for col2 in cat_cols:
                    if col1 == col2:
                        matrix.loc[col1, col2] = 1.0
                    else:
                        matrix.loc[col1, col2] = cramers_v(df[col1], df[col2])
            matrix = matrix.astype(float)

            st.markdown("#### 🔥 Matrice de Cramér's V")
            fig = px.imshow(matrix, text_auto=".2f", aspect="auto", color_continuous_scale="OrRd")
            st.plotly_chart(fig, use_container_width=True)
