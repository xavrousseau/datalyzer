# ============================================================
# Fichier : sections/cat_analysis.py
# Objectif : Analyse des variables catégorielles
# Statut   : Module avancé — HORS barre de progression EDA
# Points   :
#   - Matrice de Cramér’s V avec seuil et limite de cardinalité
#   - Croisements cible↔explicative (num→boxplot, cat→crosstab + bar empilée)
#   - Garde-fous sur colonnes disponibles et matrices vides
# Auteur   : Xavier Rousseau 
# ============================================================
 
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Détections de type robustes
from pandas.api.types import (
    is_numeric_dtype,
    is_categorical_dtype,
    is_object_dtype,
    is_string_dtype,
    is_bool_dtype,
)

# Utilitaires internes du projet
from utils.filters import get_active_dataframe
from utils.eda_utils import compute_cramers_v_matrix, plot_boxplots
from utils.ui_utils import section_header, show_footer


# =============================================================================
# Helpers — typage, libellés, et styling « safe » sans Matplotlib
# =============================================================================

def _is_categorical_like(s: pd.Series) -> bool:
    """Retourne True si la série *peut* être traitée comme **catégorielle**.

    On prend large : dtype `category`, `object`, `string`, ou `bool`.
    Pourquoi ? En pratique, beaucoup de colonnes qualitatives arrivent en `object`
    (ex. lecture CSV). Les exclure serait frustrant.
    """
    return (
        is_categorical_dtype(s)
        or is_object_dtype(s)
        or is_string_dtype(s)
        or is_bool_dtype(s)
    )


def _labelize(x: Any) -> str:
    """Transforme un libellé quelconque en **chaîne sûre** pour l'affichage.

    - Remplace `None` et `NaN` par le symbole `∅` (repérable visuellement).
    - Retourne toujours un `str` compatible JSON/Plotly/Streamlit.
    """
    if x is None:
        return "∅"
    try:
        if isinstance(x, float) and np.isnan(x):
            return "∅"
    except Exception:
        pass
    return str(x)


