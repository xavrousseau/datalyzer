import streamlit as st
import os

# Étapes d'analyse EDA avec emoji
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
    """Initialise la page et applique le style sombre"""
    st.set_page_config(
        page_title="Datalyzer — Analyse exploratoire zen japonais",
        page_icon="🎴",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Chargement de la police japonaise
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    # Application directe du thème sombre
    dark_theme_path = "assets/style_dark.css"
    if os.path.exists(dark_theme_path):
        with open(dark_theme_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Le thème sombre est introuvable. Apparence par défaut utilisée.")

    # Branding visuel dans la sidebar (logo ou torii ?)
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align: center; padding-bottom: 1rem;'>
                <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Torii_gate_icon_red.svg/96px-Torii_gate_icon_red.svg.png' width='48' />
                <h3 style='margin-top: 0.5rem;'>Datalyzer</h3>
            </div>
            """, unsafe_allow_html=True
        )
