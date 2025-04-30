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
    """
    Permet à l'utilisateur de choisir un fichier actif parmi ceux déjà chargés.
    Affiche un bouton de validation explicite.
    Retourne le DataFrame sélectionné et son nom uniquement après validation.
    """
    all_dfs = st.session_state.get("dfs", {})

    if not all_dfs:
        st.warning("⚠️ Aucun fichier n'a été chargé.")
        st.stop()

    filenames = list(all_dfs.keys())

    selected_name = st.selectbox(
        "📁 Choisissez un fichier à analyser :",
        filenames,
        key="global_df_selector"
    )

    # Affiche les dimensions et un aperçu
    df_preview = all_dfs[selected_name]
    st.info(f"📄 `{selected_name}` – {df_preview.shape[0]} lignes × {df_preview.shape[1]} colonnes")
    st.dataframe(df_preview.head(5), use_container_width=True)

    # Bouton explicite de validation
    if st.button("✅ Valider ce fichier"):
        st.session_state["df"] = df_preview
        st.success(f"✅ Fichier sélectionné : `{selected_name}`")
        return df_preview, selected_name

    # Ne retourne rien tant que non validé
    return None, None
