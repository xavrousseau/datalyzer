import streamlit as st
import os
from datetime import datetime

EDA_STEPS = {
    "types": "🧾 Types",
    "missing": "❓ Manquants",
    "histos": "📊 Distributions",
    "outliers": "🚨 Outliers",
    "stats": "📈 Statistiques",
    "cleaning": "🧹 Nettoyage",
    "correlations": "🔗 Corrélations"
}

def configure_app():
    st.set_page_config(
        page_title="Datalyzer — Analyse exploratoire zen japonais",
        page_icon="🎴",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    if "theme" not in st.session_state:
        hour = datetime.now().hour
        st.session_state.theme = "dark" if hour < 7 or hour > 19 else "light"

    theme_file = {
        "light": "assets/style_light.css",
        "dark": "assets/style_dark.css"
    }.get(st.session_state.theme)

    if theme_file and os.path.exists(theme_file):
        with open(theme_file, "r", encoding="utf-8") as f:
            style = f.read()
            st.markdown(f"<style>{style}</style>", unsafe_allow_html=True)
    else:
        st.warning("❗ Le fichier CSS demandé est manquant. Apparence par défaut appliquée.")
