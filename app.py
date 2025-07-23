# ============================================================
# Fichier : app.py
# Objectif : Point d’entrée principal de l’application Datalyzer
# Version : sombre uniquement, stable, compatible Docker/Streamlit
# Auteur : Xavier Rousseau
# ============================================================

import streamlit as st
from config import configure_app
from utils.state_manager import init_session_state, set_state

# === Import des modules fonctionnels ===
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

# === Initialisation de l'état global (session) ===
init_session_state()

# === Configuration globale de l'application ===
configure_app()

# === Dictionnaire de navigation : nom → fonction associée ===
routes = {
    "Accueil": run_home,
    "Chargement": run_chargement,
    "Jointures": run_jointures,
    "Export": run_export,
    "Exploration": run_exploration,
    "Typage": run_typage,
    "Qualité": run_qualite,
    "Anomalies": run_anomalies,
    "Analyse multivariée": run_multivariee,
    "Analyse catégorielle": run_analyse_categorielle,
    "Analyse cible": run_cible,
    "Suggestions": run_suggestions
}

# === Barre latérale de navigation ===
def nav_menu():
    with st.sidebar:
        # --- Image décorative (remplace l'ancien <img src="...">) ---
        st.image(
            "static/images/sidebars/thumb_manga_flashy.png",
            width=200,
            caption=None
        )

        st.markdown("---")

        # --- Style réduit pour le sélecteur de pages ---
        st.markdown("""
            <style>
                div[data-baseweb="select"] span {
                    font-size: 14px !important;
                }
                label[for="Choisissez une section"] {
                    font-size: 14px !important;
                    font-weight: 600;
                }
            </style>
        """, unsafe_allow_html=True)

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

        # --- Signature bas de menu ---
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; font-size:12px; color:gray;'>"
            "Datalyzer – © Xavier Rousseau</p>",
            unsafe_allow_html=True
        )

# === Affichage du menu latéral ===
nav_menu()

# === Exécution de la page sélectionnée ===
active_page = st.session_state.get("page", "Accueil")
selected_function = routes.get(active_page)

if selected_function:
    selected_function()
else:
    st.warning(f"La page « {active_page} » n'est pas disponible.")
