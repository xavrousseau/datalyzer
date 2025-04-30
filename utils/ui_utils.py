# ============================================================
# Fichier : ui_utils.py
# Objectif : Fonctions d’interface graphique pour Datalyzer
# Version enrichie avec animation, footer dynamique et plus de personnalisation
# ============================================================

import streamlit as st
import base64
import os
from datetime import datetime

# ============================================================
# 🖼️ Affichage de bannière (image en en-tête avec animation)
# ============================================================

def show_header_image(image_name: str, height: int = 200, alt_text: str = "Bannière Datalyzer", fadein: bool = True):
    """
    Affiche une image de bannière depuis le dossier `images/` avec un effet d'apparition progressif.
    
    Args:
    - image_name (str): Le nom du fichier image.
    - height (int): Hauteur de l'image.
    - alt_text (str): Texte alternatif pour l'image.
    - fadein (bool): Activer ou non l'animation fadein.
    """
    image_path = os.path.join("images", image_name)
    fallback_path = os.path.join("images", "default.png")

    if not os.path.exists(image_path):
        if os.path.exists(fallback_path):
            image_path = fallback_path
        else:
            st.info("📭 Aucune image de bannière disponible (ni principale ni fallback).")
            return

    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            fadein_style = "animation: fadein 2s ease-in-out;" if fadein else ""
            st.markdown(f"""
                <div role="img" aria-label="{alt_text}" style="
                    height: {height}px;
                    background-image: url('data:image/png;base64,{data}');
                    background-size: cover;
                    background-position: center;
                    border-radius: 10px;
                    margin-bottom: 1.5rem;
                    {fadein_style}
                "></div>
                <style>
                    @keyframes fadein {{
                        0% {{opacity: 0;}}
                        100% {{opacity: 1;}}
                    }}
                </style>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de l’image : {e}")

# ============================================================
# 🖼️ Affichage sûr d'une image (vérifie existence avant affichage)
# ============================================================

def show_header_image_safe(image_name: str, height: int = 200, alt_text: str = "Bannière Datalyzer", fadein: bool = True):
    """
    Affiche une image uniquement si elle existe, sinon ne rien afficher.
    Utile pour éviter les erreurs en cas de fichier manquant.
    
    Args:
    - image_name (str): Le nom du fichier image.
    - height (int): Hauteur de l'image.
    - alt_text (str): Texte alternatif pour accessibilité.
    - fadein (bool): Active une animation d'apparition douce.
    """
    image_path = os.path.join("images", image_name)
    if os.path.exists(image_path):
        show_header_image(image_name, height=height, alt_text=alt_text, fadein=fadein)
    else:
        pass  # Pas d'erreur, on reste discret

# ============================================================
# 🧭 En-tête stylisé avec emoji + titre + sous-titre
# ============================================================

def show_icon_header(emoji: str, title: str, subtitle: str = "", title_size: str = "1.8rem"):
    """
    Affiche un en-tête élégant avec emoji, titre principal et sous-titre optionnel.
    
    Args:
    - emoji (str): Emoji pour le titre.
    - title (str): Titre principal.
    - subtitle (str): Sous-titre optionnel.
    - title_size (str): Taille du titre.
    """
    st.markdown(f"""
        <div style="margin-top: 1rem; margin-bottom: 1.5rem;">
            <h1 style="font-size: {title_size}; font-weight: 700; margin-bottom: 0.3rem;">
                {emoji} {title}
            </h1>
            {"<p style='font-size: 1.05rem; color: #777;'>" + subtitle + "</p>" if subtitle else ""}
        </div>
    """, unsafe_allow_html=True)


# ============================================================
# 📊 Barre de progression horizontale des étapes EDA
# ============================================================

def show_eda_progress(steps_dict: dict, status_dict: dict):
    """
    Affiche une barre de progression des étapes EDA.

    Args:
        steps_dict (dict): {code étape: label affiché}
        status_dict (dict): {code étape: booléen validé}
    """
    total = len(steps_dict)
    done = sum(status_dict.get(k, False) for k in steps_dict)
    ratio = done / total if total else 0

    st.markdown("### 📊 Progression EDA")
    st.progress(ratio)

    cols = st.columns(total)
    for idx, (code, label) in enumerate(steps_dict.items()):
        icon = "✅" if status_dict.get(code) else "🔲"
        cols[idx].markdown(f"{icon} {label}")


# ============================================================
# 🔻 Footer de l'application (dynamique)
# ============================================================

def show_footer(author: str = "Xavier Rousseau", github: str = "", version: str = "1.0"):
    """
    Affiche un pied de page avec l’auteur, la version et un lien GitHub (optionnel).
    
    Args:
    - author (str): Auteur de l’application.
    - github (str): Lien GitHub (facultatif).
    - version (str): Version de l’application.
    """
    st.markdown("---")
    today = datetime.today().strftime("%Y-%m-%d")
    github_link = f" • [github.com/{github}]({github})" if github else ""
    st.markdown(f"""
        <div style="text-align: center; font-size: 0.9rem; color: #888; margin-top: 2rem;">
            🧪 Datalyzer v{version} — par {author} — {today}{github_link}
        </div>
    """, unsafe_allow_html=True)
