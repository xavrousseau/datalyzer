# config.py

import streamlit as st
import os
from datetime import datetime

def configure_app():
    st.set_page_config(
        page_title="Datalyzer – EDA Exploratoire et Zen",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    if "theme" not in st.session_state:
        hour = datetime.now().hour
        st.session_state.theme = "dark" if hour < 7 or hour > 19 else "light"

    with st.sidebar:
        st.markdown("### 🎨 Thème d’affichage")
        theme_choice = st.radio("Choisissez un thème", options=["clair", "sombre", "auto"], index=0 if st.session_state.theme == "light" else 1 if st.session_state.theme == "dark" else 2)

        if theme_choice == "auto":
            hour = datetime.now().hour
            st.session_state.theme = "dark" if hour < 7 or hour > 19 else "light"
        elif theme_choice == "clair":
            st.session_state.theme = "light"
        elif theme_choice == "sombre":
            st.session_state.theme = "dark"

    css_file = f"assets/style_{st.session_state.theme}.css"
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Le fichier {css_file} est manquant. L'apparence par défaut sera utilisée.")
