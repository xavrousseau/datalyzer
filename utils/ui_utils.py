# ============================================================
# Fichier : utils/ui_utils.py
# Objectif : Fonctions d’interface graphique pour Datalyzer
# Version : stable, compatible local/docker, thème sombre
# Auteur : Xavier Rousseau (refonte commentée)
# ------------------------------------------------------------
# Points clés :
# - Affichage image d’en-tête robuste (PIL -> base64) + fallback.
# - En-têtes (icône + titre) paramétrables (couleurs, tailles, align).
# - Barre de progression EDA adaptative (colonnes qui se replient).
# - Footer sobre, accessible, avec date/année et lien GitHub.
# - Pas de dépendance forte à une palette globale : couleurs passées
#   en param, avec valeurs par défaut raisonnables.
# ============================================================

from __future__ import annotations

import os
import base64
from datetime import datetime
from io import BytesIO
from typing import Dict, Iterable, Optional
import html
import streamlit as st
from PIL import Image
from textwrap import dedent


# =============================== Helpers internes ==============================

def _to_base64_img(path: str, *, resize_to: tuple[int, int] | None = None) -> str:
    """
    Charge une image et renvoie une data-URL base64 'data:image/<fmt>;base64,...'.
    Utile pour fiabiliser l’affichage (chemins relatifs parfois capricieux en prod).

    Args:
        path: chemin local vers l’image.
        resize_to: (w, h) si redimensionnement souhaité.

    Raises:
        FileNotFoundError / PIL.UnidentifiedImageError en cas de souci.
    """
    img = Image.open(path)
    if resize_to:
        img = img.resize(resize_to)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _centered_html_img(data_url: str, *, height: int | None = None, alt: str = "header") -> str:
    """
    Génère un bloc HTML centré contenant une image avec styles doux.
    """
    height_attr = f"height='{height}'" if height else ""
    return (
        "<div style='display:flex;justify-content:center;margin-bottom:1rem;'>"
        f"<img src='{data_url}' alt='{alt}' {height_attr} "
        "style='border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.2);'/>"
        "</div>"
    )


# ============================= Image d’en-tête sûre ============================

def show_header_image_safe(
    relative_path: str,
    height: int = 220,
    caption: str | None = None,
    *,
    resize_to: tuple[int, int] | None = (900, 220),
) -> bool:
    """
    Affiche une image d’en-tête depuis /static en essayant plusieurs chemins.
    Retourne True si l'image a été affichée, False sinon.

    Args:
        relative_path: "images/headers/header.png" ou simplement "header.png".
        height: hauteur cible CSS (px) pour le rendu.
        caption: petite légende sous l’image.
        resize_to: taille pour le redimensionnement côté PIL avant encodage.

    Stratégie de recherche (dans cet ordre) :
      1) "static/<relative_path>"
      2) si <relative_path> ne contient pas de '/', on tente aussi :
         "static/images/headers/<relative_path>"

    Notes :
      - On privilégie un rendu BASE64 pour éviter les soucis de SERVE de fichiers
        statiques (notamment en prod / reverse proxy).
      - En échec, fallback vers st.image avec use_container_width (centré via colonnes).
    """
    candidates: list[str] = [os.path.join("static", relative_path)]
    if "/" not in relative_path and "\\" not in relative_path:
        candidates.append(os.path.join("static", "images", "headers", relative_path))

    for path in candidates:
        if os.path.exists(path):
            try:
                data_url = _to_base64_img(path, resize_to=resize_to)
                st.markdown(_centered_html_img(data_url, height=height), unsafe_allow_html=True)
                if caption:
                    st.caption(caption)
                return True
            except Exception:
                # Fallback simple : st.image, centré via colonnes Streamlit
                col_l, col_c, col_r = st.columns([1, 2, 1])
                with col_c:
                    st.image(path, caption=caption, use_container_width=True)
                return True

    st.info("Aucune image d’en-tête trouvée.")
    return False


# ================================ En-tête stylé ================================

