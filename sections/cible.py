# ============================================================
# Fichier : cible.py
# Objectif : Analyse autour d’une ou deux variables cibles
# Contenu : corrélations avec la cible, regroupements cat→moyennes,
#           boxplots, nuage de points, export optionnel
# Statut   : Module avancé — HORS barre de progression EDA
# ============================================================

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header
from utils.eda_utils import compute_correlation_matrix  # cache & garde-fous


def run_cible():
    # === En-tête visuel ======================================
    show_header_image_safe("bg_night_serenity.png")
    show_icon_header("🎯", "Analyse cible", "Corrélations, regroupements, visualisations autour d’une cible")

    # 🔁 Récupération du fichier actif
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Merci de sélectionner un fichier dans l’onglet Fichiers.")
        return

    # === Préparation des colonnes ============================
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if len(num_cols) == 0:
        st.warning("⚠️ Aucune variable numérique détectée dans le fichier.")
        return

    # === Sélection des variables cibles ======================
    st.markdown("### ⚙️ Cibles à analyser")
    c1, c2 = st.columns(2)
    target_1 = c1.selectbox("🎯 Cible principale (numérique)", num_cols, key="target1")
    target_2 = c2.selectbox("🎯 Cible secondaire (optionnel)", [None] + num_cols, key="target2")

    # === Interface en onglets ================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Corrélations", "📈 Groupes par cible", "📦 Boxplots", "🧮 Nuage de points"
    ])

    # ----------------------------------------------------------------
    # Onglet 1 — Corrélations avec la cible principale
    # ----------------------------------------------------------------
    with tab1:
        st.markdown("### 📊 Corrélations numériques avec la cible principale")

        # Choix de la méthode (une seule à la fois)
        method = st.radio("Méthode", ["pearson", "spearman", "kendall"], horizontal=True, key="cible_corr_method")

        # Matrice + série triée par importance (on retire la cible elle-même)
        corr_mat = compute_correlation_matrix(df[num_cols], method=method)
        if corr_mat.empty or target_1 not in corr_mat.columns:
            st.info("Pas assez de colonnes numériques ou corrélation indisponible.")
        else:
            s = corr_mat[target_1].drop(labels=[target_1]).dropna().sort_values(ascending=False)
            if s.empty:
                st.info("Aucune corrélation exploitable avec la cible pour cette méthode.")
            else:
                st.dataframe(s.rename("corr").to_frame(), use_container_width=True)

                fig_corr = px.bar(
                    s.reset_index().rename(columns={"index": "Variable", target_1: "corr"}),
                    x="Variable", y=target_1 if target_1 in s.index else "corr",
                    title=f"Corrélations avec la cible ({method})"
                )
                st.plotly_chart(fig_corr, use_container_width=True)

            # Heatmap globale (optionnelle)
            if st.checkbox("Afficher la heatmap globale des corrélations"):
                fig_heatmap = px.imshow(
                    corr_mat, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                    title=f"Matrice des corrélations ({method})"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

    # ----------------------------------------------------------------
    # Onglet 2 — Moyennes par groupe catégoriel
    # ----------------------------------------------------------------
    with tab2:
        st.markdown("### 📈 Moyennes par groupe catégoriel")
        if not cat_cols:
            st.info("Aucune variable catégorielle disponible pour les regroupements.")
            group_col = None
        else:
            group_col = st.selectbox("📁 Variable de regroupement", cat_cols, key="groupcol")

            agg_func = st.selectbox("⚙️ Agrégat", ["mean", "median"], index=0, key="aggfunc")
            agg_label = "moyenne" if agg_func == "mean" else "médiane"

            def _agg(series: pd.Series):
                return getattr(series, agg_func)()

            # target_1 par groupe
            st.markdown(f"#### 📈 {agg_label.capitalize()} de `{target_1}` par `{group_col}`")
            by1 = df.groupby(group_col)[target_1].apply(_agg).sort_values(ascending=False).reset_index()
            st.plotly_chart(px.bar(by1, x=group_col, y=target_1, title=f"{agg_label.capitalize()} par groupe"),
                            use_container_width=True)

            # target_2 (si définie) par groupe
            if target_2:
                st.markdown(f"#### 📈 {agg_label.capitalize()} de `{target_2}` par `{group_col}`")
                by2 = df.groupby(group_col)[target_2].apply(_agg).sort_values(ascending=False).reset_index()
                st.plotly_chart(px.bar(by2, x=group_col, y=target_2, title=f"{agg_label.capitalize()} (cible secondaire)"),
                                use_container_width=True)

        # Export des agrégations (si un group_col est défini)
        st.markdown("#### 📤 Export")
        if st.button("Exporter l’agrégat (CSV)"):
            try:
                if cat_cols and group_col:
                    export_cols = [group_col, target_1] + ([target_2] if target_2 else [])
                    # On reconstruit un tableau aligné simple pour l’export
                    out = df.groupby(group_col)[[c for c in [target_1, target_2] if c]].agg(agg_func)
                    out.to_csv(f"{target_1}_by_{group_col}_{agg_func}.csv", encoding="utf-8-sig")
                    st.success("✅ Export réalisé (CSV).")
                else:
                    st.info("Rien à exporter : choisissez une variable de regroupement.")
            except Exception as e:
                st.error(f"❌ Erreur lors de l’export : {e}")

    # ----------------------------------------------------------------
    # Onglet 3 — Boxplots Num ↔ Cat
    # ----------------------------------------------------------------
    with tab3:
        st.markdown("### 📦 Boxplots Numérique ↔ Catégories")
        if not cat_cols:
            st.warning("Pas de variable catégorielle pour créer un boxplot.")
        else:
            cat_col = st.selectbox("📁 Variable catégorielle (X)", cat_cols, key="box_cat")
            num_col = st.selectbox("🔢 Variable numérique (Y)", num_cols, key="box_num")
            st.plotly_chart(px.box(df, x=cat_col, y=num_col, title=f"{num_col} par {cat_col}"),
                            use_container_width=True)

    # ----------------------------------------------------------------
    # Onglet 4 — Nuage de points
    # ----------------------------------------------------------------
    with tab4:
        st.markdown("### 🧮 Nuage de points")
        x = st.selectbox("🧭 Axe X", num_cols, key="xscatter")
        y = st.selectbox("🧭 Axe Y", num_cols, key="yscatter")
        color = st.selectbox("🎨 Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")

        fig_scatter = px.scatter(
            df, x=x, y=y, color=color,
            title=f"Scatter {y} ~ {x}" + (f" (couleur : {color})" if color else "")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Note : pas de barre de progression ni validate_step_button ici (module avancé)
