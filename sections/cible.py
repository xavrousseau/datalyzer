# sections/cible.py

import streamlit as st
import pandas as pd
import plotly.express as px

def run_cible(df):
    st.subheader("🎯 Analyse orientée variable cible")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée.")
        return

    target_1 = st.selectbox("🎯 Variable cible principale", num_cols, key="target1")
    target_2 = st.selectbox("🎯 Variable cible secondaire (optionnel)", [None] + num_cols, key="target2")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Corrélations", "📈 Cible par groupe", "📦 Boxplot", "🧮 Nuage de points"
    ])

    with tab1:
        corr = df[num_cols].corr()[target_1].drop(target_1).sort_values(ascending=False)
        st.dataframe(corr)
        st.plotly_chart(px.bar(corr.reset_index(), x="index", y=target_1), use_container_width=True)

    with tab2:
        if not cat_cols:
            st.info("Aucune variable catégorielle pour groupement.")
        else:
            group_col = st.selectbox("Variable catégorielle", cat_cols, key="groupcol")
            avg_target1 = df.groupby(group_col)[target_1].mean().sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(avg_target1, x=group_col, y=target_1), use_container_width=True)

            if target_2:
                avg_target2 = df.groupby(group_col)[target_2].mean().sort_values(ascending=False).reset_index()
                st.plotly_chart(px.bar(avg_target2, x=group_col, y=target_2), use_container_width=True)

    with tab3:
        if not cat_cols:
            st.warning("Pas de variable catégorielle pour créer un boxplot.")
        else:
            cat_col = st.selectbox("X = variable catégorielle", cat_cols, key="box_cat")
            num_col = st.selectbox("Y = variable numérique", num_cols, key="box_num")
            st.plotly_chart(px.box(df, x=cat_col, y=num_col), use_container_width=True)

    with tab4:
        x = st.selectbox("X", num_cols, key="xscatter")
        y = st.selectbox("Y", num_cols, key="yscatter")
        color = st.selectbox("Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")
        st.plotly_chart(px.scatter(df, x=x, y=y, color=color), use_container_width=True)