def show_icon_header(
    icon: str,
    title: str,
    subtitle: str = "",
    description: str = "",
    *,
    title_size: str = "1.8rem",
    align: str = "center",
    color_title: str = "#FF6D99",
    color_subtitle: str = "#AAAAAA",
    color_description: str = "#BBBBBB",
    max_width_ch: int = 70,
) -> None:
    """
    Affiche un bloc en-tête : icône + titre + sous-titre + description.

    Args:
        icon: emoji/icone (ex: "📂").
        title: titre principal.
        subtitle: sous-titre court (optionnel).
        description: paragraphe explicatif (optionnel).
        title_size: taille CSS du titre (ex: '2rem').
        align: 'left' | 'center' | 'right'.
        color_title: couleur du titre.
        color_subtitle: couleur du sous-titre.
        color_description: couleur du paragraphe.
        max_width_ch: largeur max du paragraphe en "ch" (caractères).
    """
    align = align if align in {"left", "center", "right"} else "center"

    subtitle_html = (
        f"<p style='font-size:1rem;color:{color_subtitle};margin:.2rem 0 .6rem 0;'>"
        f"{subtitle}</p>"
        if subtitle
        else ""
    )
    desc_html = (
        f"<p style='font-size:.95rem;color:{color_description};margin:0;max-width:{max_width_ch}ch;display:inline-block;'>"
        f"{description}</p>"
        if description
        else ""
    )

    st.markdown(
        f"""
        <div style="text-align:{align};margin-bottom:1.5rem;">
          <div style="font-size:2rem;line-height:1;margin-bottom:.25rem;">{icon}</div>
          <h1 style="font-size:{title_size};font-weight:700;color:{color_title};margin:.1rem 0 .4rem 0;">
            {title}
          </h1>
          {subtitle_html}
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================= Progression des étapes ==========================

def show_eda_progress(
    steps_dict: Dict[str, str],
    status_dict: Optional[Dict[str, bool]] = None,
    *,
    title: str = "Progression EDA",
    compact: bool = True,
    single_row: bool = True,
) -> float:
    status = status_dict or st.session_state.get("validation_steps", {}) or {}
    total  = len(steps_dict)
    done   = sum(bool(status.get(code, False)) for code in steps_dict)
    ratio  = (done / total) if total else 0.0
    percent = int(ratio * 100)

    st.markdown(f"### {html.escape(title)}")

    if compact:
        bar_html = dedent(f"""
        <div style="margin:.3rem 0 .8rem 0;">
          <div style="height:8px;background:#2b2f3a;border-radius:8px;overflow:hidden;">
            <div style="height:8px;width:{percent}%;background:#7bd88f;"></div>
          </div>
          <div style="font-size:.9rem;color:#9aa0a6;margin-top:.3rem;">
            Progression : {done}/{total} ({percent}%)
          </div>
        </div>
        """).strip()
        st.markdown(bar_html, unsafe_allow_html=True)
    else:
        st.progress(ratio)

    if total == 0:
        st.caption("Aucune étape définie.")
        return ratio

    wrap = "nowrap" if single_row else "wrap"
    overflow_x = "auto" if single_row else "visible"

    cards = []
    for code, label in steps_dict.items():
        label_safe = html.escape(str(label))
        done_flag  = bool(status.get(code, False))
        icon  = "✅" if done_flag else "⏳"
        color = "#7bd88f" if done_flag else "#a0a0a0"
        cards.append(dedent(f"""
        <div style="
          flex:0 0 auto;display:flex;align-items:center;gap:.6rem;
          padding:.7rem .95rem;margin:.35rem;background:rgba(17,17,17,.20);
          border:1px solid #333;border-radius:.9rem;white-space:nowrap;">
          <span style="color:{color};font-size:1.05rem;">{icon}</span>
          <span style="color:#e6e6e6;">{label_safe}</span>
        </div>
        """).strip())

    container_html = dedent(f"""
    <div style="display:flex;flex-wrap:{wrap};gap:.25rem;overflow-x:{overflow_x};
                padding:.2rem .1rem .4rem .1rem;scrollbar-width:thin;">
      {''.join(cards)}
    </div>
    <div style="font-size:.85rem;color:#9aa0a6;margin-top:.2rem;">
      Légende : <span style="color:#7bd88f;">✅ terminé</span> · <span style="#a0a0a0;">⏳ en attente</span>
    </div>
    """).strip()

    st.markdown(container_html, unsafe_allow_html=True)
    return ratio


# =================================== Footer ===================================

def show_footer(
    author: str = "Xavier Rousseau",
    github: str = "xsorouz",
    version: str = "1.0",
    *,
    show_date: bool = True,
) -> None:
    """
    Affiche un footer sobre avec auteur, version, date et lien GitHub.

    Args:
        author: nom affiché.
        github: handle GitHub (profile/org).
        version: version de l’app.
        show_date: afficher la date du jour.
    """
    st.markdown("---")
    today = datetime.today().strftime("%Y-%m-%d") if show_date else ""
    year = datetime.today().strftime("%Y")

    date_part = f" — {today}" if today else ""
    st.markdown(
        f"""
        <div style="text-align:center;font-size:.9rem;color:#888;margin-top:1rem;">
          © {year} · Datalyzer v{version} — {author}{date_part}
          • <a href="https://github.com/{github}" target="_blank" rel="noopener noreferrer">
              github.com/{github}
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )
