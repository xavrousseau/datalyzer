# ============================================================
# Fichier : app.py
# Objectif : Point d’entrée principal de l’application Datalyzer
# Version  : sombre uniquement, stable, compatible Docker/Streamlit
# Auteur   : Xavier Rousseau
# ============================================================

import streamlit as st

# --- Config & gestion d'état ---
from config import configure_app
from utils.state_manager import init_session_state, set_state

# --- Sections principales ---
from sections.home import run_home
from sections.fichiers import run_chargement
from sections.jointures import run_jointures
from sections.export import run_export
from sections.exploration import run_exploration
from sections.typage import run_typage
from sections.qualite import run_qualite
from sections.anomalies import run_anomalies
from sections.multivariee import run_multivariee
from sections.cat_analysis import run_analyse_categorielle
from sections.cible import run_cible
from sections.suggestions import run_suggestions
from sections.sql_lab import render as run_sql_lab

# ============================================================
# 1) CONFIGURATION GLOBALE
# ============================================================

st.set_page_config(
    page_title="Datalyzer",
    page_icon=":shinto_shrine:",
    layout="wide",                 # mode large → responsive
    initial_sidebar_state="expanded"
)

# Init session (dictionnaire interne pour conserver l’état)
init_session_state()

# Configuration app (styles globaux, couleurs, etc.)
configure_app()


# ============================================================
# 2) ROUTES — dictionnaire nom → fonction associée
# ============================================================

routes = {
    "Accueil": run_home,
    "Chargement": run_chargement,
    "Jointures": run_jointures,
    "Export": run_export,
    "Qualité": run_qualite,
    "Exploration": run_exploration,
    "SQL Lab": run_sql_lab, 
    "Typage": run_typage,
    "Anomalies": run_anomalies,
    "Analyse multivariée": run_multivariee,
    "Analyse catégorielle": run_analyse_categorielle,
    "Analyse cible": run_cible,
    "Suggestions": run_suggestions,
}


# ============================================================
# 3) BARRE LATÉRALE
# ============================================================

def nav_menu():
    """Affiche le menu latéral avec logo, navigation et signature."""
    with st.sidebar:
        # --- Logo ou image décorative ---
        st.image(
            "static/images/sidebars/japanese-temple.png",
            width=200
        )

        st.markdown("---")

        # --- Style du selecteur de pages (CSS inline) ---
        st.markdown(
            """
            <style>
                div[data-baseweb="select"] span {
                    font-size: 14px !important;
                }
                label[for="Choisissez une section"] {
                    font-size: 14px !important;
                    font-weight: 600;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        # --- Navigation principale ---
        st.markdown("#### Navigation")
        module_names = list(routes.keys())
        default_page = st.session_state.get("page", "Accueil")

        selected_module = st.selectbox(
            "Choisissez une section",
            module_names,
            index=module_names.index(default_page)
        )
        set_state("page", selected_module)

        # --- Signature ---
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; font-size:12px; color:gray;'>"
            "Datalyzer – © Xavier Rousseau</p>",
            unsafe_allow_html=True
        )


# ============================================================
# 4) ROUTAGE
# ============================================================

# Menu latéral
nav_menu()

# Page active
active_page = st.session_state.get("page", "Accueil")
selected_function = routes.get(active_page)

if selected_function:
    selected_function()
else:
    st.warning(f"La page « {active_page} » n'est pas disponible.")
