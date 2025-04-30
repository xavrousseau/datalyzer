# ============================================================
# Fichier : filters.py
# Objectif : Fonctions utilitaires pour Datalyzer
# Sélection de fichier actif, validation d'étapes, filtrages
# Version robuste sans doublons d'alertes
# ============================================================

import streamlit as st
import pandas as pd
from utils.snapshot_utils import save_snapshot

# ============================================================
# 🔁 Sélecteur du fichier actif
# ============================================================

def get_active_dataframe() -> tuple[pd.DataFrame, str] | tuple[None, None]:
    """
    Permet de sélectionner dynamiquement un fichier chargé via un selectbox.
    Retourne un tuple (DataFrame, nom) si un fichier est actif, sinon (None, None).
    Affiche un warning une seule fois en cas d'absence.
    """
    dfs = st.session_state.get("dfs", {})
    if not dfs:
        return None, None  # ⚡ Warning doit être géré au niveau appelant pour éviter doublon

    options = list(dfs.keys())
    selected = st.selectbox("🗂️ Sélectionner un fichier à analyser :", options, key="global_df_selector")
    df = dfs.get(selected)

    if isinstance(df, pd.DataFrame):
        st.session_state.df = df
        return df, selected
    else:
        return None, None

# ============================================================
# 🧹 Validation d’étape avec bouton et snapshot intelligent
# ============================================================

def mark_step_done(step: str, custom_name: str = None):
    """
    Marque une étape comme validée dans la session et sauvegarde un snapshot.
    Si l'étape est déjà validée, ne fait rien (pas de double warning).
    """
    st.session_state.setdefault("validation_steps", {})

    if st.session_state["validation_steps"].get(step):
        return  # ⚡ Ne spamme pas un warning si déjà validé
    
    st.session_state["validation_steps"][step] = True

    snapshot_label = (custom_name or f"{step}_validated").strip().replace(" ", "_")
    if not snapshot_label.replace("_", "").isalnum():
        st.warning("❌ Nom de snapshot invalide : utilisez uniquement lettres, chiffres et underscores.")
        return

    try:
        save_snapshot(label=snapshot_label)
        st.success(f"✅ Étape '{step}' validée et snapshot '{snapshot_label}' sauvegardé.")
    except Exception as e:
        st.error(f"❌ Erreur pendant la sauvegarde : {e}")

def validate_step_button(step_name: str, label: str = "✅ Valider l’étape", context_prefix: str = ""):
    """
    Affiche un champ + bouton de validation d’étape avec snapshot optionnel.
    Le context_prefix permet d'assurer l'unicité des clés Streamlit.
    """
    custom = st.text_input(
        f"Nom du snapshot pour l'étape `{step_name}` (optionnel)", 
        key=f"{context_prefix}name_{step_name}"
    )
    if st.button(label, key=f"{context_prefix}validate_{step_name}"):
        mark_step_done(step_name, custom_name=custom)

# ============================================================
# 📊 Fonctions de filtrage sur les colonnes
# ============================================================

def get_columns_by_dtype(df: pd.DataFrame, dtype: str = "number") -> list:
    """
    Renvoie la liste des colonnes correspondant au type spécifié ('number', 'object', etc.).
    """
    return df.select_dtypes(include=dtype).columns.tolist()

def filter_dataframe_by_column(df: pd.DataFrame, column: str, value):
    """
    Filtre le DataFrame sur une valeur précise d'une colonne.
    """
    return df[df[column] == value]
