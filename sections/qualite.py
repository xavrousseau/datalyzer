# ============================================================
# Fichier : sections/qualite.py
# Objectif : Évaluation de la qualité des données (score + anomalies)
# Version  : unifiée (UI harmonisée, étape EDA = "stats")
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.steps import EDA_STEPS
from utils.eda_utils import (
    detect_constant_columns,
    get_columns_above_threshold,
    detect_outliers,
)

from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe, validate_step_button
from utils.ui_utils import section_header, show_footer


# =============================== Helpers internes ==============================

def _compute_quality_score(df: pd.DataFrame) -> int:
    """
    Calcule un score de qualité très lisible sur 100.
    Heuristique volontairement simple, facile à expliquer :

      - Pénalité NA : moyenne des NA (% cellules vides) × 40 points.
      - Pénalité doublons : 20 points si au moins une ligne dupliquée.
      - Pénalité colonnes constantes : part des colonnes à 1 modalité × 40 points.

    Le score est borné à [0, 100].

    Remarque : c’est un baromètre pédagogique, pas un indicateur normatif.
    """
    if df.empty:
        return 0
    na_penalty    = df.isna().mean().mean() * 40
    dup_penalty   = 20 if df.duplicated().any() else 0
    const_penalty = (df.nunique() <= 1).sum() / max(1, df.shape[1]) * 40
    return max(0, int(100 - (na_penalty + dup_penalty + const_penalty)))


