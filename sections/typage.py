# ============================================================
# Fichier : sections/typage.py
# Objectif : Suggestions et corrections interactives des types
# Version  : harmonisée (UI unifiée + fichier actif)
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import pandas as pd
import streamlit as st
from utils.steps import EDA_STEPS
from config import color
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import get_active_dataframe
from utils.ui_utils import section_header, show_eda_progress, show_footer


def run_typage() -> None:
    """
    Atelier « Typage » : propose un type cible par colonne (heuristique simple),
    puis applique des conversions tolérantes et *nullable*.

    Parcours :
      1) Récupère le DataFrame actif (via `get_active_dataframe`).
      2) Calcule des suggestions (cache Streamlit pour réactivité).
      3) L’utilisateur choisit le type cible parmi : int, float, string, bool, datetime.
      4) Application des conversions (to_numeric, to_datetime, astype) avec `errors="coerce"`
         et dtypes Pandas *nullable* quand pertinent (Int64, boolean, string).

    Pourquoi des dtypes *nullable* ?
      - `Int64` (avec I majuscule) et `boolean` gèrent proprement les valeurs manquantes
        (NA) contrairement à `int64`/`bool` natifs NumPy.

    Effets de bord :
      - Les valeurs non convertibles sont mises à NA (coercion).
      - Le DataFrame actif (st.session_state["df"]) est mis à jour sur place.
      - Un snapshot est enregistré (suffixe "typage_auto") et l’action est loggée.
    """
    # ---------- En-tête unifié : bannière + titre ----------
    section_header(
        title="Typage",
        subtitle="Suggestions automatiques et corrections interactives des types.",
        section="analyse",  # image définie dans config.SECTION_BANNERS["analyse"]
        emoji="🧾",
    )

    # ---------- Barre de progression (visuelle, non bloquante) ----------
    show_eda_progress(EDA_STEPS, compact=True, single_row=True)

    # ---------- Fichier actif ----------
    df, nom = get_active_dataframe()
    if df is None:
        st.warning("❌ Aucun fichier actif. Sélectionnez-en un dans l’onglet **Fichiers**.")
        return

    st.markdown(f"🔎 **Fichier actif : `{nom}`** — {df.shape[0]} lignes × {df.shape[1]} colonnes")

    # ---------- Suggestions automatiques ----------
    @st.cache_data(show_spinner=False)
    def suggerer_types(df_in: pd.DataFrame) -> dict[str, str]:
        """
        Déduit un type cible simple à partir du dtype actuel.

        Règles :
          - integer → "int"         (proposé en Int64 nullable)
          - float   → "float"
          - bool    → "bool"        (proposé en boolean nullable)
          - datetime→ "datetime"
          - sinon   → "string"      (dtype string Pandas, nullable)

        Note :
          - Ce n'est pas une inférence statistique (pas d'analyse de format).
            C’est une initialisation raisonnable à affiner manuellement.
        """
        suggestions: dict[str, str] = {}
        for col in df_in.columns:
            s = df_in[col]
            if pd.api.types.is_integer_dtype(s):
                suggestions[col] = "int"
            elif pd.api.types.is_float_dtype(s):
                suggestions[col] = "float"
            elif pd.api.types.is_bool_dtype(s):
                suggestions[col] = "bool"
            elif pd.api.types.is_datetime64_any_dtype(s):
                suggestions[col] = "datetime"
            else:
                suggestions[col] = "string"
        return suggestions

    types_suggeres = suggerer_types(df)
    type_options = ["int", "float", "string", "bool", "datetime"]
    corrections: dict[str, str] = {}

    st.markdown("### ✏️ Choisissez le type cible pour chaque colonne")
    with st.expander("Afficher les suggestions de typage", expanded=True):
        for col, suggestion in types_suggeres.items():
            current_type = str(df[col].dtype)
            st.caption(f"🔎 `{col}` : dtype détecté → `{current_type}`")
            selected = st.selectbox(
                f"Type cible pour `{col}`",
                type_options,
                index=type_options.index(suggestion),
                key=f"type_{col}",
            )
            corrections[col] = selected

    st.divider()

    # ---------- Application des corrections ----------
    if st.button("⚙️ Appliquer les corrections de typage", type="primary"):
        erreurs: list[tuple[str, str]] = []

        # On travaille sur le DF actif (atelier interactif) :
        # conversions tolérantes (errors='coerce') pour éviter les plantages.
        for col, t in corrections.items():
            try:
                if t == "int":
                    # to_numeric + Int64 (nullable) pour conserver les NA éventuels
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                elif t == "float":
                    # float64 avec coercion (NA sur non-convertibles)
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif t == "bool":
                    # dtype 'boolean' (nullable) ; astype gère {True/False/1/0/"true"/"false"} partiellement
                    # Les valeurs non mappées deviennent NA.
                    df[col] = df[col].astype("boolean")
                elif t == "datetime":
                    # Inférence tolérante (format mixte → NA si ambiguïtés)
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=False)
                else:
                    # dtype 'string' Pandas (nullable) → préférable à object
                    df[col] = df[col].astype("string")
            except Exception as e:
                erreurs.append((col, str(e)))

        # Mise à jour du state global (clé standard "df")
        st.session_state["df"] = df

        # Snapshot + log
        save_snapshot(df, suffix="typage_auto")
        log_action("typage", f"Typage appliqué sur {len(corrections)} colonnes")

        # Feedback utilisateur
        if erreurs:
            st.warning("⚠️ Des erreurs sont survenues lors de la conversion :")
            for c, msg in erreurs:
                st.error(f"`{c}` → {msg}")
        else:
            st.success("✅ Typage appliqué avec succès. Snapshot enregistré.")

    st.divider()

    # ---------- Note de contexte ----------
    st.info(
        "ℹ️ Cette page est un **atelier de typage**. "
        "La validation de l’étape *Types de variables* se fait depuis l’onglet **Exploration → Types**."
    )

    # ---------- Footer ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
