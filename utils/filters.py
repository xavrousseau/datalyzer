# utils/filters.py
import pandas as pd
import streamlit as st


def filter_duplicates(df: pd.DataFrame, cols: list[str] = None) -> pd.DataFrame:
    """
    Retourne les lignes dupliquées dans un DataFrame.
    Si `cols` est fourni, utilise uniquement ces colonnes pour détecter les doublons.
    """
    if cols:
        return df[df.duplicated(subset=cols, keep=False)]
    return df[df.duplicated(keep=False)]


def remove_duplicates(df: pd.DataFrame, cols: list[str] = None) -> pd.DataFrame:
    """
    Supprime les doublons du DataFrame.
    Si `cols` est fourni, supprime les doublons en se basant sur ces colonnes.
    """
    return df.drop_duplicates(subset=cols if cols else None)


def filter_columns(df: pd.DataFrame, cols_to_keep: list[str]) -> pd.DataFrame:
    """
    Ne garde que les colonnes spécifiées dans `cols_to_keep`.
    """
    return df[cols_to_keep]


def drop_columns(df: pd.DataFrame, cols_to_drop: list[str]) -> pd.DataFrame:
    """
    Supprime les colonnes spécifiées dans `cols_to_drop` du DataFrame.
    """
    return df.drop(columns=cols_to_drop, errors="ignore")


def get_duplicate_summary(df: pd.DataFrame, cols: list[str] = None) -> dict:
    """
    Retourne un résumé des doublons détectés :
    - nombre total de lignes
    - nombre de doublons
    - pourcentage de doublons
    """
    total = len(df)
    dupes = filter_duplicates(df, cols)
    n_dupes = len(dupes)
    pct = round((n_dupes / total) * 100, 2) if total > 0 else 0.0
    return {"total": total, "duplicates": n_dupes, "percent": pct}

def select_active_dataframe():
    all_dfs = st.session_state.get("dfs", {})
    if not all_dfs:
        st.warning("❌ Aucun fichier chargé.")
        st.stop()
    selected_name = st.selectbox("📁 Choisissez un fichier à analyser", list(all_dfs.keys()), key="global_df_selector")
    st.session_state["df"] = all_dfs[selected_name]
    return all_dfs[selected_name], selected_name