def _find_placeholder_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte quelques valeurs « placeholders » courantes (insensibles à la casse).

    Valeurs : {"unknown","n/a","na","undefined","none","missing","?"}

    Retourne un DataFrame (colonne -> nb d’occurrences) filtré sur > 0.
    """
    placeholder_values = {"unknown", "n/a", "na", "undefined", "none", "missing", "?"}
    hits = {
        col: int(df[col].astype(str).str.lower().isin(placeholder_values).sum())
        for col in df.columns
    }
    hits = {k: v for k, v in hits.items() if v > 0}
    return pd.DataFrame.from_dict(hits, orient="index", columns=["Occurrences"]) if hits else pd.DataFrame()


# ================================== Vue =======================================

def run_qualite() -> None:
    """
    Tableau « Qualité » :
      - Score global compréhensible (0–100) basé sur NA, doublons, colonnes constantes.
      - Résumé des anomalies typiques (NA>50%, constantes, doublons).
      - Vérifications ciblées : numériques encodés en texte, noms suspects, placeholders.
      - Coup d’œil outliers (z-score>3) pour chaque variable numérique.
      - Liste de colonnes candidates à suppression + correction semi-auto.

    Effets :
      - Certaines actions modifient `st.session_state["df"]` in-place,
        créent un snapshot et loguent l’action.
    """
    # ---------- En-tête + barre compacte ----------
    section_header(
        title="Qualité",
        subtitle="Évaluez la qualité des données (score global, doublons, placeholders, outliers…).",
        section="qualite",  # ← utilise SECTION_BANNERS["qualite"]
        emoji="",
    )

    # ---------- DataFrame actif ----------
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif ou fichier vide. Sélectionnez un fichier dans l’onglet **Chargement**.")
        return

    # ---------- Score global (pédagogique) ----------
    st.markdown("### 🌸 Score global de qualité")
    score = _compute_quality_score(df)
    st.subheader(f"🌟 **{score} / 100**")
    st.caption(
        "Le score combine le taux de valeurs manquantes, la présence de doublons et la part de colonnes constantes. "
        "C’est un indicateur pédagogique pour prioriser les actions."
    )
    st.divider()

    # ---------- Résumé des anomalies ----------
    st.markdown("### 🧾 Résumé des anomalies")
    nb_const = int((df.nunique() <= 1).sum())
    nb_na50  = int((df.isna().mean() > 0.5).sum())
    nb_dup   = int(df.duplicated().sum())

    st.markdown(
        f"- 🔁 **{nb_dup} lignes dupliquées**  \n"
        f"- 🟨 **{nb_na50} colonnes avec >50% de NA**  \n"
        f"- 🧊 **{nb_const} colonnes constantes**"
    )
    st.divider()

    # ---------- Heatmap NA (optionnelle) ----------
    # Note perf : px.imshow sur de très gros tableaux peut être coûteux.
    # On laisse l’utilisateur décider via une case à cocher.
    if st.checkbox("📊 Afficher la heatmap des NA"):
        if df.size > 1_000_000:
            st.warning("⚠️ Tableau volumineux : l’affichage peut être lent.")
        fig = px.imshow(
            df.isna(),
            aspect="auto",
            color_continuous_scale="Blues",
            title="Carte des valeurs manquantes",
        )
        st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # ---------- Vérifications supplémentaires ----------
    st.markdown("### 🩺 Vérifications supplémentaires")

    # (1) Colonnes 'object' susceptibles d’être des numériques encodés en texte.
    # Heuristique : après suppression des '.' et ',' (formats décimaux), >=80% de str.isnumeric().
    suspect_numeric_as_str = [
        col for col in df.select_dtypes(include="object").columns
        if df[col].astype(str)
              .str.replace(".", "", regex=False)
              .str.replace(",", "", regex=False)
              .str.isnumeric().mean() > 0.8
    ]
    if suspect_numeric_as_str:
        st.warning("🔢 Colonnes `object` contenant majoritairement des chiffres (potentiel typage à corriger) :")
        st.code(", ".join(suspect_numeric_as_str))

    # (2) Noms de colonnes suspects : 'Unnamed' (Excel), ou présence de 'id'
    suspect_names = [col for col in df.columns if col.startswith("Unnamed") or "id" in col.lower()]
    if suspect_names:
        st.warning("📛 Noms de colonnes suspects :")
        st.code(", ".join(suspect_names))

    # (3) Valeurs placeholders
    placeholder_df = _find_placeholder_values(df)
    if not placeholder_df.empty:
        st.warning("❓ Valeurs placeholders détectées :")
        st.dataframe(placeholder_df, use_container_width=True)
    st.divider()

    # ---------- Outliers globaux (z-score > 3) ----------
    st.markdown("### 📉 Valeurs extrêmes (Z-score > 3)")
    num_cols = df.select_dtypes(include="number").columns.tolist()
    out_counts: dict[str, int] = {}
    for col in num_cols:
        s = df[col].dropna()
        if s.empty or s.std(ddof=0) == 0:
            continue
        try:
            out_idx_or_df = detect_outliers(df[[col]], method="zscore", threshold=3.0)
            out_counts[col] = int(out_idx_or_df.shape[0]) if isinstance(out_idx_or_df, pd.DataFrame) else int(len(out_idx_or_df))
        except Exception:
            # On ignore silencieusement une colonne problématique (types inattendus, etc.).
            continue

    if out_counts:
        st.warning("🚨 Outliers détectés :")
        st.dataframe(pd.DataFrame.from_dict(out_counts, orient="index", columns=["Nb outliers"]))
        st.caption("Astuce : utilisez l’onglet **Anomalies** pour cibler, visualiser et corriger variable par variable.")
    else:
        st.success("✅ Aucun outlier détecté avec cette règle globale.")
    st.divider()

    # ---------- Colonnes problématiques (constantes & >50% NA) ----------
    st.markdown("### 🧊 Colonnes constantes & >50% NA")
    const_cols = detect_constant_columns(df)
    na_cols    = get_columns_above_threshold(df, 0.5)
    if const_cols or na_cols:
        candidates = sorted(set(const_cols) | set(na_cols))
        st.warning(f"⚠️ Colonnes candidates à suppression ({len(candidates)}) :")
        st.code(", ".join(candidates))
    else:
        st.info("Rien à signaler selon ces règles simples.")
    st.divider()

    # ---------- Correction automatique (semi-auto, confirmée) ----------
    st.markdown("### 🧼 Correction automatique des colonnes problématiques")
    if st.button("Corriger maintenant", key="qual_fix"):
        try:
            to_drop = sorted(set(const_cols) | set(na_cols))
            if not to_drop:
                st.info("Aucune colonne à supprimer selon les règles.")
            else:
                st.markdown("### Colonnes à supprimer :")
                st.code(", ".join(to_drop))
                if st.button("Confirmer la suppression", key="qual_fix_confirm"):
                    # Modif in-place + mise à jour du state
                    df.drop(columns=to_drop, inplace=True, errors="ignore")
                    st.session_state["df"] = df
                    save_snapshot(df, suffix="qualite_cleaned")
                    log_action("qualite_auto_fix", f"{len(to_drop)} colonnes supprimées")
                    st.success(f"✅ Correction appliquée : {len(to_drop)} colonnes supprimées.")
        except Exception as e:
            st.error(f"❌ Erreur pendant la correction : {e}")
    st.divider()

    # ---------- Validation étape EDA ----------
    validate_step_button("stats", context_prefix="qualite_")

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
