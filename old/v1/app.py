# ============================================================
# Fichier : app.py
# Objectif : Point d’entrée de l’application Datalyzer
# Version corrigée avec navigation dynamique et suivi d’étapes EDA
# ============================================================

import streamlit as st

from config import configure_app, EDA_STEPS
from utils.ui_utils import show_header_image

# 📦 Pages
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
# 🔧 Initialisation de session
# ============================================================
configure_app()

st.session_state.setdefault("page", "home")
st.session_state.setdefault("dfs", {})
st.session_state.setdefault("validation_steps", {})  # ✅ nom unifié

# ============================================================
# 🎛️ Barre latérale : navigation + progression
# ============================================================
def nav_menu():
    with st.sidebar:
        # 🌗 Thème
        st.markdown("### 🎨 Thème d’affichage")
        emoji = "🌞" if st.session_state.theme == "light" else "🌙"
        st.markdown(f"**{emoji} Mode actif : {'Thème clair' if st.session_state.theme == 'light' else 'Thème sombre'}**")

        # 🖼️ Image d’en-tête
        show_header_image("bg_torii_sunrise.png", height=160, alt_text="Torii japonais")

        # 📚 Navigation
        st.markdown("## 🚀 Navigation")
        pages = {
            "🏠 Page d’accueil": "home",
            "📂 Fichiers & Snapshots": "chargement",
            "🔗 Jointures": "jointures",
            "💾 Export": "export",
            "🔍 Exploration": "exploration",
            "🧾 Typage": "typage",
            "💡 Suggestions": "suggestions",
            "🚨 Qualité": "qualite",
            "🧪 Multivariée": "multivariee",
            "📊 Catégorielle": "cat",
            "🎯 Cible": "cible",
            "🚨 Anomalies": "anomalies"
        }

        # 🔘 Boutons avec surbrillance de la page active
        for label, key in pages.items():
            if st.session_state.page == key:
                st.markdown(f"➡️ **{label}**")
            else:
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key

        # 📊 Suivi de progression
        if st.session_state["dfs"]:
            validation = st.session_state["validation_steps"]
            n_total = len(EDA_STEPS)
            n_done = sum(validation.get(k, False) for k in EDA_STEPS)

            st.markdown("### 📊 Progression EDA")
            st.progress(n_done / n_total)
            st.markdown(f"**{n_done} / {n_total} étapes validées ({int(n_done / n_total * 100)}%)**")

            st.markdown("### 📌 Étapes validées")
            for step_key, step_label in EDA_STEPS.items():
                st.write(f"{'✅' if validation.get(step_key) else '🔲'} {step_label}")

            # 🔄 Réinitialisation des étapes
            if st.button("🔄 Réinitialiser l’analyse"):
                confirm = st.radio("❓ Êtes-vous sûr ?", ["Non", "Oui"], key="confirm_reset")
                if confirm == "Oui":
                    st.session_state["validation_steps"] = {}
                    st.success("✔️ Analyse réinitialisée.")

# Affiche le menu dans la sidebar
nav_menu()

# ============================================================
# 🚦 Routage dynamique vers les pages
# ============================================================
page = st.session_state.page

routes = {
    "home": run_home,
    "chargement": run_chargement,
    "jointures": run_jointures,
    "export": run_export,
    "exploration": run_exploration,
    "typage": run_typage,
    "suggestions": run_suggestions,
    "qualite": run_qualite,
    "multivariee": run_multivariee,
    "cat": run_analyse_categorielle,
    "cible": run_cible,
    "anomalies": run_anomalies
}

# Exécution de la page sélectionnée
if page in routes:
    routes[page]()

    # 🎉 Félicitations si toutes les étapes sont validées
    if page in EDA_STEPS and all(st.session_state["validation_steps"].get(k, False) for k in EDA_STEPS):
        st.balloons()
        st.success("🎉 Toutes les étapes EDA sont terminées ! Vous pouvez exporter ou approfondir votre analyse.")
