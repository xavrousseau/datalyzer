# ============================================================
# Fichier : config.py
# Objectif : Configuration globale de l'application Datalyzer
# Thème fixe : sombre uniquement (zen, sobre, stable)
# ============================================================

from __future__ import annotations

from pathlib import Path
import streamlit as st

# --- Métadonnées de l'application ---
APP_NAME: str = "Datalyzer"
SECTIONS_DIR: str = "sections"

# NB : garde ce chemin s'il est valide ; sinon bascule-la sous "static/images/sidebars/"
LOGO_PATH: str = "images/sidebars/japanese-temple.png"

# --- Palette sombre (cohérente avec assets/style_dark.css) ---
PALETTE_ZEN: dict[str, str] = {
    "fond": "#0D0E17",          # Fond sombre principal
    "primaire": "#FF6D99",      # Rose sakura tamisé
    "secondaire": "#88BDBC",    # Vert bambou doux
    "texte": "#E0E0E0",         # Texte clair lisible
    "accent": "#D9CAB3",        # Beige sable
    "fond_section": "#1A1B2B",  # Conteneurs
}

def color(key: str, default: str) -> str:
    """Accès tolérant aux couleurs (évite KeyError et stabilise les sections)."""
    return PALETTE_ZEN.get(key, default)

# --- Étapes EDA ---
# ⚠️ Source unique : utils/steps.py
# (on *retire* EDA_STEPS d'ici pour éviter tout décalage de clés / doublon)

# --- Bannières & UI par section ---
BANNER_SIZE: tuple[int, int] = (900, 220)

# Images par défaut pour le fallback cyclique
DEFAULT_BANNERS = [
    "static/images/headers/header_temple.png",
    "static/images/headers/header_resized_2.png",
    "static/images/headers/header_series_01_lever_soleil.png",
]

# Chemins d'images par section (relatifs à la racine de l’app)
# Ajout de la clé "analyse" car utilisée par plusieurs modules.
SECTION_BANNERS: dict[str, str] = {
    # --- Accueil & chargement ---
    "home":        "static/images/headers/header_temple.png",
    "chargement":  "static/images/headers/header_series_01_lever_soleil.png",

    # --- Préparation & exploration ---
    "typage":      "static/images/headers/header_resized_2.png",
    "exploration": "static/images/headers/header_temple.png",
    "anomalies":   "static/images/headers/header_series_01_lever_soleil.png",
    "qualite":     "static/images/headers/header_resized_2.png",

    # --- Analyses avancées ---
    "suggestions": "static/images/headers/header_temple.png",
    "multivariee": "static/images/headers/header_series_01_lever_soleil.png",
    "cible":       "static/images/headers/header_resized_2.png",
    "cat_analysis":"static/images/headers/header_temple.png",

    # --- Fusion & export ---
    "jointures":   "static/images/headers/header_series_01_lever_soleil.png",
    "export":      "static/images/headers/header_resized_2.png",

    # --- Alias générique pour modules refactorés ---
    "analyse":     "static/images/headers/header_temple.png",
}

def banner_for(section: str) -> str:
    """
    Renvoie le chemin de bannière pour une section.
    Fallback robuste :
      - normalise le nom de section
      - si clé absente → cycle déterministe parmi DEFAULT_BANNERS
      - si chemin configuré mais manquant sur disque → bascule sur le cycle
    """
    if not section:
        return DEFAULT_BANNERS[0]
    key = str(section).strip().lower()
    path = SECTION_BANNERS.get(key)
    if path:
        # si le fichier configuré n'existe pas (déploiement / renommage), on retombe sur le cycle
        if Path(path).exists():
            return path
    # fallback déterministe
    idx = abs(hash(key)) % len(DEFAULT_BANNERS)
    return DEFAULT_BANNERS[idx]

# --- Garde-fous internes ---
_PAGE_CONFIG_DONE: bool = False
_CSS_LOADED: bool = False

def _inject_css_once(css_path: Path) -> None:
    """Injecte la feuille de style une seule fois."""
    global _CSS_LOADED
    if _CSS_LOADED:
        return
    if css_path.exists():
        try:
            css = css_path.read_text(encoding="utf-8")
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            _CSS_LOADED = True
        except Exception:
            st.warning("Impossible de charger assets/style_dark.css (encodage/permissions).")
    else:
        st.caption("⚠️ Feuille de style 'assets/style_dark.css' introuvable.")

# === Initialisation de la page ===
def configure_app() -> None:
    """
    Configure la page Streamlit :
    - titre, icône, layout
    - injection du thème sombre CSS (une seule fois)
    - chargement de la police Noto Sans JP
    """
    global _PAGE_CONFIG_DONE

    if not _PAGE_CONFIG_DONE:
        st.set_page_config(
            page_title=f"{APP_NAME} — Analyse exploratoire",
            page_icon="🌑",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        _PAGE_CONFIG_DONE = True

    _inject_css_once(Path("assets/style_dark.css"))

    # Police (idempotent côté navigateur)
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )
