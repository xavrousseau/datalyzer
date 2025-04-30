# ============================================================
# Fichier : home.py
# Objectif : Page d’accueil de Datalyzer (version épurée & pro)
# ============================================================

import streamlit as st
from utils.ui_utils import show_header_image

def run_home():
    # 🎴 Image pleine largeur en tête
    show_header_image("bg_torii_sunrise.png")

    # 🎌 Introduction à l'application
    st.title("🌸 Bienvenue sur Datalyzer")
    st.markdown("""
        _Une interface fluide et zen pour explorer, nettoyer et analyser vos données._  
        Cette application vous permet de transformer vos fichiers de données bruts en jeux de données prêts à l’analyse ou au machine learning, grâce à un pipeline interactif complet.
    """)

    st.divider()

    # 🧭 Guide utilisateur / description des sections
    st.markdown("## 🗺️ Guide de navigation")

    st.markdown("""
    ### 📁 Fichiers
    - **Chargement & Snapshots** : Importez vos fichiers CSV ou Excel, enregistrez des versions intermédiaires (snapshots).
    - **Jointures** : Fusionnez plusieurs fichiers selon des clés communes avec vérification automatique.
    - **Export** : Sélectionnez les colonnes finales et exportez dans plusieurs formats (.csv, .json, .xlsx...).

    ### 🔍 Analyse
    - **Exploration** : Types de variables, valeurs manquantes, distributions, outliers, nettoyage automatique.
    - **Typage** : Correction interactive des types de colonnes (int, float, string...).
    - **Suggestions** : Recommandations de nettoyage (encodage, texte libre, redondances).
    - **Qualité** : Score global, heatmap de NA, détection des colonnes problématiques.
    - **Multivariée** : ACP, clustering, projection 2D, boxplots.
    - **Catégorielle** : Corrélations via Cramér’s V, boxplots, croisements.
    - **Cible** : Analyse approfondie d’une variable cible (corrélations, regroupements, nuages de points).
    - **Anomalies** : Détection d’outliers par variable avec Z-score ou IQR.
    """)

    st.divider()

    # 💡 Astuce
    st.info("💡 Astuce : utilisez le menu latéral gauche pour naviguer entre les sections.")