def _sanitize_index_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne une **copie** stringifiée pour éviter les soucis d'index/colonnes.

    Objectif : éviter les erreurs JSON côté Streamlit si des `NaN`/`None` se glissent
    dans les noms d'index ou de colonnes.
    """
    out = df.copy()
    out.index = pd.Index([_labelize(i) for i in out.index], name=out.index.name or "index")
    out.columns = pd.Index([_labelize(c) for c in out.columns], name=out.columns.name)
    return out


def _style_bg_gradient_safe(df: pd.DataFrame, cmap: str = "Purples"):
    """Applique un dégradé de fond via `pandas.Styler.background_gradient` **si possible**.

    Cette méthode nécessite **Matplotlib**. Sur Streamlit Cloud (ou env minimal),
    Matplotlib peut être absent. Dans ce cas, on renvoie le DataFrame tel quel
    (pas de style, mais surtout **pas de crash**).
    """
    try:
        import matplotlib  # noqa: F401 - simple test de présence
        return df.style.background_gradient(cmap=cmap)
    except Exception:
        return df


# =============================================================================
# Vue principale — atelier « Analyse catégorielle »
# =============================================================================

def run_analyse_categorielle() -> None:
    """Affiche l'atelier d'analyse des variables catégorielles.

    Deux volets complémentaires :
      1) **Corrélations** entre variables catégorielles (matrice de Cramér's V),
         avec seuil, limitation de cardinalité et heatmap optionnelle.
      2) **Croisements** avec une **cible** :
         - Cible **numérique** → *boxplots* par catégorie explicative.
         - Cible **catégorielle-like** → *crosstab* normalisé (%) + *barres empilées*.

    Principes de robustesse :
      - Détection de type tolérante (catégoriel « large »).
      - Libellés nettoyés pour compatibilité JSON.
      - Garde-fous si matrices ou jeux sont vides.
    """
    # ---------- En-tête ----------
    section_header(
        title="Analyse catégorielle",
        subtitle="Corrélations et croisements avec une cible.",
        section="analyse",
        emoji="",
    )

    # ---------- Fichier actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Merci de charger un fichier dans l’onglet **Fichiers**.")
        return

    # ---------- Détection des colonnes catégorielles ----------
    # On prend large : object/category/string/bool
    cat_cols = df.select_dtypes(include=["object", "category", "string", "boolean"]).columns.tolist()
    if not cat_cols:
        st.info("❗ Aucune variable catégorielle détectée.")
        return

    # ---------- Onglets ----------
    tab1, tab2 = st.tabs(["🔗 Corrélations (Cramér’s V)", "🎯 Cible par variable"])

    # ==================================================================
    # Onglet 1 — Corrélations (Cramér’s V)
    # ==================================================================
    with tab1:
        st.markdown("### 🔗 Corrélations entre variables catégorielles (Cramér’s V)")

        # Paramètres (expander pour aérer l'UI)
        with st.expander("⚙️ Paramètres"):
            c1, c2 = st.columns(2)
            min_corr = c1.slider("Seuil d'affichage (Cramér ≥)", 0.0, 1.0, 0.3, 0.05)
            max_levels = c2.number_input(
                "Max modalités par variable (pour crosstabs)",
                min_value=2,
                max_value=200,
                value=50,
                step=1,
                help="Les colonnes au-delà de ce seuil sont ignorées pour éviter des tables trop volumineuses.",
            )
            show_full = st.checkbox("Afficher la matrice complète (non filtrée)", value=False)

        # Calcul de la matrice — la fonction utilitaire gère les cardinalités
        try:
            cramers_df = compute_cramers_v_matrix(df[cat_cols], max_levels=max_levels)
        except Exception as e:
            st.error(f"Erreur lors du calcul de Cramér’s V : {e}")
            cramers_df = pd.DataFrame()

        if cramers_df.empty:
            st.info("Aucune matrice exploitable (trop peu de colonnes ou cardinalités trop élevées).")
        else:
            # On ignore la diagonale (corrélation parfaite avec soi-même) pour le filtrage
            cramers_nodiag = cramers_df.copy()
            np.fill_diagonal(cramers_nodiag.values, np.nan)

            if show_full:
                st.dataframe(_style_bg_gradient_safe(cramers_df), use_container_width=True)
            else:
                filtered = cramers_nodiag.where(cramers_nodiag >= min_corr)
                filtered = filtered.dropna(axis=0, how="all").dropna(axis=1, how="all")
                if filtered.empty:
                    st.info(f"Aucune paire avec Cramér’s V ≥ {min_corr}.")
                else:
                    st.dataframe(_style_bg_gradient_safe(filtered), use_container_width=True)

            # Heatmap optionnelle : vue macro instantanée
            if st.checkbox("Afficher une heatmap (aperçu global)"):
                try:
                    fig = px.imshow(
                        cramers_df,
                        color_continuous_scale="Purples",
                        zmin=0,
                        zmax=1,
                        aspect="auto",
                        origin="lower",
                        title="Matrice de Cramér’s V (aperçu)",
                    )
                    fig.update_layout(margin=dict(t=40, l=20, r=20, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Heatmap indisponible : {e}")

    # ==================================================================
    # Onglet 2 — Croisement avec une variable cible
    # ==================================================================
    with tab2:
        st.markdown("### 🎯 Analyse d’une variable cible")

        # Choix de la cible (peut être numérique OU catégorielle-like)
        cible = st.selectbox("🎯 Variable cible", df.columns.tolist())

        # Variables explicatives catégorielles à cardinalité raisonnable (≤ 20)
        cat_cols_filtered = [c for c in cat_cols if df[c].nunique(dropna=False) <= 20 and c != cible]
        if not cat_cols_filtered:
            st.warning("❌ Pas de variables catégorielles 'explicatives' disponibles (≤ 20 modalités).")
            st.stop()

        explicative = st.selectbox("📂 Variable explicative (catégorielle)", cat_cols_filtered)

        # Typage de la cible — deux familles autorisées : numérique OU catégorielle-like
        cible_is_num = is_numeric_dtype(df[cible])
        cible_is_cat = _is_categorical_like(df[cible])

        # ---- Cas 2.a) Cible numérique → boxplot num↔cat ----
        if cible_is_num:
            st.markdown("#### 📉 Boxplot (cible numérique par catégorie explicative)")
            try:
                fig = plot_boxplots(df, cible, explicative)  # utilitaire projet
            except Exception:
                fig = None

            if fig is None:
                # Fallback : coercition en numérique + drop des NaN
                y = pd.to_numeric(df[cible], errors="coerce")
                x = df[explicative].astype("string")
                data = pd.DataFrame({explicative: x, cible: y}).dropna(subset=[cible])

                if data.empty:
                    st.info("Impossible de tracer le boxplot (aucune valeur numérique exploitable après coercition).")
                else:
                    fig = px.box(
                        data,
                        x=explicative,
                        y=cible,
                        points="outliers",
                        title=f"{cible} par {explicative}",
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.plotly_chart(fig, use_container_width=True)

        # ---- Cas 2.b) Cible catégorielle-like → crosstab % + barres empilées ----
        elif cible_is_cat:
            st.markdown("#### 📊 Répartition croisée normalisée (par ligne)")

            # `dropna=False` : on conserve une colonne dédiée aux valeurs manquantes de la cible.
            cross = pd.crosstab(df[explicative], df[cible], normalize="index", dropna=False).round(3)

            # Stringifier labels pour compatibilité JSON/Plotly/Streamlit
            cross = _sanitize_index_and_columns(cross)

            st.dataframe(cross, use_container_width=True)

            st.markdown("#### 📊 Répartition empilée")
            # Passage en long format pour empiler facilement les barres
            cross_plot = (cross * 100).reset_index().melt(
                id_vars=explicative,  # l'index.name est conservé par reset_index()
                var_name=str(df[cible].name or "Cible"),
                value_name="Part (%)",
            )

            fig_stack = px.bar(
                cross_plot,
                x=explicative,
                y="Part (%)",
                color=str(df[cible].name or "Cible"),
                title=f"Répartition de {df[cible].name or 'Cible'} par {explicative} (normalisée %)",
                barmode="stack",
            )

            # Ordonner l'axe X par fréquence décroissante (sur DF complet, labels stringifiés)
            order_x = df[explicative].astype("string").value_counts(dropna=False).index.tolist()
            order_x = [_labelize(x) for x in order_x]
            fig_stack.update_xaxes(categoryorder="array", categoryarray=order_x)
            fig_stack.update_yaxes(range=[0, 100])

            st.plotly_chart(fig_stack, use_container_width=True)

        # ---- Cas 2.c) Cible non exploitable ----
        else:
            st.warning(
                "❌ La variable cible sélectionnée n’est pas exploitable ici "
                "(ni numérique, ni catégorielle-like : category/object/string/bool)."
            )

    # ---------- Footer ----------
    show_footer(author="Xavier Rousseau", site_url="https://xavrousseau.github.io/", version="1.0")
