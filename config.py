# ============================================================
# Fichier : config.py
# Objectif : Configuration globale de l'application Datalyzer
# Thème fixe : sombre uniquement (zen, sobre, stable)
# ============================================================

import streamlit as st
import os

# --- Métadonnées de l'application ---
APP_NAME = "Datalyzer"
SECTIONS_DIR = "sections"
LOGO_PATH = "images/sidebars/japanese-temple.png"

# --- Palette de couleurs sombre (zen & cohérente avec style_dark.css) ---
PALETTE_ZEN = {
    "fond": "#0D0E17",           # Fond sombre principal
    "primaire": "#FF6D99",       # Rose sakura tamisé
    "secondaire": "#88BDBC",     # Vert bambou doux
    "texte": "#E0E0E0",          # Texte clair lisible
    "accent": "#D9CAB3",         # Beige sable
    "fond_section": "#1A1B2B"    # Conteneurs
}

# --- Étapes EDA utilisées dans l'app ---
EDA_STEPS = {
    "types": "Types de variables",
    "missing": "Valeurs manquantes",
    "histos": "Distributions",
    "outliers": "Valeurs extrêmes",
    "stats": "Statistiques descriptives",
    "cleaning": "Nettoyage intelligent",
    "correlations": "Corrélations"
}

# === Fonction d'initialisation de la page ===
def configure_app():
    """
    Configure la page Streamlit avec :
    - titre
    - icône
    - layout large
    - style sombre fixe
    - chargement de la police Noto Sans JP
    """
    st.set_page_config(
        page_title=f"{APP_NAME} — Analyse exploratoire",
        page_icon="🌑",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Chargement du thème sombre CSS
    css_path = "assets/style_dark.css"
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("Fichier style_dark.css introuvable.")

    # Chargement de la police japonaise zen
    st.markdown("""
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)
