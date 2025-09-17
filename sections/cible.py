# ============================================================
# Fichier : sections/cible.py
# Objectif : Analyse autour d’une ou deux variables cibles
# Contenu : corrélations avec la cible, regroupements cat→moyennes,
#           boxplots, nuage de points, export optionnel
# Statut   : Module avancé — HORS barre de progression EDA
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import io
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.filters import get_active_dataframe
from utils.ui_utils import section_header, show_footer
from utils.eda_utils import compute_correlation_matrix


def run_cible() -> None:
    """
    Atelier « Analyse cible » : explore les relations entre une cible numérique
    (obligatoire) et le reste des variables via 4 volets :

      1) Corrélations : colonne numérique cible vs autres numériques
         (méthodes Pearson/Spearman/Kendall).
      2) Groupes par catégorie : agrégats (moyenne/ médiane) d’une ou deux
         cibles selon une variable catégorielle.
      3) Boxplots Num↔Cat : distribution d’une variable numérique par classe.
      4) Nuage de points : relation bivariable (option de coloration catégorielle).

    Remarques :
      - Ce module n’altère pas les données ; il sert à comprendre et prioriser.
      - L’export des agrégats se fait en mémoire via un bouton de téléchargement.
    """
    # ---------- En-tête ----------
    section_header(
        title="Analyse cible",
        subtitle="Corrélations, regroupements, visualisations autour d’une cible",
        section="analyse",
        emoji="🎯",
    )

    # ---------- DataFrame actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Merci de sélectionner un fichier dans l’onglet **Chargement**.")
        return

    # Sélection basique des types (prend en compte dtype 'category' côté cat)
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée dans ce fichier.")
        return

    # ---------- Choix des cibles ----------
    st.markdown("### ⚙️ Variables cibles")
    c1, c2 = st.columns(2)
    target_1 = c1.selectbox("🎯 Cible principale (numérique)", num_cols, key="target1")
    # None comme première option pour expliciter le caractère optionnel
    target_2 = c2.selectbox("🎯 Cible secondaire (optionnelle)", [None] + num_cols, key="target2")

    # ---------- Navigation par onglets ----------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Corrélations", "📈 Groupes par cible", "📦 Boxplots", "🧮 Nuage de points"
    ])

    # ========================================================
    # Onglet 1 — Corrélations avec la cible principale
    # ========================================================
    with tab1:
        st.markdown("### 📊 Corrélations numériques avec la cible principale")
        method = st.radio(
            "Méthode",
            ["pearson", "spearman", "kendall"],
            horizontal=True,
            key="cible_corr_method",
            help=(
                "Pearson : corrélation linéaire (variables quantitatives). "
                "Spearman : corrélation de rang (robuste aux non-linéarités). "
                "Kendall : corrélation de rang, plus conservatrice sur petits n."
            ),
        )

        # Sous-ensemble numérique pour la matrice
        corr_mat = compute_correlation_matrix(df[num_cols], method=method)
        if corr_mat.empty or target_1 not in corr_mat.columns:
            st.info("Pas assez de colonnes numériques ou corrélations indisponibles.")
        else:
            # Série des corrélations vs la cible (hors diagonale)
            s = (
                corr_mat[target_1]
                .drop(labels=[target_1], errors="ignore")
                .dropna()
                .sort_values(ascending=False)
            )
            if s.empty:
                st.info("Aucune corrélation exploitable avec la cible pour cette méthode.")
            else:
                st.dataframe(s.rename("corr").to_frame(), use_container_width=True)

                fig_corr = px.bar(
                    s.reset_index().rename(columns={"index": "Variable", target_1: "corr"}),
                    x="Variable", y="corr",
                    title=f"Corrélations avec la cible ({method})"
                )
                st.plotly_chart(fig_corr, use_container_width=True)

            if st.checkbox("Afficher la heatmap globale des corrélations"):
                fig_heatmap = px.imshow(
                    corr_mat,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1,
                    title=f"Matrice des corrélations ({method})"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)

    # ========================================================
    # Onglet 2 — Moyennes par groupe catégoriel
    # ========================================================
    with tab2:
        st.markdown("### 📈 Moyennes par groupe catégoriel")

        if not cat_cols:
            st.info("Aucune variable catégorielle disponible pour les regroupements.")
            group_col = None
        else:
            group_col = st.selectbox("📁 Variable de regroupement", cat_cols, key="groupcol")
            agg_func = st.selectbox("⚙️ Agrégat", ["mean", "median"], index=0, key="aggfunc")
            agg_label = "moyenne" if agg_func == "mean" else "médiane"

            # Premier agrégat (cible principale)
            st.markdown(f"#### 📈 {agg_label.capitalize()} de `{target_1}` par `{group_col}`")
            by1 = df.groupby(group_col, dropna=False)[target_1].agg(agg_func).sort_values(ascending=False).reset_index()
            st.plotly_chart(
                px.bar(by1, x=group_col, y=target_1, title=f"{agg_label.capitalize()} par groupe"),
                use_container_width=True
            )

            # Cible secondaire si fournie
            if target_2:
                st.markdown(f"#### 📈 {agg_label.capitalize()} de `{target_2}` par `{group_col}`")
                by2 = df.groupby(group_col, dropna=False)[target_2].agg(agg_func).sort_values(ascending=False).reset_index()
                st.plotly_chart(
                    px.bar(by2, x=group_col, y=target_2, title=f"{agg_label.capitalize()} (cible secondaire)"),
                    use_container_width=True
                )

        # Export des agrégats (en mémoire)
        st.markdown("#### 📤 Export")
        if st.button("Exporter l’agrégat (CSV)"):
            try:
                if cat_cols and group_col:
                    cols_to_agg = [target_1] + ([target_2] if target_2 else [])
                    out = df.groupby(group_col, dropna=False)[cols_to_agg].agg(agg_func).reset_index()
                    buf = io.StringIO()
                    out.to_csv(buf, index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="📥 Télécharger le CSV",
                        data=buf.getvalue(),
                        file_name=f"{'_and_'.join([c for c in cols_to_agg])}_by_{group_col}_{agg_func}.csv",
                        mime="text/csv",
                    )
                    st.success("✅ Export prêt au téléchargement.")
                else:
                    st.info("Rien à exporter : choisissez une variable de regroupement.")
            except Exception as e:
                st.error(f"❌ Erreur lors de l’export : {e}")

    # ========================================================
    # Onglet 3 — Boxplots Num ↔ Cat
    # ========================================================
    with tab3:
        st.markdown("### 📦 Boxplots Numérique ↔ Catégories")

        if not cat_cols:
            st.warning("Pas de variable catégorielle pour créer un boxplot.")
        else:
            cat_col = st.selectbox("📁 Variable catégorielle (X)", cat_cols, key="box_cat")
            num_col = st.selectbox("🔢 Variable numérique (Y)", num_cols, key="box_num")
            st.plotly_chart(
                px.box(df, x=cat_col, y=num_col, title=f"{num_col} par {cat_col}"),
                use_container_width=True
            )

    # ========================================================
    # Onglet 4 — Nuage de points
    # ========================================================
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

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
