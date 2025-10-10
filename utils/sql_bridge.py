# ============================================================
# Fichier : utils/sql_bridge.py
# Objectif : Pont entre les sections et le SQL Lab
#            - exposer un DataFrame comme table SQL (miroir)
#            - reconstruire le miroir à partir des fichiers chargés
# Auteur   : Xavier Rousseau
# ============================================================

from __future__ import annotations

import os
import re
from typing import Dict

import pandas as pd
import streamlit as st

# Clés de session communes à l'app
KEY_DFS = "dfs"            # dict[str, pd.DataFrame] — fichiers/snapshots chargés
KEY_DF = "df"              # pd.DataFrame — fichier actif global (optionnel ici)
SQL_DATASETS = "datasets"  # dict[str, pd.DataFrame] — tables vues par le SQL Lab

_SANITIZE_RE = re.compile(r"[^\w\-\.]+")


# ------------------------- utilitaires internes -------------------------

def _sanitize_table_name(name: str) -> str:
    """
    Produit un nom de table "safe" (minuscules, espaces/accents -> '_', sans extension).
    NOTE : côté exécution SQL on *quote* les identifiants, mais ce nom lisible
    évite les surprises dans les menus déroulants.
    """
    base = os.path.splitext(str(name).strip().lower())[0]
    return _SANITIZE_RE.sub("_", base).replace(".", "_")


def _ensure_sql_mirror() -> None:
    """Garantit l'existence du miroir SQL dans la session."""
    st.session_state.setdefault(SQL_DATASETS, {})
    st.session_state.setdefault(KEY_DFS, {})


# ----------------------------- API publique ------------------------------

def expose_to_sql_lab(name: str, df: pd.DataFrame, *, make_active: bool = False) -> str:
    """
    Expose un DataFrame comme TABLE SQL dans le SQL Lab.
    - L'enregistre (ou met à jour) côté fichiers (KEY_DFS) sous le nom brut `name`
    - Crée/Met à jour la table miroir (SQL_DATASETS) sous un nom "safe"
    - Option make_active : met aussi à jour KEY_DF (fichier actif global)
    Retourne le nom de TABLE créé dans le miroir (utile pour afficher un message).
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise TypeError("expose_to_sql_lab attend un pandas.DataFrame non nul")

    _ensure_sql_mirror()

    # 1) côté application : historiser le DF dans le pool global
    st.session_state[KEY_DFS][name] = df
    if make_active:
        st.session_state[KEY_DF] = df

    # 2) côté SQL Lab : publier dans le miroir (nom 'safe' pour la liste)
    table = _sanitize_table_name(name)
    st.session_state[SQL_DATASETS][table] = df

    return table


def remove_from_sql_lab(name_or_table: str) -> bool:
    """
    Retire une table du miroir SQL.
    - Accepte soit le nom brut (fichier) soit déjà le nom 'safe' (table).
    - Ne touche pas aux données sources (KEY_DFS).
    Retourne True si suppression dans le miroir, False sinon.
    """
    _ensure_sql_mirror()
    # essaie d'abord comme table 'safe'
    if name_or_table in st.session_state[SQL_DATASETS]:
        del st.session_state[SQL_DATASETS][name_or_table]
        return True
    # sinon, essaie depuis le nom brut
    safe = _sanitize_table_name(name_or_table)
    if safe in st.session_state[SQL_DATASETS]:
        del st.session_state[SQL_DATASETS][safe]
        return True
    return False


def refresh_sql_mirror_from_files() -> Dict[str, pd.DataFrame]:
    """
    Reconstruit complètement le miroir SQL (datasets) à partir de KEY_DFS.
    - Utile quand plusieurs sections ont modifié/ajouté des DataFrames.
    - Ne change pas KEY_DF (actif global).
    Retourne le dict (copie) des tables publiées.
    """
    _ensure_sql_mirror()
    st.session_state[SQL_DATASETS].clear()

    for fname, fdf in (st.session_state.get(KEY_DFS, {}) or {}).items():
        table = _sanitize_table_name(fname)
        st.session_state[SQL_DATASETS][table] = fdf

    # renvoie une copie (lecture)
    return dict(st.session_state[SQL_DATASETS])
