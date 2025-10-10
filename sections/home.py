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
      - Un encart d’introduction au SQL Lab.
      - Trois cartes présentant les fonctionnalités clés.
      - Un pied de page cohérent sur tout le site.
    """
    # --- Palette : couleurs de texte et de fond du bloc introductif.
    text = color("texte", "#e8eaed")
    section_bg = color("fond_section", "#111418")

    # ---------- En-tête standard ----------
    section_header(
        title=APP_NAME,
        subtitle=(
            "Une plateforme sobre et efficace pour explorer, nettoyer "
            "et structurer vos données tabulaires."
        ),
        section="home",
        prequote=PRE_TITLE_QUOTE,
        emoji="🏯",
    )

    # ---------- Bloc “Pour bien démarrer” ----------
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


    # ---------- Sous-titre d’intro ----------
    st.subheader("Aperçu de l'application")

    # ---------- Trois colonnes principales ----------
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

    # Petit espace vertical
    st.markdown("<div style='height:.75rem;'></div>", unsafe_allow_html=True)

    # ---------- Bloc “À propos du SQL Lab” ----------
    st.markdown(
        f"""
        <div role="note"
             style="
                background-color:{section_bg};
                border-left:4px solid #7aa2f7;
                border-radius:10px;
                padding:1rem 1.5rem;
                margin-bottom:1.5rem;
                box-shadow:0 1px 6px rgba(0,0,0,0.06);
                color:{text};
             ">
            <strong>À propos du SQL Lab</strong><br/>
            Le SQL Lab vous permet d’exécuter des <em>requêtes ad hoc</em> (moteur DuckDB intégré)
            pour vérifier ou croiser vos données rapidement.
            <ul style="margin:.5rem 0 0 .75rem;">
                <li><b>Comment y retrouver vos jeux ?</b>
                    Depuis chaque section (Exploration, Typage, Anomalies, Export…),
                    cliquez sur <em>Publier au SQL Lab</em> pour y rendre la table disponible.</li>
                <li><b>Jointures faciles :</b>
                    une colonne <code>__index__</code> est automatiquement ajoutée pour simplifier les jointures.</li>
                <li><b>Requêtes autorisées :</b>
                    uniquement des <code>SELECT</code> et <code>JOIN</code> —
                    les opérations <code>DROP/UPDATE/DELETE/CREATE</code> sont bloquées.</li>
                <li><b>Utilisation typique :</b>
                    contrôles qualité, vérifications ciblées, exploration libre.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Pied de page ----------
    show_footer(
        author="Xavier Rousseau",
        site_url="https://xavrousseau.github.io/",
        version="1.0",
    )
