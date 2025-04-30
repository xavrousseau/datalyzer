# ============================================================
# Fichier : app.py
# Objectif : Point d’entrée de l’application Datalyzer
# ============================================================

import streamlit as st
from config import configure_app
configure_app()

# Utils
from utils.snapshot_utils import save_snapshot
from utils.log_utils import log_action
from utils.filters import select_active_dataframe

# Pages
from sections.home import run_home
from sections.fichiers import run_chargement
from sections.jointures import run_jointures
from sections.export import run_export
from sections.exploration import run_exploration
from sections.typage import run_typage
from sections.suggestions import run_suggestions
from sections.qualite import run_qualite
from sections.multivariee import run_multivariee
from sections.cat_analysis import run_analyse_categorielle
from sections.cible import run_cible
from sections.anomalies import run_anomalies

# ============================================================
# Initialisation de l’état et de la configuration
# ============================================================

 

if "page" not in st.session_state:
    st.session_state.page = "home"

EDA_STEPS = {
    "types": "🧾 Types",
    "missing": "❓ Manquants",
    "histos": "📊 Distributions",
    "outliers": "🚨 Outliers",
    "stats": "📈 Stats",
    "cleaning": "🧹 Nettoyage",
    "correlations": "🔗 Corrélations"
}

# ============================================================
# Barre latérale : Menu de navigation
# ============================================================

def nav_menu():
 
    with st.sidebar:
        st.markdown("---")
        emoji = "🌞" if st.session_state.theme == "light" else "🌙"
        theme_label = "Thème clair" if st.session_state.theme == "light" else "Thème sombre"
        st.markdown(f"**{emoji} Mode actif : {theme_label}**")

        
        st.image("images/bg_torii_sunrise.png", use_container_width=True)
        st.markdown("## 🚀 Navigation")

        st.markdown("### 🏠 Accueil")
        if st.button("🏠 Page d’accueil", use_container_width=True):
            st.session_state.page = "home"

        st.markdown("### 📁 Fichiers")
        if st.button("📂 Fichiers & Snapshots", use_container_width=True):
            st.session_state.page = "chargement"
        if st.button("🔗 Jointures", use_container_width=True):
            st.session_state.page = "jointures"
        if st.button("💾 Export", use_container_width=True):
            st.session_state.page = "export"

        st.markdown("### 🔍 Analyse")
        if st.button("🔍 Exploration", use_container_width=True):
            st.session_state.page = "exploration"
        if st.button("🧾 Typage", use_container_width=True):
            st.session_state.page = "typage"
        if st.button("💡 Suggestions", use_container_width=True):
            st.session_state.page = "suggestions"
        if st.button("🚨 Qualité", use_container_width=True):
            st.session_state.page = "qualite"
        if st.button("🧪 Multivariée", use_container_width=True):
            st.session_state.page = "multivariee"
        if st.button("📊 Catégorielle", use_container_width=True):
            st.session_state.page = "cat"
        if st.button("🎯 Cible", use_container_width=True):
            st.session_state.page = "cible"
        if st.button("🚨 Anomalies", use_container_width=True):
            st.session_state.page = "anomalies"

nav_menu()

# ============================================================
# Barre de progression des étapes EDA
# ============================================================

if "dfs" in st.session_state and st.session_state["dfs"]:
    validation = st.session_state.get("validation_steps", {})
    n_total = len(EDA_STEPS)
    n_done = sum(1 for k in EDA_STEPS if validation.get(k))
    progress_pct = int(n_done / n_total * 100)

    st.sidebar.markdown("### 📊 Progression EDA")
    st.sidebar.progress(progress_pct / 100)
    st.sidebar.markdown(f"**{n_done} / {n_total} étapes validées ({progress_pct}%)**")

    st.sidebar.markdown("### 📌 Étapes validées")
    for key, label in EDA_STEPS.items():
        status = "✅" if validation.get(key) else "🔲"
        st.sidebar.write(f"{status} {label}")

    if st.sidebar.button("🔄 Réinitialiser l’analyse"):
        st.session_state["validation_steps"] = {}
        st.success("✔️ Analyse réinitialisée.")

# ============================================================
# Routage vers les pages
# ============================================================

if st.session_state.page == "home":
    run_home()
elif st.session_state.page == "chargement":
    run_chargement()
elif st.session_state.page == "jointures":
    run_jointures()
elif st.session_state.page == "export":
    if "df" in st.session_state:
        run_export(st.session_state.df)
    else:
        st.warning("❌ Aucune donnée à exporter.")
else:
    df, selected_name = select_active_dataframe()
    st.session_state.df = df

    if st.session_state.page == "exploration":
        run_exploration()
    elif st.session_state.page == "typage":
        run_typage()
    elif st.session_state.page == "suggestions":
        run_suggestions()
    elif st.session_state.page == "qualite":
        run_qualite()
    elif st.session_state.page == "multivariee":
        run_multivariee()
    elif st.session_state.page == "cat":
        run_analyse_categorielle()
    elif st.session_state.page == "cible":
        run_cible()
    elif st.session_state.page == "anomalies":
        run_anomalies()

    all_steps_done = all(st.session_state.get("validation_steps", {}).get(k) for k in EDA_STEPS)
    if all_steps_done:
        st.balloons()
        st.success("🎉 Toutes les étapes EDA sont terminées ! Vous pouvez exporter ou approfondir votre analyse.")
