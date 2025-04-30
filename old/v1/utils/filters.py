# ============================================================
# Fichier : filters.py
# Objectif : Fonctions utilitaires pour Datalyzer
# Sélection de fichier actif, filtrage, validation d’étapes
# Version enrichie avec validation des entrées et meilleure gestion des erreurs
# ============================================================

import streamlit as st
import pandas as pd
from utils.snapshot_utils import save_snapshot


# ============================================================
# 🔁 Sélecteur du fichier actif
# ============================================================

def get_active_dataframe() -> tuple[pd.DataFrame, str] | tuple[None, None]:
    """
    Affiche un selectbox pour choisir un fichier parmi ceux importés.
    Retourne le DataFrame sélectionné et son nom.
    """
    dfs = st.session_state.get("dfs", {})
    if not dfs:
        st.warning("⚠️ Aucun fichier importé. Merci d'en charger un dans l'onglet Chargement.")
        return None, None

    options = list(dfs.keys())
    selected = st.selectbox("🗂️ Fichier à analyser", options, key="global_df_selector")
    df = dfs.get(selected)

    if isinstance(df, pd.DataFrame):
        st.session_state.df = df  # Mise à jour du fichier actif global
        return df, selected
    else:
        return None, None


# ============================================================
# 🧹 Validation d’étape avec bouton et nom de snapshot
# ============================================================

def mark_step_done(step: str, custom_name: str = None):
    """
    Marque une étape comme validée dans la session Streamlit
    et sauvegarde un snapshot nommé.
    
    Args:
        step (str): Le nom de l'étape à valider.
        custom_name (str): Le nom personnalisé du snapshot (facultatif).
    """
    st.session_state.setdefault("validation_steps", {})
    if step in st.session_state["validation_steps"]:
        st.warning(f"⚠️ L'étape '{step}' a déjà été validée.")
        return  # Empêche la validation si l'étape est déjà validée
    
    st.session_state["validation_steps"][step] = True

    # Validation du nom de snapshot
    if custom_name:
        custom_name = custom_name.strip().replace(" ", "_")  # Remplacer les espaces par des underscores
        if not custom_name.isalnum():
            st.warning("❌ Le nom du snapshot contient des caractères invalides. Utilisez des lettres et chiffres uniquement.")
            return
    else:
        custom_name = f"{step}_validated"
    
    try:
        save_snapshot(label=custom_name)
        st.success(f"✅ Étape '{step}' validée. Snapshot sauvegardé.")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde du snapshot : {e}")


def validate_step_button(step_name: str, label: str = "✅ Valider l’étape", context_prefix: str = ""):
    """
    Affiche un champ de nom de snapshot (optionnel) + bouton de validation.
    Permet de personnaliser la clé pour éviter les doublons dans la page.
    """
    final_key = f"{context_prefix}name_{step_name}"  # On ajoute un contexte pour rendre unique
    custom = st.text_input(f"Nom du snapshot pour l'étape `{step_name}` (optionnel)", key=final_key)

    if st.button(label, key=f"{context_prefix}validate_{step_name}"):
        mark_step_done(step_name, custom_name=custom)


        
# ============================================================
# 📊 Filtrage par type (utilisé dans suggestions ou ciblage)
# ============================================================

def get_columns_by_dtype(df: pd.DataFrame, dtype: str = "number") -> list:
    """
    Retourne la liste des colonnes du DataFrame correspondant à un type pandas donné.
    Exemple : "number", "object", "bool", etc.
    """
    return df.select_dtypes(include=dtype).columns.tolist()


def filter_dataframe_by_column(df: pd.DataFrame, column: str, value):
    """
    Filtre un DataFrame en gardant les lignes où column == value.
    """
    return df[df[column] == value]
