# ============================================================
# Fichier : app.py
# Objectif : Point d’entrée principal de Datalyzer — Version Pro & Zen
# ============================================================

import streamlit as st
from config import configure_app, EDA_STEPS
from utils.ui_utils import show_header_image_safe

# 📦 Import des pages fonctionnelles
from sections.home import run_home
from sections.exploration import run_exploration
from sections.typage import run_typage
from sections.qualite import run_qualite
from sections.multivariee import run_multivariee
from sections.anomalies import run_anomalies
from sections.cat_analysis import run_analyse_categorielle
from sections.cible import run_cible
from sections.fichiers import run_chargement
from sections.jointures import run_jointures
from sections.export import run_export
from sections.suggestions import run_suggestions

# 🛠️ Configuration globale de l'application
configure_app()

# 🔁 État global
st.session_state.setdefault("page", "home")
st.session_state.setdefault("dfs", {})
st.session_state.setdefault("validation_steps", {})

# 🧭 Menu de navigation
def nav_menu():
    with st.sidebar:
        # ✅ Logo + titre centré (sans doublon)
        st.markdown("""
            <div style="text-align: center; padding-top: 1.2rem;">
                <img src="images/sidebars/japanese-temple.png" width="100" style="border-radius: 8px; margin-bottom: 0.6rem;" />
                <div style="font-size: 16px; font-weight: bold; color: #FF6D99;">Datalyzer</div>
            </div>
        """, unsafe_allow_html=True)

        # 📁 Bloc Données
        st.markdown("### Données")
        if st.button("Chargement & Snapshots", use_container_width=True):
            st.session_state.page = "chargement"
        if st.button("Jointures", use_container_width=True):
            st.session_state.page = "jointures"
        if st.button("Export", use_container_width=True):
            st.session_state.page = "export"

        st.markdown("---")

        # 📊 Bloc Analyse
        st.markdown("### Analyse exploratoire")
        if st.button("Accueil", use_container_width=True):
            st.session_state.page = "home"
        if st.button("Exploration", use_container_width=True):
            st.session_state.page = "exploration"
        if st.button("Typage", use_container_width=True):
            st.session_state.page = "typage"
        if st.button("Qualité", use_container_width=True):
            st.session_state.page = "qualite"
        if st.button("Analyse multivariée", use_container_width=True):
            st.session_state.page = "multivariee"
        if st.button("Anomalies", use_container_width=True):
            st.session_state.page = "anomalies"
        if st.button("Analyse catégorielle", use_container_width=True):
            st.session_state.page = "cat"
        if st.button("Cible", use_container_width=True):
            st.session_state.page = "cible"
        if st.button("Suggestions", use_container_width=True):
            st.session_state.page = "suggestions"

        # 🔻 Footer
        st.markdown("<hr style='border:1px solid #333;'>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center; font-size:12px; color:gray;'>"
            "Datalyzer v1.0 – © Xavier Rousseau</p>",
            unsafe_allow_html=True
        )

# 🔄 Affichage menu
nav_menu()

# 🚀 Routing
routes = {
    "home": run_home,
    "chargement": run_chargement,
    "jointures": run_jointures,
    "export": run_export,
    "exploration": run_exploration,
    "typage": run_typage,
    "qualite": run_qualite,
    "multivariee": run_multivariee,
    "anomalies": run_anomalies,
    "cat": run_analyse_categorielle,
    "cible": run_cible,
    "suggestions": run_suggestions
}

# 🧭 Exécution de la page active
if st.session_state.page in routes:
    routes[st.session_state.page]()
