# ============================================================
# Fichier : sections/cible.py
# Objectif : Analyse autour d’une ou deux variables cibles
# Contenu : corrélations avec la cible, regroupements cat→moyennes,
#           boxplots, nuage de points, export optionnel
# Statut   : Module avancé — HORS barre de progression EDA
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

from utils.filters import get_active_dataframe 
from utils.ui_utils import section_header, show_footer
from utils.eda_utils import compute_correlation_matrix
from utils.sql_bridge import expose_to_sql_lab

# ---------------------------- Helpers ----------------------------

def _dedup_columns(cols: list[str]) -> list[str]:
    """Rend les noms de colonnes uniques en suffixant .1, .2, … aux doublons."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for c in cols:
        if c in seen:
            seen[c] += 1
            out.append(f"{c}.{seen[c]}")
        else:
            seen[c] = 0
            out.append(c)
    return out


# ---------------------------- Vue principale ----------------------------

def run_cible() -> None:
    """
    Atelier « Analyse cible » : explore les relations entre une cible numérique
    (obligatoire) et le reste des variables via 4 volets :

      1) Corrélations : cible vs autres numériques (Pearson/Spearman/Kendall).
      2) Groupes par catégorie : agrégats (moyenne/médiane) d’1–2 cibles par classe.
      3) Boxplots Num↔Cat : distribution d’une variable numérique par catégorie.
      4) Nuage de points : relation bivariable (coloration catégorielle optionnelle).

    Remarques :
      - Le module n’altère pas les données ; export des agrégats via bouton.
      - Robustesse aux colonnes dupliquées (DF de travail dédoublonné).
    """
    # ---------- En-tête ----------
    section_header(
        title="Analyse cible",
        subtitle="Corrélations, regroupements, visualisations autour d’une cible",
        section="cible",   # bannière dédiée si définie dans config.SECTION_BANNERS
        emoji="",
    )

    # ---------- DataFrame actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Merci de sélectionner un fichier dans l’onglet **Chargement**.")
        return

    # DF de travail avec colonnes uniques (évite DuplicateError de Narwhals/Plotly)
    dfw = df.copy()
    if not dfw.columns.is_unique:
        dfw.columns = _dedup_columns(list(dfw.columns))
        st.caption(
            "ℹ️ Colonnes dupliquées détectées : elles ont été renommées **temporairement** "
            "pour l’analyse (suffixes `.1`, `.2`, …). Les données originales ne sont pas modifiées."
        )

    # Sélection des types (prend en compte dtype 'category' côté cat)
    num_cols = dfw.select_dtypes(include="number").columns.tolist()
    cat_cols = dfw.select_dtypes(include=["object", "category", "string"]).columns.tolist()

    if not num_cols:
        st.warning("⚠️ Aucune variable numérique détectée dans ce fichier.")
        return

    # ---------- Choix des cibles ----------
    st.markdown("### ⚙️ Variables cibles")
    c1, c2 = st.columns(2)
    target_1 = c1.selectbox("🎯 Cible principale (numérique)", num_cols, key="target1")
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

        if len(num_cols) < 2:
            st.info("Pas assez de variables numériques pour calculer des corrélations.")
        else:
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

            # Matrice sur le sous-ensemble numérique du DF de travail
            corr_mat = compute_correlation_matrix(dfw[num_cols], method=method)

            if corr_mat.empty or target_1 not in corr_mat.columns:
                st.info("Pas assez de colonnes numériques ou corrélations indisponibles.")
            else:
                s = corr_mat[target_1].drop(labels=[target_1], errors="ignore").dropna()
                if s.empty:
                    st.info("Aucune corrélation exploitable avec la cible pour cette méthode.")
                else:
                    # Tri par valeur absolue (importance)
                    s_ordered = s.reindex(s.abs().sort_values(ascending=False).index)
                    st.dataframe(s_ordered.rename("corr").to_frame(), use_container_width=True)

                    fig_corr = px.bar(
                        s_ordered.reset_index().rename(columns={"index": "Variable", target_1: "corr"}),
                        x="Variable", y="corr",
                        title=f"Corrélations avec la cible ({method})"
                    )
                    fig_corr.update_xaxes(categoryorder="array", categoryarray=s_ordered.index.tolist())
                    st.plotly_chart(fig_corr, use_container_width=True)

                # Heatmap globale : on passe par les valeurs NumPy pour ignorer les noms dupliqués
                if st.checkbox("Afficher la heatmap globale des corrélations"):
                    fig_heatmap = px.imshow(
                        corr_mat.values,
                        x=[str(c) for c in corr_mat.columns],
                        y=[str(i) for i in corr_mat.index],
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

            # --- cible principale ---
            if dfw[target_1].dropna().empty:
                st.info(f"Pas de valeurs numériques disponibles pour `{target_1}`.")
            else:
                st.markdown(f"#### 📈 {agg_label.capitalize()} de `{target_1}` par `{group_col}`")
                by1 = (
                    dfw.groupby(group_col, dropna=False)[target_1]
                       .agg(agg_func)
                       .reset_index()
                )
                order1 = (
                    by1.sort_values(target_1, ascending=False, na_position="last")[group_col]
                       .astype(str)
                       .tolist()
                )
                fig1 = px.bar(by1, x=group_col, y=target_1, title=f"{agg_label.capitalize()} par groupe")
                fig1.update_xaxes(categoryorder="array", categoryarray=order1)
                st.plotly_chart(fig1, use_container_width=True)

            # --- cible secondaire optionnelle ---
            if target_2:
                if dfw[target_2].dropna().empty:
                    st.info(f"Pas de valeurs numériques disponibles pour `{target_2}`.")
                else:
                    st.markdown(f"#### 📈 {agg_label.capitalize()} de `{target_2}` par `{group_col}`")
                    by2 = (
                        dfw.groupby(group_col, dropna=False)[target_2]
                           .agg(agg_func)
                           .reset_index()
                    )
                    order2 = (
                        by2.sort_values(target_2, ascending=False, na_position="last")[group_col]
                           .astype(str)
                           .tolist()
                    )
                    fig2 = px.bar(by2, x=group_col, y=target_2, title=f"{agg_label.capitalize()} (cible secondaire)")
                    fig2.update_xaxes(categoryorder="array", categoryarray=order2)
                    st.plotly_chart(fig2, use_container_width=True)

        # Export / Publication des agrégats
        st.markdown("#### 📤 Export / Publication")
        if cat_cols and group_col:
            cols_to_agg = [target_1] + ([target_2] if target_2 else [])
            try:
                out = (
                    dfw.groupby(group_col, dropna=False)[cols_to_agg]
                    .agg(agg_func)
                    .reset_index()
                )
            except Exception as e:
                out = None
                st.error(f"❌ Erreur lors du calcul de l'agrégat : {e}")

            col_export, col_sql = st.columns(2)
            with col_export:
                if out is not None and st.button("📥 Télécharger le CSV"):
                    csv_bytes = out.to_csv(index=False).encode("utf-8-sig")  # BOM pour Excel
                    st.download_button(
                        label="⬇️ Export CSV (agrégat)",
                        data=csv_bytes,
                        file_name=f"{'_and_'.join(cols_to_agg)}_by_{group_col}_{agg_func}.csv",
                        mime="text/csv",
                    )
                    st.success("✅ Export prêt au téléchargement.")

            with col_sql:
                if out is not None and st.button("🧩 Publier l’agrégat au SQL Lab"):
                    # Nom explicite : <fichier>__agg_<agg>_<cibles>_by_<groupe>
                    targets_tag = "_and_".join(cols_to_agg)
                    table_sql = expose_to_sql_lab(f"{nom}__agg_{agg_func}_{targets_tag}_by_{group_col}", out)
                    st.success(f"✅ Table SQL exposée : `{table_sql}`.")

        else:
            st.info("Rien à exporter/publier : choisissez une variable de regroupement.")

    # ========================================================
    # Onglet 3 — Boxplots Num ↔ Cat
    # ========================================================
    with tab3:
        st.markdown("### 📦 Boxplots Numérique ↔ Catégories")

        if not cat_cols or not num_cols:
            st.warning("Pas assez de variables (catégorielles et/ou numériques) pour un boxplot.")
        else:
            # Limiter les catégories trop nombreuses pour garder un graph lisible
            cat_options = [c for c in cat_cols if dfw[c].nunique(dropna=False) <= 50] or cat_cols
            cat_col = st.selectbox("📁 Variable catégorielle (X)", cat_options, key="box_cat")
            num_col = st.selectbox("🔢 Variable numérique (Y)", num_cols, key="box_num")

            # DF minimal aux noms sûrs pour éviter les collisions
            data_box = pd.DataFrame({"CAT": dfw[cat_col], "NUM": pd.to_numeric(dfw[num_col], errors="coerce")})
            data_box = data_box.dropna(subset=["NUM"])

            if data_box.empty:
                st.info("Pas de données exploitables pour ce couple Num ↔ Cat (après suppression des NA numériques).")
            else:
                order = (
                    data_box.groupby("CAT")["NUM"]
                            .median()
                            .sort_values(ascending=False)
                            .index.astype(str)
                            .tolist()
                )
                fig_box = px.box(data_box, x="CAT", y="NUM", title=f"{num_col} par {cat_col}")
                fig_box.update_xaxes(categoryorder="array", categoryarray=order)
                st.plotly_chart(fig_box, use_container_width=True)

    # ========================================================
    # Onglet 4 — Nuage de points
    # ========================================================
    with tab4:
        st.markdown("### 🧮 Nuage de points")

        if len(num_cols) < 2:
            st.warning("Il faut au moins deux variables numériques pour tracer un nuage de points.")
        else:
            x = st.selectbox("🧭 Axe X", num_cols, key="xscatter")
            y = st.selectbox("🧭 Axe Y", num_cols, key="yscatter")
            color = st.selectbox("🎨 Couleur (optionnelle)", [None] + cat_cols, key="color_scatter")

            # DF minimal aux noms sûrs pour éviter les collisions/duplicats
            plot_df = pd.DataFrame({
                "X": pd.to_numeric(dfw[x], errors="coerce"),
                "Y": pd.to_numeric(dfw[y], errors="coerce"),
            })
            if color:
                plot_df["COLOR"] = dfw[color]

            # Filtre NA sur X/Y
            plot_df = plot_df.dropna(subset=["X", "Y"])

            # Downsample pour garder l’UI réactive
            max_points = 20_000
            if len(plot_df) > max_points:
                plot_df = plot_df.sample(max_points, random_state=42)

            if plot_df.empty:
                st.info("Aucune donnée exploitable pour ce couple X/Y (après filtrage des NA).")
            else:
                fig_scatter = px.scatter(
                    plot_df,
                    x="X", y="Y",
                    color="COLOR" if "COLOR" in plot_df.columns else None,
                    title=f"Scatter {y} ~ {x}" + (f" (couleur : {color})" if color else "")
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
 

 
    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )