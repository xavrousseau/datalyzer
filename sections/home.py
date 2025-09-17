# ============================================================
# Fichier : sections/home.py
# Objectif : Page d’accueil professionnelle, claire et zen
# Auteur : Xavier Rousseau
# ------------------------------------------------------------
# Améliorations :
#  - Encodage base64 de la bannière mis en cache (@st.cache_data)
#  - Fallback propre si l’image manque (sans stacktrace)
#  - Palette tolérante (valeurs par défaut si une clé est absente)
#  - HTML minimal, composants Streamlit priorisés
# ============================================================

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

import streamlit as st
from PIL import Image, UnidentifiedImageError

from utils.ui_utils import show_footer
from config import APP_NAME, PALETTE_ZEN

# =============================== Constantes UI =================================

BANNER_PATH = "static/images/headers/header_temple.png"
BANNER_SIZE = (900, 220)   # Largeur x hauteur en pixels
CARD_MIN_HEIGHT_PX = 280
PRE_TITLE_QUOTE = "« La clarté naît de la structure. » — Datalyzer"

# Couleurs avec valeurs de secours (si une clé manque dans PALETTE_ZEN)
def _c(key: str, default: str) -> str:
    return PALETTE_ZEN.get(key, default)


# =============================== Helpers UI ====================================

@st.cache_data
def _encode_banner_base64(path: str, size: tuple[int, int]) -> Optional[str]:
    """
    Lit l'image, la redimensionne et renvoie le base64 (PNG).
    Mise en cache pour éviter de réencoder à chaque rerun Streamlit.
    """
    p = Path(path)
    if not p.exists():
        return None
    try:
        img = Image.open(p).resize(size)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except (UnidentifiedImageError, OSError):
        return None


def _render_banner(path: str = BANNER_PATH, size: tuple[int, int] = BANNER_SIZE) -> None:
    """
    Affiche la bannière d’accueil centrée.
    Utilise un <img> base64 (style contrôlé) si possible, sinon fallback st.image,
    sinon affiche un petit message discret (pas de stacktrace).
    """
    b64 = _encode_banner_base64(path, size)
    if b64:
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;margin-bottom:1.5rem;">
              <img src="data:image/png;base64,{b64}" alt="Bannière {APP_NAME}"
                   style="border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.2);" />
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Fallback 1 : essayer st.image si le fichier existe
    if Path(path).exists():
        st.image(path, caption=None, use_container_width=True)
    else:
        # Fallback 2 : message discret
        st.info("Bannière indisponible (image manquante).")


def _card(title: str, content_html: str, *, key: Optional[str] = None) -> None:
    """
    Rend une "carte" simple et cohérente avec la DA.
    Le contenu est HTML (listes, paragraphes) pour une mise en forme souple.
    """
    bg = _c("fond_section", "#111418")
    txt = _c("texte", "#e8eaed")
    sec = _c("secondaire", "#8ab4f8")

    st.markdown(
        f"""
        <div role="region" aria-label="{title}"
             style="
                background-color:{bg};
                border-radius:10px;
                padding:1.2rem;
                min-height:{CARD_MIN_HEIGHT_PX}px;
                box-shadow:0 1px 6px rgba(0,0,0,0.06);
                color:{txt};
             ">
            <h4 style="color:{sec};margin-top:0;">{title}</h4>
            <div style="line-height:1.55;font-size:14.5px;">{content_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================== Vue principale ================================

def run_home() -> None:
    """Affiche la page d'accueil principale de l'application Datalyzer."""
    primary = _c("primaire", "#8ab4f8")
    text = _c("texte", "#e8eaed")
    accent = _c("accent", "#7bdff2")
    section_bg = _c("fond_section", "#111418")

    # --- Bannière (robuste) ---
    _render_banner()

    # --- Citation d’intro (courte, accessible) ---
    st.markdown(
        f"""
        <p style="text-align:center;font-style:italic;font-size:14px;color:{accent};
                  margin:0 0 1rem 0;">
            {PRE_TITLE_QUOTE}
        </p>
        """,
        unsafe_allow_html=True,
    )

    # --- Titre principal + baseline ---
    st.markdown(
        f"""
        <h1 style="color:{primary};margin-bottom:.5rem;">{APP_NAME}</h1>
        <p style="font-size:16px;color:{text};margin-top:0;">
            Une plateforme sobre et efficace pour explorer, nettoyer et structurer vos données tabulaires.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:.5rem;'></div>", unsafe_allow_html=True)

    # --- Bloc "Pour bien démarrer" : court, contrasté, non intrusif ---
    st.markdown(
        f"""
        <div role="note"
             style="background-color:{section_bg};
                    border-radius:10px;
                    padding:1rem 1.5rem;
                    margin-bottom:2rem;
                    box-shadow:0 1px 6px rgba(0,0,0,0.06);
                    color:{text};">
            <strong>Pour bien démarrer :</strong>
            importez vos données via l’onglet <em>Chargement</em>, puis explorez, corrigez
            et exportez un jeu prêt à l’analyse.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Aperçu de l'application")

    # --- Trois colonnes : se replient automatiquement en mobile ---
    col1, col2, col3 = st.columns(3)

    with col1:
        _card(
            "Fonctionnalités principales",
            """
            <ul>
              <li>Import : CSV, Excel, JSON, Parquet</li>
              <li>Exploration intuitive des variables</li>
              <li>Nettoyage : doublons, types, valeurs manquantes</li>
              <li>Analyse : ACP, clustering, corrélations</li>
              <li>Suggestions de préparation automatique</li>
              <li>Export multi-format des jeux corrigés</li>
            </ul>
            """,
        )

    with col2:
        _card(
            "Données",
            """
            <ul>
              <li>Chargement : CSV, XLSX, Parquet</li>
              <li>Jointures : fusion intelligente sur clés</li>
              <li>Export : formats propres et exploitables</li>
            </ul>
            """,
        )

    with col3:
        _card(
            "Analyse",
            """
            <ul>
              <li>Exploration : types, distributions, manquants</li>
              <li>Typage : correction semi-automatique</li>
              <li>Qualité : doublons, erreurs, valeurs vides</li>
              <li>Multivariée : ACP, corrélations, clustering</li>
              <li>Ciblée / catégorielle : regroupements</li>
              <li>Suggestions : colonnes à corriger ou exclure</li>
            </ul>
            """,
        )

    st.markdown("<div style='height:.75rem;'></div>", unsafe_allow_html=True)

    # --- Pied de page standard (version affichée) ---
    show_footer(author="Xavier Rousseau", github="xsorouz", version="1.0")
