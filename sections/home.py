# ============================================================
# Fichier : sections/home.py
# Objectif : Page d’accueil professionnelle, claire et zen
# Auteur : Xavier Rousseau
# ------------------------------------------------------------
# Points de design :
#  - Utilise utils.ui_utils.section_header() pour l'en-tête
#    standard (bannière + citation + titre + baseline).
#  - Utilise utils.ui_utils.ui_card() pour des cartes homogènes
#    et responsives.
#  - Les couleurs proviennent de config.color() : tolérant aux
#    clés manquantes avec valeurs par défaut.
#  - show_footer() affiche un pied de page cohérent sur tout le
#    site.
# ============================================================

from __future__ import annotations

import streamlit as st

from utils.ui_utils import section_header, ui_card, show_footer
from config import APP_NAME, color


# ---------- Constantes UI ----------
# Petit aphorisme d’intro ; s’affiche avant le titre principal.
PRE_TITLE_QUOTE: str = "« La clarté naît de la structure. » — Datalyzer"


def run_home() -> None:
    """
    Affiche la page d'accueil principale de l'application Datalyzer.

    Rendu :
      - En-tête standard (bannière liée à la section "home", citation,
        titre = APP_NAME, baseline).
      - Un encart "Pour bien démarrer" avec un mini mode d'emploi.
      - Trois cartes en colonnes présentant les fonctionnalités clés.
      - Un pied de page avec auteur, site et version.

    Dépendances attendues :
      - `config.APP_NAME` : nom lisible de l’app.
      - `config.color(key: str, fallback: str)` : récupère une couleur
        de palette, avec valeur de secours si la clé n’existe pas.
      - `utils.ui_utils.section_header(...)` : en-tête visuel unifié.
      - `utils.ui_utils.ui_card(title: str, html_content: str)` :
        carte responsive avec contenu HTML.
      - `utils.ui_utils.show_footer(...)` : pied de page standardisé.

    Accessibilité :
      - Les encarts informatifs utilisent role="note".
      - Les listes de fonctionnalités sont de vraies <ul>/<li>.

    Remarque :
      - On utilise `unsafe_allow_html=True` pour un HTML minimal et
        maîtrisé (encarts, espacements). Le contenu est statique ici.
    """
    # --- Palette : couleurs de texte et de fond du bloc introductif.
    #     `color` renvoie la valeur définie dans la config, sinon le fallback.
    text = color("texte", "#e8eaed")
    section_bg = color("fond_section", "#111418")

    # ---------- En-tête standard (bannière + citation + titre + baseline) ----------
    # `section="home"` fait chercher l’image dans config.SECTION_BANNERS["home"].
    section_header(
        title=APP_NAME,
        subtitle=(
            "Une plateforme sobre et efficace pour explorer, nettoyer "
            "et structurer vos données tabulaires."
        ),
        section="home",
        prequote=PRE_TITLE_QUOTE,
    )

    # ---------- Bloc “Pour bien démarrer” ----------
    # Petit encart didactique, neutre et lisible, avec role ARIA.
    st.markdown(
        f"""
        <div role="note"
             style="
                background-color:{section_bg};
                border-radius:10px;
                padding:1rem 1.5rem;
                margin-bottom:2rem;
                box-shadow:0 1px 6px rgba(0,0,0,0.06);
                color:{text};
             ">
            <strong>Pour bien démarrer :</strong>
            importez vos données via l’onglet <em>Chargement</em>, puis explorez, corrigez
            et exportez un jeu prêt à l’analyse.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Séparateur visuel léger
    st.markdown("---")
    st.markdown("### Aperçu de l'application")

    # ---------- Trois colonnes ----------
    # Astuce : sur des écrans étroits, Streamlit empile les colonnes ;
    #           évite d’y mettre des contenus trop longs.
    col1, col2, col3 = st.columns(3)

    # Carte 1 : panorama des fonctionnalités
    with col1:
        ui_card(
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

    # Carte 2 : volet données (I/O + jointures)
    with col2:
        ui_card(
            "Données",
            """
            <ul>
              <li>Chargement : CSV, XLSX, Parquet</li>
              <li>Jointures : fusion intelligente sur clés</li>
              <li>Export : formats propres et exploitables</li>
            </ul>
            """,
        )

    # Carte 3 : analytique et qualité
    with col3:
        ui_card(
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

    # Petit espace vertical (plus souple qu’un <br>).
    st.markdown("<div style='height:.75rem;'></div>", unsafe_allow_html=True)

    # ---------- Pied de page ----------
    # Note : show_footer(...) est centralisé pour garantir la cohérence du site.
    # Assure-toi que sa signature correspond à cette invocation dans utils.ui_utils.
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
