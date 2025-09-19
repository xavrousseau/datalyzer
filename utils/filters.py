# ============================================================
# Fichier : utils/filters.py
# Objectif : Fonctions utilitaires pour Datalyzer
# - Sélection du fichier actif
# - Validation d'étapes + snapshot
# - Petits filtres DataFrame
# Version : robuste, idempotente, sans doublons d'alertes
# ============================================================

from __future__ import annotations

from typing import Optional, Tuple, List
import re

import streamlit as st
import pandas as pd

from utils.snapshot_utils import save_snapshot


# ================================ Sélecteur DF =================================

def get_active_dataframe(
    *,
    selector_label: str = "🗂️ Sélectionner un fichier à analyser :",
    selector_key: str = "global_df_selector",
    dfs_key: str = "dfs",
    df_key: str = "df",
) -> Tuple[pd.DataFrame, str] | Tuple[None, None]:
    """
    Permet de sélectionner dynamiquement un fichier chargé via un selectbox.
    - Si un seul fichier est présent, il est sélectionné automatiquement.
    - Met aussi à jour st.session_state[df_key] pour usage aval.
    - Ne spamme pas de warnings en cas d'absence : retourne (None, None).

    Returns:
        (df, name) si un fichier actif est disponible, sinon (None, None).
    """
    dfs = st.session_state.get(dfs_key, {})
    if not dfs:
        return None, None  # ⚠️ le composant appelant choisira s'il affiche un warning

    options = list(dfs.keys())

    # Auto-sélection si un seul fichier
    if len(options) == 1:
        selected_name = options[0]
        df = dfs[selected_name]
        if isinstance(df, pd.DataFrame):
            st.session_state[df_key] = df
            return df, selected_name
        return None, None

    # Plusieurs fichiers : selectbox persistante
    selected_name = st.selectbox(selector_label, options, key=selector_key)
    df = dfs.get(selected_name)

    if isinstance(df, pd.DataFrame):
        st.session_state[df_key] = df
        return df, selected_name
    return None, None


# ============================ Validation d'étape + snapshot ====================

def _sanitize_snapshot_label(label: str) -> str:
    """
    Snapshot label sûr (lettres/chiffres/underscore). Laisse à snapshot_utils le
    soin d'appliquer sa propre slugification également (défense en profondeur).
    """
    label = (label or "").strip()
    label = label.replace(" ", "_")
    # on autorise [A-Za-z0-9_]
    if not re.fullmatch(r"[A-Za-z0-9_]*", label):
        return ""
    return label or "step_validated"


def mark_step_done(step: str, custom_name: Optional[str] = None, *, df_key: str = "df") -> None:
    """
    Marque une étape comme validée et tente de sauvegarder un snapshot du DF actif.
    - Idempotent : si l'étape est déjà validée, ne fait rien (pas de doublon).
    - Si aucun DataFrame actif n'est disponible, on valide l'étape sans snapshot.

    Args:
        step: identifiant court de l'étape (ex. "jointures").
        custom_name: nom de snapshot optionnel (sans espaces/accents spéciaux).
        df_key: clé dans st.session_state où se trouve le DataFrame actif.
    """
    st.session_state.setdefault("validation_steps", {})

    if st.session_state["validation_steps"].get(step):
        return

    st.session_state["validation_steps"][step] = True

    # Prépare le label de snapshot
    snapshot_label = _sanitize_snapshot_label(custom_name or f"{step}_validated")
    if not snapshot_label:
        st.warning("❌ Nom de snapshot invalide : utilisez uniquement lettres, chiffres et underscores.")
        return

    df = st.session_state.get(df_key)

    try:
        if isinstance(df, pd.DataFrame):
            # ✅ Sauvegarde réelle du DF actif
            save_snapshot(df, label=snapshot_label)
            st.success(f"✅ Étape « {step} » validée et snapshot « {snapshot_label} » sauvegardé.")
        else:
            # Pas de DF actif : on valide sans snapshot
            st.info(f"ℹ️ Étape « {step} » validée, mais aucun DataFrame actif : snapshot non créé.")
    except Exception as e:
        st.error(f"❌ Erreur pendant la sauvegarde du snapshot : {e}")


def validate_step_button(
    step_name: str,
    label: str = "✅ Valider l’étape",
    context_prefix: str = "",
    *,
    df_key: str = "df",
) -> None:
    """
    Affiche un champ + bouton de validation d’étape avec snapshot optionnel.
    Le `context_prefix` assure l'unicité des clés Streamlit si le composant est
    rendu plusieurs fois dans la même page.

    Signature conservée pour compatibilité avec l'existant.
    """
    input_key = f"{context_prefix}name_{step_name}"
    button_key = f"{context_prefix}validate_{step_name}"

    custom = st.text_input(
        f"Nom du snapshot pour l'étape `{step_name}` (optionnel)",
        key=input_key,
    )
    if st.button(label, key=button_key):
        mark_step_done(step_name, custom_name=custom, df_key=df_key)


# ================================== Filtres ====================================

def get_columns_by_dtype(df: pd.DataFrame, dtype: str = "number") -> List[str]:
    """
    Renvoie la liste des colonnes correspondant au type spécifié.
    Exemples de `dtype` : 'number', 'object', 'datetime', 'category', etc.
    """
    
    return df.select_dtypes(include=dtype).columns.tolist()


def filter_dataframe_by_column(df: pd.DataFrame, column: str, value) -> pd.DataFrame:
    """
    Filtre le DataFrame sur une valeur précise d'une colonne (égalité stricte).
    Renvoie `df` inchangé si la colonne n'existe pas.
    """
    if column not in df.columns:
        return df
    return df[df[column] == value]


# ----------- Quelques filtres bonus pratiques (optionnels mais utiles) --------

def filter_contains(df: pd.DataFrame, column: str, substring: str, *, case: bool = False) -> pd.DataFrame:
    """
    Filtre les lignes dont `column` contient `substring` (pour colonnes objet/str).
    """
    if column not in df.columns:
        return df
    return df[df[column].astype("string").str.contains(substring, case=case, na=False)]


def filter_between(df: pd.DataFrame, column: str, left, right, *, inclusive: str = "both") -> pd.DataFrame:
    """
    Filtre les lignes où `left <= column <= right` (numérique ou datetime).
    inclusive: 'both' | 'neither' | 'left' | 'right'
    """
    if column not in df.columns:
        return df
    return df[df[column].between(left, right, inclusive=inclusive)]


def filter_in(df: pd.DataFrame, column: str, values: List) -> pd.DataFrame:
    """
    Filtre les lignes dont la valeur de `column` appartient à `values`.
    """
    if column not in df.columns:
        return df
    return df[df[column].isin(values)]
