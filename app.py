# ============================================================
# Fichier : app.py
# Objectif : Point d’entrée principal de Datalyzer — Version Pro
# ============================================================

import streamlit as st
from datetime import datetime

from config import configure_app, EDA_STEPS
from utils.ui_utils import show_header_image_safe

# 📦 Import des vraies pages
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

# 🛠️ Initialisation de l’app
configure_app()

# 🧹 Initialisation état
st.session_state.setdefault("page", "home")
st.session_state.setdefault("dfs", {})
st.session_state.setdefault("validation_steps", {})

# 🎴 Sidebar stylée
def nav_menu():
    with st.sidebar:
        show_header_image_safe("sidebars/sidebar_geisha_full.png", height=240)

        st.markdown("## 🎨 Choix du thème")
        choix = st.selectbox("Sélectionnez un thème", ["clair", "sombre", "auto"])
        if choix == "auto":
            hour = datetime.now().hour
            st.session_state.theme = "dark" if hour < 7 or hour > 19 else "light"
        else:
            st.session_state.theme = "light" if choix == "clair" else "dark"

        st.markdown("---")
        st.markdown("## 🏯 Navigation")

        if st.button("🏠 Accueil", use_container_width=True):
            st.session_state.page = "home"

        if st.button("📂 Chargement & Snapshots", use_container_width=True):
            st.session_state.page = "chargement"
        if st.button("🔗 Jointures", use_container_width=True):
            st.session_state.page = "jointures"
        if st.button("💾 Export", use_container_width=True):
            st.session_state.page = "export"

        st.markdown("---")
        st.markdown("## 🔍 Analyse")

        if st.button("🔎 Exploration", use_container_width=True):
            st.session_state.page = "exploration"
        if st.button("🧾 Typage", use_container_width=True):
            st.session_state.page = "typage"
        if st.button("🧪 Qualité", use_container_width=True):
            st.session_state.page = "qualite"
        if st.button("📊 Analyse Multivariée", use_container_width=True):
            st.session_state.page = "multivariee"
        if st.button("🚨 Anomalies", use_container_width=True):
            st.session_state.page = "anomalies"
        if st.button("📋 Analyse Catégorielle", use_container_width=True):
            st.session_state.page = "cat"
        if st.button("🎯 Cible", use_container_width=True):
            st.session_state.page = "cible"
        if st.button("💡 Suggestions", use_container_width=True):
            st.session_state.page = "suggestions"

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

if st.session_state.page in routes:
    routes[st.session_state.page]()
