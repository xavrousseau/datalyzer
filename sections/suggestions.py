# ============================================================
# Fichier : sections/suggestions.py
# Objectif : Identifier les colonnes à encoder ou à vectoriser
# Version  : harmonisée, seuils paramétrables, détection robuste
# Statut   : Module avancé — HORS barre de progression EDA
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import re
import pandas as pd
import streamlit as st

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe 
from utils.ui_utils import section_header, show_footer


# =============================== Helpers ======================================

def _is_identifier(colname: str) -> bool:
    """
    Heuristique *nominale* d'identifiant :
      motifs usuels : id, uid, uuid, identifiant, code (début/fin/_).
    """
    return bool(re.search(r"(?:^|_)(id|uid|uuid|identifiant|code)(?:$|_)",
                          str(colname), flags=re.I))


def _avg_str_len(s: pd.Series) -> float:
    """
    Longueur moyenne (approx) des chaînes après cast en dtype 'string'.
    Sert à distinguer *texte libre* vs *catégories*.
    """
    try:
        return float(s.astype("string").str.len().dropna().mean())
    except Exception:
        return 0.0


# ================================== Vue =======================================

def run_suggestions() -> None:
    """
    Tableau « Suggestions » : repère les colonnes
      - à **encoder** (catégorielles ou numériques discrètes),
      - à **vectoriser** (texte libre / haute cardinalité),
      - à **exclure** des features (identifiants).

    Le module ne réalise pas l'encodage/la vectorisation ; il dresse un diagnostic.
    """
    # ---------- En-tête unifiée ----------
    section_header(
        title="Suggestions",
        subtitle="Colonnes discrètes à encoder, texte libre à vectoriser.",
        section="analyse",
        emoji="",
    )

    # ---------- DataFrame actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Importez/sélectionnez un fichier dans l’onglet **Fichiers**.")
        return

    # ---------- Paramètres ----------
    with st.expander("⚙️ Paramètres (seuils)"):
        col_a, col_b, col_c = st.columns(3)
        cat_encode_max   = col_a.number_input("Max modalités pour encoder une catégorie",  2, 200, 50, 1)
        num_discrete_max = col_b.number_input("Max modalités pour encoder un numérique",   2, 200, 10, 1)
        text_vectorize_min = col_c.number_input("Min modalités pour vectoriser un texte", 20, 5000, 100, 10)

        col_d, col_e = st.columns(2)
        id_ratio     = col_d.slider("Seuil d’unicité pour ‘identifiant’", 0.5, 1.0, 0.9, 0.05)
        long_text_len = col_e.slider("Longueur moyenne (texte libre)", 10, 200, 30, 5)

    # ---------- Préparation des colonnes ----------
    num_cols = df.select_dtypes(include="number").columns.tolist()
    obj_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    bool_cols = df.select_dtypes(include=["bool", "boolean"]).columns.tolist()
    # datetime + datetime avec TZ
    dt_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

    to_encode_num: dict[str, str] = {}
    to_encode_cat: dict[str, str] = {}
    to_vectorize: dict[str, str]  = {}
    identifiers: dict[str, str]   = {}

    n = len(df)

    # ---------- Identifiants (nom ou unicité élevée) ----------
    for col in df.columns:
        uniq = int(df[col].nunique(dropna=True))
        uniq_ratio = (uniq / n) if n else 0.0
        if _is_identifier(col) or uniq_ratio >= id_ratio:
            identifiers[col] = "🪪 Identifiant (unicité élevée / nom)"

    # Colonnes à ignorer pour les suggestions d'encodage/vectorisation
    ignore = set(bool_cols) | set(dt_cols) | set(identifiers.keys())

    # ---------- Numériques discrets (à encoder) ----------
    for col in [c for c in num_cols if c not in ignore]:
        uniq = int(df[col].nunique(dropna=True))
        # Un numérique avec peu de modalités → catégorie déguisée
        if 2 <= uniq <= num_discrete_max and (uniq / n if n else 0.0) < id_ratio:
            to_encode_num[col] = f"🔢 Numérique discret (modalités={uniq}) — à encoder"

    # ---------- Catégories vs texte libre ----------
    for col in [c for c in obj_cols if c not in ignore]:
        uniq = int(df[col].nunique(dropna=True))
        avg_len = _avg_str_len(df[col])
        if uniq <= cat_encode_max:
            to_encode_cat[col] = f"🏷️ Catégorie (modalités={uniq}) — à encoder"
        elif uniq >= text_vectorize_min or avg_len >= long_text_len:
            to_vectorize[col] = f"📝 Texte libre (modalités={uniq}, len≈{avg_len:.0f}) — à vectoriser"

    # ---------- Rendu des suggestions ----------
    st.markdown("### 🔎 Suggestions détectées")
    any_sugg = False

    if identifiers:
        any_sugg = True
        st.markdown("#### 🪪 Identifiants (à exclure des features)")
        st.dataframe(
            pd.DataFrame.from_dict(identifiers, orient="index", columns=["Raison"]),
            use_container_width=True
        )

    if to_encode_num:
        any_sugg = True
        st.markdown("#### 🔢 Numériques discrets — à encoder")
        st.dataframe(
            pd.DataFrame.from_dict(to_encode_num, orient="index", columns=["Suggestion"]),
            use_container_width=True
        )

    if to_encode_cat:
        any_sugg = True
        st.markdown("#### 🏷️ Catégories — à encoder")
        st.dataframe(
            pd.DataFrame.from_dict(to_encode_cat, orient="index", columns=["Suggestion"]),
            use_container_width=True
        )

    if to_vectorize:
        any_sugg = True
        st.markdown("#### 📝 Texte libre — à vectoriser")
        st.dataframe(
            pd.DataFrame.from_dict(to_vectorize, orient="index", columns=["Suggestion"]),
            use_container_width=True
        )

    if not any_sugg:
        st.success("✅ Aucune colonne à encoder/vectoriser selon ces règles.")

    st.markdown("### 📊 Résumé")
    c1, c2, c3 = st.columns(3)
    c1.metric("À encoder (num)", len(to_encode_num))
    c2.metric("À encoder (cat)", len(to_encode_cat))
    c3.metric("À vectoriser (texte)", len(to_vectorize))

    st.divider()

    # ---------- Suppression optionnelle du texte libre ----------
    # (Correction : remplacement des boutons imbriqués par une confirmation explicite)
    to_drop = list(to_vectorize.keys())
    if to_drop:
        st.markdown("### 🗑️ Colonnes candidates à suppression (texte libre / haute cardinalité)")
        with st.expander("🔎 Détails des colonnes concernées"):
            st.code(", ".join(to_drop))

        st.caption(
            "⚠️ Cette opération **ne crée pas** de vectorisation ; elle sert uniquement "
            "à alléger le dataset pour un prototypage rapide."
        )
        confirm = st.checkbox("Je confirme la suppression des colonnes listées", key="sugg_confirm_drop")

        if st.button("🚮 Supprimer maintenant", type="primary", disabled=not confirm):
            try:
                df.drop(columns=to_drop, inplace=True, errors="ignore")
                st.session_state["df"] = df
                save_snapshot(df, suffix="suggestions_cleaned")
                log_action("suggestions_cleanup", f"{len(to_drop)} colonnes supprimées (texte libre)")
                st.success("✅ Colonnes supprimées. Snapshot sauvegardé.")
            except Exception as e:
                st.error(f"❌ Erreur pendant la suppression : {e}")
    else:
        st.info("Aucune colonne candidate à suppression automatique selon ces règles.")

 
    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
