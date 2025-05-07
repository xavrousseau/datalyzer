# ============================================================
# Fichier : ui_utils.py
# Objectif : Fonctions d’interface graphique pour Datalyzer
# Version finale : bannière, header, footer, progression
# ============================================================

import streamlit as st
import base64
import os
from datetime import datetime

# ============================================================
# 🖼️ Affichage de bannière principale avec animation douce
# ============================================================

def show_header_image(image_name: str, height: int = 200, alt_text: str = "Bannière Datalyzer", fadein: bool = True):
    """
    Affiche une image depuis le dossier `images/` en tant que bannière principale,
    avec effet fade-in stylisé.

    Args:
        image_name (str): Nom du fichier image relatif à 'images/'.
        height (int): Hauteur en pixels.
        alt_text (str): Texte alternatif.
        fadein (bool): Active l'animation d'apparition douce.
    """
    image_path = os.path.join("images", image_name)
    fallback_path = os.path.join("images", "default.png")

    if not os.path.exists(image_path):
        image_path = fallback_path if os.path.exists(fallback_path) else None

    if not image_path:
        st.info("📭 Aucune image de bannière disponible.")
        return

    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            fadein_style = "animation: fadein 1.2s ease-in-out;" if fadein else ""

            st.markdown(f"""
                <div role="img" aria-label="{alt_text}" style="
                    height: {height}px;
                    background-image: url('data:image/png;base64,{data}');
                    background-size: cover;
                    background-position: center;
                    border-radius: 12px;
                    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
                    margin-bottom: 2rem;
                    {fadein_style}
                ">
                </div>
                <style>
                    @keyframes fadein {{
                        from {{ opacity: 0; transform: translateY(-10px); }}
                        to {{ opacity: 1; transform: translateY(0); }}
                    }}
                </style>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de l’image : {e}")


# ============================================================
# 🖼️ Version sécurisée : affiche l’image uniquement si elle existe
# ============================================================

def show_header_image_safe(image_name: str, height: int = 200, alt_text: str = "Bannière Datalyzer", fadein: bool = True):
    """
    Affiche une image uniquement si elle existe, sinon ne rien afficher.
    
    Args:
        image_name (str): Le nom du fichier image dans `images/`.
        height (int): Hauteur de l'image.
        alt_text (str): Texte alternatif pour accessibilité.
        fadein (bool): Active une animation d'apparition douce.
    """
    image_path = os.path.join("images", image_name)
    if os.path.exists(image_path):
        show_header_image(image_name, height=height, alt_text=alt_text, fadein=fadein)


# ============================================================
# 🧭 En-tête stylisé avec titre + sous-titre (optionnel)
# ============================================================

def show_icon_header(title: str, subtitle: str = "", title_size: str = "1.8rem", align: str = "center"):
    """
    Affiche un bloc titre / sous-titre centré ou aligné gauche, propre et élégant.

    Args:
        title (str): Titre principal.
        subtitle (str): Sous-titre facultatif.
        title_size (str): Taille CSS du titre.
        align (str): 'left', 'center' ou 'right'.
    """
    st.markdown(f"""
        <div style="text-align: {align}; margin-bottom: 2rem;">
            <h1 style="font-size: {title_size}; font-weight: 700; margin-bottom: 0.4rem; color: #E0E6F8;">
                {title}
            </h1>
            {"<p style='font-size: 1rem; color: #AAA;'>" + subtitle + "</p>" if subtitle else ""}
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
# 🔻 Footer de l'application
# ============================================================

def show_footer(author: str = "Xavier Rousseau", github: str = "", version: str = "1.0"):
    """
    Affiche un pied de page avec l’auteur, la version et un lien GitHub (optionnel).
    
    Args:
        author (str): Auteur de l’application.
        github (str): Lien GitHub (facultatif).
        version (str): Version de l’application.
    """
    st.markdown("---")
    today = datetime.today().strftime("%Y-%m-%d")
    github_link = f" • [github.com/{github}]({github})" if github else ""
    st.markdown(f"""
        <div style="text-align: center; font-size: 0.9rem; color: #888; margin-top: 2rem;">
            🧪 Datalyzer v{version} — par {author} — {today}{github_link}
        </div>
    """, unsafe_allow_html=True)
