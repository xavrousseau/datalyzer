# ============================================================
# Fichier : suggestions.py
# Objectif : Identifier les colonnes à encoder ou à vectoriser
# Version : harmonisée, seuils paramétrables, détection robuste
# ============================================================

import re
import pandas as pd
import streamlit as st

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header


def _is_identifier(colname: str) -> bool:
    return bool(re.search(r"(?:^|_)(id|uid|uuid|identifiant|code)(?:$|_)", str(colname), flags=re.I))


def _avg_str_len(s: pd.Series) -> float:
    try:
        return float(s.astype("string").str.len().dropna().mean())
    except Exception:
        return 0.0


def run_suggestions():
    show_header_image_safe("bg_night_serenity.png")
    show_icon_header("💡", "Suggestions", "Colonnes discrètes à encoder, texte libre à vectoriser")

    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif. Importez/sélectionnez un fichier dans l’onglet Fichiers.")
        return

    with st.expander("⚙️ Paramètres (seuils)"):
        col_a, col_b, col_c = st.columns(3)
        cat_encode_max = col_a.number_input("Max modalités pour encoder une catégorie", 2, 200, 50, 1)
        num_discrete_max = col_b.number_input("Max modalités pour encoder un numérique", 2, 200, 10, 1)
        text_vectorize_min = col_c.number_input("Min modalités pour vectoriser un texte", 20, 5000, 100, 10)
        id_ratio = st.slider("Seuil d’unicité pour ‘identifiant’", 0.5, 1.0, 0.9, 0.05)
        long_text_len = st.slider("Longueur moyenne (texte libre)", 10, 200, 30, 5)

    # --- Préparation des colonnes (✅ fix datetimes) ---
    num_cols = df.select_dtypes(include="number").columns.tolist()
    obj_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    bool_cols = df.select_dtypes(include=["bool", "boolean"]).columns.tolist()
    dt_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

    to_encode_num, to_encode_cat, to_vectorize, identifiers = {}, {}, {}, {}
    n = len(df)

    # Identifiants (nom ou unicité élevée)
    for col in df.columns:
        uniq = df[col].nunique(dropna=True)
        uniq_ratio = (uniq / n) if n else 0
        if _is_identifier(col) or uniq_ratio >= id_ratio:
            identifiers[col] = "🪪 Identifiant (unicité élevée / nom)"

    ignore = set(bool_cols) | set(dt_cols) | set(identifiers.keys())

    # Numériques discrets
    for col in [c for c in num_cols if c not in ignore]:
        uniq = int(df[col].nunique(dropna=True))
        if 2 <= uniq <= num_discrete_max and (uniq / n if n else 0) < id_ratio:
            to_encode_num[col] = f"🔢 Numérique discret (modalités={uniq}) — à encoder"

    # Catégories vs texte libre
    for col in [c for c in obj_cols if c not in ignore]:
        uniq = int(df[col].nunique(dropna=True))
        avg_len = _avg_str_len(df[col])
        if uniq <= cat_encode_max:
            to_encode_cat[col] = f"🏷️ Catégorie (modalités={uniq}) — à encoder"
        elif uniq >= text_vectorize_min or avg_len >= long_text_len:
            to_vectorize[col] = f"📝 Texte libre (modalités={uniq}, len≈{avg_len:.0f}) — à vectoriser"

    st.markdown("### 🔎 Suggestions détectées")
    any_sugg = False

    if identifiers:
        any_sugg = True
        st.markdown("#### 🪪 Identifiants (à exclure des features)")
        st.dataframe(pd.DataFrame.from_dict(identifiers, orient="index", columns=["Raison"]), use_container_width=True)

    if to_encode_num:
        any_sugg = True
        st.markdown("#### 🔢 Numériques discrets — à encoder")
        st.dataframe(pd.DataFrame.from_dict(to_encode_num, orient="index", columns=["Suggestion"]), use_container_width=True)

    if to_encode_cat:
        any_sugg = True
        st.markdown("#### 🏷️ Catégories — à encoder")
        st.dataframe(pd.DataFrame.from_dict(to_encode_cat, orient="index", columns=["Suggestion"]), use_container_width=True)

    if to_vectorize:
        any_sugg = True
        st.markdown("#### 📝 Texte libre — à vectoriser")
        st.dataframe(pd.DataFrame.from_dict(to_vectorize, orient="index", columns=["Suggestion"]), use_container_width=True)

    if not any_sugg:
        st.success("✅ Aucune colonne à encoder/vectoriser selon ces règles.")

    st.markdown("### 📊 Résumé")
    c1, c2, c3 = st.columns(3)
    c1.metric("À encoder (num)", len(to_encode_num))
    c2.metric("À encoder (cat)", len(to_encode_cat))
    c3.metric("À vectoriser (texte)", len(to_vectorize))

    st.divider()

    # Suppression optionnelle du texte libre
    to_drop = list(to_vectorize.keys())
    if to_drop:
        st.markdown("### 🗑️ Colonnes candidates à suppression (texte libre / haute cardinalité)")
        with st.expander("🔎 Détails des colonnes concernées"):
            st.code(", ".join(to_drop))
        if st.button("🚮 Préparer la suppression des colonnes", key="sugg_drop_prepare"):
            st.warning(
                f"Vous êtes sur le point de supprimer {len(to_drop)} colonne(s) de texte libre. "
                "Cela **ne crée pas** de vectorisation automatique."
            )
            if st.button("✅ Confirmer la suppression", key="sugg_drop_confirm"):
                try:
                    df.drop(columns=to_drop, inplace=True, errors="ignore")
                    st.session_state.df = df
                    save_snapshot(df, suffix="suggestions_cleaned")
                    log_action("suggestions_cleanup", f"{len(to_drop)} colonnes supprimées (texte libre)")
                    st.success("✅ Colonnes supprimées. Snapshot sauvegardé (CSV).")
                except Exception as e:
                    st.error(f"❌ Erreur pendant la suppression : {e}")
    else:
        st.info("Aucune colonne candidate à suppression automatique selon ces règles.")
