# ============================================================
# Fichier : ui_utils.py
# Objectif : Fonctions d’interface graphique pour Datalyzer
# Version : stable, compatible local/cloud, thème sombre
# Auteur : Xavier Rousseau
# ============================================================

import streamlit as st
import os
from datetime import datetime

# ============================================================
# 🖼️ Affiche une image d’en-tête si elle existe
# ============================================================

def show_header_image_safe(relative_path: str, height: int = 220, caption: str = None):
    """
    Affiche une image d’en-tête depuis le dossier static/.

    Args:
        relative_path (str): Chemin relatif (ex: "images/headers/header.png")
        height (int): Hauteur de l’image en pixels
        caption (str): Texte alternatif ou descriptif
    """
    full_path = os.path.join("static", relative_path)
    if os.path.exists(full_path):
        st.image(full_path, use_column_width=True, caption=caption)
    else:
        st.info("Aucune image d’en-tête trouvée.")

# ============================================================
# 🧭 Affiche un en-tête stylisé avec titre + sous-titre
# ============================================================

def show_icon_header(title: str, subtitle: str = "", title_size: str = "1.8rem", align: str = "center"):
    """
    Affiche un bloc titre/sous-titre élégant, centré ou aligné à gauche.

    Args:
        title (str): Titre principal
        subtitle (str): Sous-titre facultatif
        title_size (str): Taille CSS du titre
        align (str): Alignement : 'left', 'center', 'right'
    """
    st.markdown(f"""
        <div style="text-align: {align}; margin-bottom: 2rem;">
            <h1 style="font-size: {title_size}; font-weight: 700; color: #FF6D99; margin-bottom: 0.3rem;">
                {title}
            </h1>
            {"<p style='font-size: 1rem; color: #AAA;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# 📊 Affiche la progression des étapes EDA
# ============================================================

def show_eda_progress(steps_dict: dict, status_dict: dict):
    """
    Affiche une barre de progression des étapes d'analyse.

    Args:
        steps_dict (dict): {étape: nom lisible}
        status_dict (dict): {étape: booléen validé}
    """
    total = len(steps_dict)
    done = sum(status_dict.get(k, False) for k in steps_dict)
    ratio = done / total if total > 0 else 0

    st.markdown("### Progression EDA")
    st.progress(ratio)

    cols = st.columns(total)
    for idx, (code, label) in enumerate(steps_dict.items()):
        icon = "✅" if status_dict.get(code) else "🔲"
        cols[idx].markdown(f"{icon} {label}")

# ============================================================
# 🔻 Affiche le pied de page de l'application
# ============================================================

def show_footer(author: str = "Xavier Rousseau", github: str = "xsorouz", version: str = "1.0"):
    """
    Affiche un footer sobre avec auteur, version, date et GitHub.

    Args:
        author (str): Nom de l’auteur
        github (str): Identifiant GitHub
        version (str): Version actuelle de l’app
    """
    st.markdown("---")
    today = datetime.today().strftime("%Y-%m-%d")
    st.markdown(f"""
        <div style="text-align: center; font-size: 0.9rem; color: #888; margin-top: 2rem;">
            Datalyzer v{version} — par {author} — {today} • 
            <a href='https://github.com/{github}' target='_blank'>github.com/{github}</a>
        </div>
    """, unsafe_allow_html=True)
