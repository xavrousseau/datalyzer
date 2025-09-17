# ============================================================
# Fichier : utils/ui_utils.py
# Objectif : Fonctions d’interface graphique pour Datalyzer
# Thème : sombre, sobre, accessible ; compatible local/docker
# ------------------------------------------------------------
# Points clés :
# - Bannière robuste (PIL -> base64, cache) avec fallbacks gracieux.
# - En-tête de section standard (bannière + pré-citation + titre).
# - En-tête “icone + titre + sous-titre + description”.
# - Barre de progression EDA compacte et responsive.
# - Cartes UI cohérentes avec la DA.
# - Footer épuré avec version, auteur, date et lien.
# - Rétro-compat : show_header_image_safe() redirige vers show_banner().
# ============================================================

from __future__ import annotations

import base64
import html
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Dict, Optional, Tuple

from PIL import Image, UnidentifiedImageError
import streamlit as st

# --- Dépendances config (une seule source de vérité) ---
# color() : accès tolérant à la palette ; BANNER_SIZE : (w,h) par défaut ;
# SECTION_BANNERS : mapping section -> chemin d’image ; APP_NAME : nom app.
from config import color, BANNER_SIZE as BANNER_SIZE_DEFAULT, SECTION_BANNERS, APP_NAME,banner_for, APP_NAME
 


# ======================================================================
# Utilitaires d'image (privés)
# ======================================================================

