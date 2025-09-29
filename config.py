# ============================================================
# Fichier : config.py
# Objectif : Configuration globale de l'application Datalyzer
# Remarque : la config de page (set_page_config) est faite dans app.py.
# Ici, on gère l'injection CSS/Fonts + utilitaires bannières/couleurs.
# ============================================================

from __future__ import annotations

from pathlib import Path
import streamlit as st

# --- Métadonnées de l'application ---
APP_NAME: str = "Datalyzer"
SECTIONS_DIR: str = "sections"

# Chemin cohérent avec app.py (où l'image est sous "static/...")
LOGO_PATH: str = "static/images/sidebars/japanese-temple.png"

# --- Palette sombre (utilitaire interne si besoin dans les sections) ---
PALETTE_ZEN: dict[str, str] = {
    "fond": "#0D0E17",          # Fond sombre principal
    "primaire": "#FF6D99",      # Rose sakura tamisé
    "secondaire": "#88BDBC",    # Vert bambou doux
    "texte": "#E0E0E0",         # Texte clair lisible
    "accent": "#D9CAB3",        # Beige sable
    "fond_section": "#1A1B2B",  # Conteneurs
}

def color(key: str, default: str) -> str:
    """Accès tolérant aux couleurs."""
    return PALETTE_ZEN.get(key, default)

# --- Bannières & UI par section ---
BANNER_SIZE: tuple[int, int] = (900, 220)

DEFAULT_BANNERS = [
    "static/images/headers/header_temple.png",
    "static/images/headers/header_resized_2.png",
    "static/images/headers/header_series_01_lever_soleil.png",
]

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
      - si chemin configuré mais manquant → bascule sur le cycle
    """
    if not section:
        return DEFAULT_BANNERS[0]
    key = str(section).strip().lower()
    path = SECTION_BANNERS.get(key)
    if path and Path(path).exists():
        return path
    idx = abs(hash(key)) % len(DEFAULT_BANNERS)
    return DEFAULT_BANNERS[idx]

# --- Garde-fous internes ---
_CSS_LOADED: bool = False

def _inject_css_once(css_path: Path) -> None:
    """Injecte la feuille de style une seule fois (sombre + clair + responsive)."""
    global _CSS_LOADED
    if _CSS_LOADED:
        return
    if not css_path.exists():
        st.caption("⚠️ Feuille de style introuvable : %s" % css_path.as_posix())
        return

    try:
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        _CSS_LOADED = True
    except Exception as e:
        st.warning(f"Impossible de charger la feuille de style ({e}).")

def configure_app() -> None:
    """
    Configuration visuelle complémentaire :
    - injection du CSS (incluant @media light + responsive)
    - chargement de la police Noto Sans JP
    NOTE : `st.set_page_config` est appelé dans app.py (au tout début).
    """
    # 1) CSS global (nom neutre : la feuille gère dark/light via media query)
    _inject_css_once(Path("assets/style.css"))

    # 2) Police (idempotent côté navigateur)
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )
