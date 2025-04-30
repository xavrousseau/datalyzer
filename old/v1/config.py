# ============================================================
# Fichier : config.py
# Objectif : Configuration initiale de Datalyzer (thème, layout, style)
# Version améliorée avec personnalisation du thème et gestion des polices
# ============================================================

import streamlit as st
import os
from datetime import datetime

# ============================================================
# 🔁 Étapes EDA centralisées
# ============================================================
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
# 🎨 Configuration globale + thème + style
# ============================================================

def configure_app():
    st.set_page_config(
        page_title="Datalyzer – EDA Exploratoire et Zen",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Police Google
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    # Thème interne (dark / light)
    if "theme" not in st.session_state:
        hour = datetime.now().hour
        st.session_state.theme = "dark" if hour < 7 or hour > 19 else "light"

    with st.sidebar:
        st.markdown("### 🎨 Thème d’affichage")

        # === Mapping affiché ↔ interne ===
        theme_mapping = {
            "light": "clair",
            "dark": "sombre",
            "auto": "auto"
        }
        reverse_mapping = {v: k for k, v in theme_mapping.items()}

        current_theme = st.session_state.get("theme", "auto")
        current_display = theme_mapping.get(current_theme, "auto")
        index = ["clair", "sombre", "auto"].index(current_display)

        # === Interface utilisateur ===
        theme_choice = st.radio("Choisissez un thème", options=["clair", "sombre", "auto"], index=index)

        if theme_choice == "auto":
            hour = datetime.now().hour
            st.session_state.theme = "dark" if hour < 7 or hour > 19 else "light"
        else:
            st.session_state.theme = reverse_mapping[theme_choice]

    # === Application du style CSS ===
    css_file_map = {
        "light": "assets/style_light.css",
        "dark": "assets/style_dark.css"
    }
    css_file = css_file_map.get(st.session_state.theme)

    if css_file and os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Le fichier {css_file} est manquant. Apparence par défaut activée.")