@st.cache_data(show_spinner=False)
def _encode_image_base64(path: str, size: Optional[Tuple[int, int]] = None) -> Optional[str]:
    """
    Charge une image, optionnellement la redimensionne, puis renvoie son contenu encodé en base64 (PNG).
    Renvoie None si le fichier est introuvable ou illisible.
    """
    p = Path(path)
    if not p.exists():
        return None
    try:
        img = Image.open(p)
        if size is not None:
            # LANCZOS = filtre de redimensionnement haute qualité
            img = img.resize(size, Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except (UnidentifiedImageError, OSError):
        return None


def _section_banner_path(section: Optional[str]) -> Optional[str]:
    """Retourne un chemin de bannière via config.banner_for() (avec fallback)."""
    if not section:
        return None
    return banner_for(section)


# ======================================================================
# Bannière : affichage robuste avec fallbacks
# ======================================================================

def show_banner(
    image_path: Optional[str] = None,
    *,
    section: Optional[str] = None,
    size: Optional[Tuple[int, int]] = None,
    alt: Optional[str] = None,
    center: bool = True,
    rounded: bool = True,
    shadow: bool = True,
) -> None:
    """
    Affiche une bannière encodée en base64 (performant et fiable derrière un reverse proxy).
    - Priorité à image_path ; sinon déduite via 'section' et SECTION_BANNERS.
    - Fallbacks : st.image si le fichier existe ; sinon message discret.

    Args:
        image_path: chemin explicite de l’image à afficher.
        section: nom logique de la section (clé de SECTION_BANNERS).
        size: (w, h) ; défaut : BANNER_SIZE_DEFAULT.
        alt: texte alternatif (accessibilité) ; défaut : "Bannière {APP_NAME}".
        center: centrer le conteneur.
        rounded: rayons de bordure doux.
        shadow: ombre portée légère.
    """
    path = image_path or _section_banner_path(section)
    size = size or BANNER_SIZE_DEFAULT
    alt = alt or f"Bannière {APP_NAME}"

    if path:
        b64 = _encode_image_base64(path, size)
        if b64:
            container_style = []
            if center:
                container_style.append("display:flex;justify-content:center;")
            container_style.append("margin-bottom:1.5rem;")

            img_style = []
            if rounded:
                img_style.append("border-radius:12px;")
            if shadow:
                img_style.append("box-shadow:0 2px 8px rgba(0,0,0,0.2);")

            st.markdown(
                f"""
                <div style="{' '.join(container_style)}">
                  <img src="data:image/png;base64,{b64}" alt="{html.escape(alt)}" style="{' '.join(img_style)}" />
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        # Fallback : fichier existant mais encodage raté → st.image (width auto)
        if Path(path).exists():
            st.image(path, caption=None, use_container_width=True)
            return

    # Fallback final : message discret (pas de stacktrace)
    st.info("Bannière indisponible (image manquante).")


# Rétro-compat : certains modules appellent encore cet ancien helper
def show_header_image_safe(path: str) -> None:
    """Alias rétro-compat : redirige l’ancien helper vers show_banner()."""
    show_banner(image_path=path)


# ======================================================================
# En-têtes
# ======================================================================

def section_header(
    title: str,
    subtitle: Optional[str] = None,
    *,
    section: Optional[str] = None,
    banner_path: Optional[str] = None,
    prequote: Optional[str] = None,
    emoji: Optional[str] = None,
    banner_size: Optional[Tuple[int, int]] = None,
) -> None:
    """
    En-tête standard de section : bannière (optionnelle) → pré-citation → titre → sous-titre.
    Utilise la palette via config.color().
    """
    primary = color("primaire", "#8ab4f8")
    text = color("texte", "#e8eaed")
    accent = color("accent", "#7bdff2")

    # 1) Bannière (si fournie par section ou chemin explicite)
    if banner_path or section:
        show_banner(banner_path, section=section, size=banner_size)

    # 2) Pré-citation (optionnelle)
    if prequote:
        st.markdown(
            f"""
            <p style="text-align:center;font-style:italic;font-size:14px;color:{accent};margin:0 0 1rem 0;">
              {html.escape(prequote)}
            </p>
            """,
            unsafe_allow_html=True,
        )

    # 3) Titre + sous-titre
    prefix = f"{emoji} " if emoji else ""
    st.markdown(
        f"""
        <h1 style="color:{primary};margin-bottom:.5rem;">{prefix}{html.escape(title)}</h1>
        """,
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"""
            <p style="font-size:16px;color:{text};margin-top:0;">{html.escape(subtitle)}</p>
            """,
            unsafe_allow_html=True,
        )


def show_icon_header(
    icon: str,
    title: str,
    subtitle: str = "",
    description: str = "",
    *,
    title_size: str = "1.8rem",
    align: str = "center",
    color_title: str | None = None,
    color_subtitle: str | None = None,
    color_description: str | None = None,
    max_width_ch: int = 70,
) -> None:
    """
    En-tête “icône + titre + sous-titre + description” (pratique pour des pages simples).
    """
    align = align if align in {"left", "center", "right"} else "center"
    color_title = color_title or color("primaire", "#FF6D99")
    color_subtitle = color_subtitle or color("accent", "#AAAAAA")
    color_description = color_description or color("texte", "#BBBBBB")

    subtitle_html = (
        f"<p style='font-size:1rem;color:{color_subtitle};margin:.2rem 0 .6rem 0;'>{html.escape(subtitle)}</p>"
        if subtitle
        else ""
    )
    desc_html = (
        f"<p style='font-size:.95rem;color:{color_description};margin:0;max-width:{max_width_ch}ch;display:inline-block;'>"
        f"{html.escape(description)}</p>"
        if description
        else ""
    )

    st.markdown(
        f"""
        <div style="text-align:{align};margin-bottom:1.5rem;">
          <div style="font-size:2rem;line-height:1;margin-bottom:.25rem;">{html.escape(icon)}</div>
          <h1 style="font-size:{title_size};font-weight:700;color:{color_title};margin:.1rem 0 .4rem 0;">
            {html.escape(title)}
          </h1>
          {subtitle_html}
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ======================================================================
# Cartes & Progression
# ======================================================================

def ui_card(title: str, content_html: str, *, min_height_px: int = 280) -> None:
    """
    Carte neutre et réutilisable. Le contenu est en HTML (listes, paragraphes).
    """
    bg = color("fond_section", "#111418")
    txt = color("texte", "#e8eaed")
    sec = color("secondaire", "#8ab4f8")

    st.markdown(
        f"""
        <div role="region" aria-label="{html.escape(title)}"
             style="
                background-color:{bg};
                border-radius:10px;
                padding:1.2rem;
                min-height:{min_height_px}px;
                box-shadow:0 1px 6px rgba(0,0,0,0.06);
                color:{txt};
             ">
            <h4 style="color:{sec};margin-top:0;">{html.escape(title)}</h4>
            <div style="line-height:1.55;font-size:14.5px;">{content_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_eda_progress(
    steps_dict: Dict[str, str],
    status_dict: Optional[Dict[str, bool]] = None,
    *,
    title: str = "Progression EDA",
    compact: bool = True,
    single_row: bool = True,
) -> float:
    """
    Affiche une progression d’étapes EDA.
    - compact=True : barre + pastilles ; sinon st.progress classique.
    - single_row=True : les pastilles défilent horizontalement ; sinon elles se replient.
    Renvoie le ratio [0,1].
    """
    status = status_dict or st.session_state.get("validation_steps", {}) or {}
    total = len(steps_dict)
    done = sum(bool(status.get(code, False)) for code in steps_dict)
    ratio = (done / total) if total else 0.0
    percent = int(ratio * 100)

    st.markdown(f"### {html.escape(title)}")

    if compact:
        bar_bg = color("fond_section", "#2b2f3a")
        bar_fg = "#7bd88f"
        st.markdown(
            dedent(f"""
            <div style="margin:.3rem 0 .8rem 0;">
              <div style="height:8px;background:{bar_bg};border-radius:8px;overflow:hidden;">
                <div style="height:8px;width:{percent}%;background:{bar_fg};"></div>
              </div>
              <div style="font-size:.9rem;color:#9aa0a6;margin-top:.3rem;">
                Progression : {done}/{total} ({percent}%)
              </div>
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )
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
        done_flag = bool(status.get(code, False))
        icon = "✅" if done_flag else "⏳"
        color_fg = "#7bd88f" if done_flag else "#a0a0a0"
        cards.append(
            dedent(f"""
            <div style="
              flex:0 0 auto;display:flex;align-items:center;gap:.6rem;
              padding:.7rem .95rem;margin:.35rem;background:rgba(17,17,17,.20);
              border:1px solid #333;border-radius:.9rem;white-space:nowrap;">
              <span style="color:{color_fg};font-size:1.05rem;">{icon}</span>
              <span style="color:#e6e6e6;">{label_safe}</span>
            </div>
            """).strip()
        )

    st.markdown(
        dedent(f"""
        <div style="display:flex;flex-wrap:{wrap};gap:.25rem;overflow-x:{overflow_x};
                    padding:.2rem .1rem .4rem .1rem;scrollbar-width:thin;">
          {''.join(cards)}
        </div>
        <div style="font-size:.85rem;color:#9aa0a6;margin-top:.2rem;">
          Légende : <span style="color:#7bd88f;">✅ terminé</span> · <span style="color:#a0a0a0;">⏳ en attente</span>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )
    return ratio


# ======================================================================
# Footer
# ======================================================================

def show_footer(
    author: str = "Xavier Rousseau",
    site_url: str = "https://xavrousseau.github.io/",
    version: str = "1.0",
    *,
    show_date: bool = True,
) -> None:
    """
    Footer sobre avec auteur, version, date et lien externe.
    """
    from datetime import datetime

    st.markdown("---")
    today = datetime.today().strftime("%Y-%m-%d") if show_date else ""
    year = datetime.today().strftime("%Y")
    date_part = f" — {today}" if today else ""

    st.markdown(
        f"""
        <div style="text-align:center;font-size:.9rem;color:#888;margin-top:1rem;">
          © {year} · Datalyzer v{html.escape(version)} — {html.escape(author)}{date_part}
          • <a href="{html.escape(site_url)}" target="_blank" rel="noopener noreferrer">{html.escape(site_url)}</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
