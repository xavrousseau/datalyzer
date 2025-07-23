# ============================================================
# Fichier : sections/home.py
# Objectif : Page d’accueil professionnelle, claire et zen
# Auteur : Xavier Rousseau
# ============================================================

import streamlit as st
from PIL import Image
from io import BytesIO
import base64
from utils.ui_utils import show_footer
from config import APP_NAME, PALETTE_ZEN


def run_home():
    """Affiche la page d'accueil principale de l'application Datalyzer"""

    # === Chargement + centrage HTML de l'image ===
    image_path = "static/images/headers/hearder_temple.png"
    try:
        img = Image.open(image_path).resize((900, 220))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        base64_img = base64.b64encode(buffer.getvalue()).decode()

        st.markdown(
            f"""
            <div style='display: flex; justify-content: center; margin-bottom: 2rem;'>
                <img src="data:image/png;base64,{base64_img}" alt="Bannière Datalyzer" 
                     style="border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);" />
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"❌ Erreur d’image d’accueil : {e}")
        
    # === Titre principal et baseline ===
    st.markdown(f"""
        <h1 style='color:{PALETTE_ZEN["primaire"]}; margin-bottom: 0.5rem;'>
            {APP_NAME}
        </h1>
        <p style='font-size: 16px; color:{PALETTE_ZEN["texte"]}; margin-top: 0;'>
            Une plateforme sobre et efficace pour explorer, nettoyer et structurer vos données tabulaires.
        </p>
        <p style='font-size: 13px; color: {PALETTE_ZEN['texte']}'>
            Utilisez le menu à gauche pour accéder aux différentes sections.
        </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # === Titre de la section principale ===
    st.markdown("### Aperçu de l'application")

    # === Création de 3 colonnes équilibrées ===
    col1, col2, col3 = st.columns(3)

    # ------------------------------------------------------------
    # Colonne 1 — Fonctionnalités principales
    # ------------------------------------------------------------
    with col1:
        st.markdown(f"""
            <div style="background-color: {PALETTE_ZEN['fond_section']};
                        border-radius: 10px;
                        padding: 1rem;
                        box-shadow: 0 1px 6px rgba(0,0,0,0.06);">
                <h4 style="color:{PALETTE_ZEN['secondaire']}; margin-top:0;">Fonctionnalités principales</h4>
                <ul style="line-height: 1.6; font-size: 15px; color: {PALETTE_ZEN['texte']}">
                    <li>Import : <code>CSV</code>, <code>Excel</code>, <code>JSON</code>, <code>Parquet</code></li>
                    <li>Exploration des variables et distributions</li>
                    <li>Nettoyage automatique (vides, doublons, typage)</li>
                    <li>Analyses multivariées : ACP, clustering, corrélations</li>
                    <li>Suggestions automatiques de préparation</li>
                    <li>Export multi-format des données nettoyées</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # ------------------------------------------------------------
    # Colonne 2 — Données : chargement, fusion, export
    # ------------------------------------------------------------
    with col2:
        st.markdown(f"""
            <div style="background-color: {PALETTE_ZEN['fond_section']};
                        border-radius: 10px;
                        padding: 1rem;
                        box-shadow: 0 1px 6px rgba(0,0,0,0.06);">
                <h4 style="color:{PALETTE_ZEN['secondaire']}; margin-top:0;">Données</h4>
                <ul style="line-height: 1.5; font-size: 14px; color:{PALETTE_ZEN['texte']}">
                    <li><strong>Chargement</strong> : fichiers .csv, .xlsx, .parquet</li>
                    <li><strong>Jointures</strong> : fusion intelligente</li>
                    <li><strong>Export</strong> : formats multiples</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # ------------------------------------------------------------
    # Colonne 3 — Analyse : exploration, qualité, suggestions
    # ------------------------------------------------------------
    with col3:
        st.markdown(f"""
            <div style="background-color: {PALETTE_ZEN['fond_section']};
                        border-radius: 10px;
                        padding: 1rem;
                        box-shadow: 0 1px 6px rgba(0,0,0,0.06);">
                <h4 style="color:{PALETTE_ZEN['secondaire']}; margin-top:0;">Analyse</h4>
                <ul style="line-height: 1.5; font-size: 14px; color:{PALETTE_ZEN['texte']}">
                    <li><strong>Exploration</strong> : types, manquants, distributions</li>
                    <li><strong>Typage</strong> : correction semi-automatique</li>
                    <li><strong>Qualité</strong> : doublons, erreurs, placeholders</li>
                    <li><strong>Multivariée</strong> : ACP, Cramér's V, clustering</li>
                    <li><strong>Cible / Catégorielle</strong> : variables cibles</li>
                    <li><strong>Suggestions</strong> : colonnes à encoder ou exclure</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    # === Pied de page ===
    show_footer(author="Xavier Rousseau", github="xsorouz", version="1.0")
