# ============================================================
# Fichier : state_manager.py
# Objectif : Centraliser la gestion de st.session_state
# ============================================================

import streamlit as st

# --- Valeurs par défaut des variables de session ---
DEFAULT_SESSION_VARS = {
    "df_original": None,           # Données brutes importées
    "df_cleaned": None,            # Données nettoyées
    "file_name": None,             # Nom du fichier chargé
    "last_action": None,           # Dernière action effectuée
    "snapshot_loaded": False,      # Indique si un snapshot a été restauré
    "export_ready": False,         # Si les données sont prêtes à l'export
    "current_section": "Accueil"   # Section sélectionnée par défaut
}

def init_session_state():
    """Initialise toutes les variables globales de session"""
    for key, default in DEFAULT_SESSION_VARS.items():
        if key not in st.session_state:
            st.session_state[key] = default

def set_state(key, value):
    """Met à jour une variable de session"""
    st.session_state[key] = value

def get_state(key):
    """Lit une variable de session"""
    return st.session_state.get(key, None)

def reset_session_state():
    """Réinitialise toutes les variables à leur valeur par défaut"""
    for key, default in DEFAULT_SESSION_VARS.items():
        st.session_state[key] = default
