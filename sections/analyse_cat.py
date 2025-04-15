# sections/analyse_cat.py

import streamlit as st
import pandas as pd
import plotly.express as px

def run_analyse_categorielle(df):

    st.subheader("📊 Analyse des variables catégorielles")

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    st.markdown(f"🔎 **Colonnes catégorielles détectées : `{len(cat_cols)}`**")

    if not cat_cols:
        st.warning("⚠️ Aucune variable catégorielle détectée.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Aperçu global", "📊 Barplots", "📈 Fréquences cumulées", "💡 Suggestions d'encodage"
    ])

    with tab1:
        st.markdown("### 📋 Détail des variables catégorielles")
        summary_cat = pd.DataFrame({
            "Colonne": cat_cols,
            "Nb modalités uniques": [df[col].nunique() for col in cat_cols],
            "Modalité la + fréquente": [df[col].mode()[0] if not df[col].mode().empty else "—" for col in cat_cols],
            "Valeurs manquantes (%)": [f"{df[col].isna().mean() * 100:.1f} %" for col in cat_cols]
        })
        st.dataframe(summary_cat, use_container_width=True)

    with tab2:
        selected_col = st.selectbox("📌 Choisissez une variable", cat_cols, key="cat_bar")
        top_n = st.slider("🔢 Top modalités à afficher", 3, 30, 10)
        top_vals = df[selected_col].value_counts().head(top_n).reset_index()
        top_vals.columns = ["Modalité", "Fréquence"]
        st.plotly_chart(px.bar(top_vals, x="Modalité", y="Fréquence", text="Fréquence"), use_container_width=True)

    with tab3:
        selected_col = st.selectbox("📈 Choisir une variable", cat_cols, key="cat_freq")
        freq_df = df[selected_col].value_counts(normalize=True).reset_index()
        freq_df.columns = ["Modalité", "Fréquence"]
        freq_df["Fréquence cumulée"] = freq_df["Fréquence"].cumsum()
        freq_df["% Fréquence"] = (freq_df["Fréquence"] * 100).round(2).astype(str) + " %"
        freq_df["% Cumulée"] = (freq_df["Fréquence cumulée"] * 100).round(2).astype(str) + " %"
        st.dataframe(freq_df[["Modalité", "% Fréquence", "% Cumulée"]], use_container_width=True)

    with tab4:
        seuil_card = st.slider("🔧 Seuil max pour OneHot encoding", 2, 50, 10)
        suggestions = []
        for col in cat_cols:
            nb_modal = df[col].nunique()
            if nb_modal <= seuil_card:
                enc = "OneHot"
            elif nb_modal == 2:
                enc = "Binaire"
            elif nb_modal > seuil_card:
                enc = "Ordinal / Embedding"
            else:
                enc = "À vérifier"
            suggestions.append((col, nb_modal, enc))
        enc_df = pd.DataFrame(suggestions, columns=["Colonne", "Nb modalités", "Encodage suggéré"])
        st.dataframe(enc_df.sort_values("Nb modalités"), use_container_width=True)
