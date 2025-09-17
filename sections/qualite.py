# ============================================================
# Fichier : qualite.py
# Objectif : Évaluation de la qualité des données (score + anomalies)
# Version : unifiée (utilise utils.eda_utils), barre compacte, étape EDA "stats"
# ============================================================

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

from utils.steps import EDA_STEPS
from utils.eda_utils import (
    detect_constant_columns,
    detect_low_variance_columns,        # dispo si tu veux l'ajouter aux règles
    get_columns_above_threshold,
    detect_outliers,
)
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import show_header_image_safe, show_icon_header


def run_qualite():
    # === En-tête + barre de progression ======================
    show_header_image_safe("bg_pagoda_moon.png")
    show_icon_header("🧪", "Qualité", "Détection de colonnes suspectes, doublons, placeholders, outliers…")

    # === DataFrame actif =====================================
    df, nom = get_active_dataframe()
    if df is None or df.empty:
        st.warning("❌ Aucun fichier actif ou fichier vide. Sélectionne un fichier dans l’onglet Fichiers.")
        return

    # === Score global (simple et explicite) ==================
    st.markdown("### 🌸 Score global de qualité")
    na_penalty   = df.isna().mean().mean() * 40                     # pénalise les NA moyens
    dup_penalty  = 20 if df.duplicated().any() else 0               # pénalise s'il y a des doublons
    const_penalty= (df.nunique() <= 1).sum() / max(1, df.shape[1]) * 40
    score = max(0, int(100 - (na_penalty + dup_penalty + const_penalty)))
    st.subheader(f"🌟 **{score} / 100**")
    st.divider()

    # === Résumé des anomalies clés ===========================
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

    # === Heatmap NA (optionnelle) ============================
    if st.checkbox("📊 Afficher la heatmap des NA"):
        fig = px.imshow(
            df.isna(),
            aspect="auto",
            color_continuous_scale="Blues",
            title="Carte des valeurs manquantes",
        )
        st.plotly_chart(fig, use_container_width=True)
    st.divider()

    # === Vérifications supplémentaires =======================
    st.markdown("### 🩺 Vérifications supplémentaires")

    # Colonnes 'object' qui semblent numériques
    suspect_numeric_as_str = [
        col for col in df.select_dtypes(include="object").columns
        if df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", "", regex=False).str.isnumeric().mean() > 0.8
    ]
    if suspect_numeric_as_str:
        st.warning("🔢 Colonnes `object` contenant majoritairement des chiffres :")
        st.code(", ".join(suspect_numeric_as_str))

    # Noms de colonnes suspects
    suspect_names = [col for col in df.columns if col.startswith("Unnamed") or "id" in col.lower()]
    if suspect_names:
        st.warning("📛 Noms de colonnes suspects :")
        st.code(", ".join(suspect_names))

    # Valeurs placeholders communes
    placeholder_values = {"unknown", "n/a", "na", "undefined", "none", "missing", "?"}
    placeholder_hits = {
        col: int(df[col].astype(str).str.lower().isin(placeholder_values).sum())
        for col in df.columns
    }
    placeholder_hits = {k: v for k, v in placeholder_hits.items() if v > 0}
    if placeholder_hits:
        st.warning("❓ Valeurs placeholders détectées :")
        st.dataframe(pd.DataFrame.from_dict(placeholder_hits, orient="index", columns=["Occurrences"]))

    st.divider()

    # === Outliers (détection commune) ========================
    st.markdown("### 📉 Valeurs extrêmes (Z-score > 3, méthode commune)")
    num_cols = df.select_dtypes(include="number").columns.tolist()
    out_counts = {}
    for col in num_cols:
        s = df[col].dropna()
        if s.empty or s.std(ddof=0) == 0:
            continue
        try:
            out_idx_or_df = detect_outliers(df[[col]], method="zscore", threshold=3.0)
            if isinstance(out_idx_or_df, pd.DataFrame):
                out_counts[col] = int(out_idx_or_df.shape[0])
            else:  # Index ou liste d’index
                out_counts[col] = int(len(out_idx_or_df))
        except Exception:
            # En cas d’erreur inattendue sur une colonne, on l’ignore dans ce résumé
            continue

    if out_counts:
        st.warning("🚨 Outliers détectés :")
        st.dataframe(pd.DataFrame.from_dict(out_counts, orient="index", columns=["Nb outliers"]))
    else:
        st.success("✅ Aucun outlier détecté avec cette règle globale.")
    st.divider()

    # === Colonnes problématiques identifiées =================
    st.markdown("### 🧊 Colonnes constantes & >50% NA")
    const_cols = detect_constant_columns(df)
    na_cols    = get_columns_above_threshold(df, 0.5)   # 50% NA
    if const_cols or na_cols:
        st.warning(f"⚠️ Colonnes candidates à suppression ({len(set(const_cols) | set(na_cols))}) :")
        st.code(", ".join(sorted(set(const_cols) | set(na_cols))))
    else:
        st.info("Rien à signaler selon ces règles simples.")
    st.divider()

    # === Correction automatique (règles claires) =============
    st.markdown("### 🧼 Correction automatique des colonnes problématiques")
    if st.button("Corriger maintenant", key="qual_fix"):
        try:
            to_drop = sorted(set(const_cols) | set(na_cols))
            if not to_drop:
                st.info("Aucune colonne à supprimer selon les règles (constantes ou >50% NA).")
            else:
                st.markdown("### Colonnes à supprimer :")
                st.code(", ".join(to_drop))
                if st.button("Confirmer la suppression", key="qual_fix_confirm"):
                    df.drop(columns=to_drop, inplace=True, errors="ignore")
                    st.session_state.df = df
                    save_snapshot(df, suffix="qualite_cleaned")
                    log_action("qualite_auto_fix", f"{len(to_drop)} colonnes supprimées")
                    st.success(f"✅ Correction appliquée : {len(to_drop)} colonnes supprimées.")
        except Exception as e:
            st.error(f"❌ Erreur pendant la correction : {e}")

    st.divider()
