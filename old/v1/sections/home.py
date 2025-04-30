# ============================================================
# Fichier : home.py
# Objectif : Page d’accueil de Datalyzer (version finale)
# Version améliorée avec éléments interactifs et navigation dynamique
# ============================================================

import streamlit as st
from utils.ui_utils import show_header_image, show_icon_header, show_footer

def run_home():
    # 🎴 Image décorative d’introduction avec redimensionnement dynamique
    show_header_image("bg_torii_sunrise.png", height=250)

    # 🎌 Titre d’accueil stylisé
    show_icon_header("🌸", "Bienvenue sur Datalyzer", "Interface zen pour explorer, nettoyer et analyser vos données")

    # ✨ Présentation succincte
    st.markdown("""
    **Datalyzer** est une application interactive qui vous accompagne dans l’analyse exploratoire de vos données :  
    nettoyage, typage, visualisation, détection d’anomalies, export...  
    _Tout est intégré dans un pipeline fluide, pédagogique et élégant._
    """)

    st.divider()

    # 🧭 Guide utilisateur avec liens directs vers les pages principales
    st.markdown("## 🗺️ Guide de navigation")

    st.markdown("""
    ### 📁 Données
    - **[Chargement & Snapshots](#chargement)** : Importez vos fichiers `.csv`, `.xlsx`, `.parquet`... et créez des versions intermédiaires.
    - **[Jointures](#jointures)** : Fusionnez vos fichiers de manière interactive avec suggestions automatiques.
    - **[Export](#export)** : Exportez vos jeux nettoyés vers différents formats (.csv, .json, .xlsx, .parquet).

    ### 🔍 Analyse interactive
    - **[Exploration](#exploration)** : Vue globale (types, manquants, distributions, outliers, nettoyage automatique).
    - **[Typage](#typage)** : Correction interactive des types (`int`, `float`, `bool`, `datetime`...).
    - **[Suggestions](#suggestions)** : Variables à encoder ou vectoriser, détection de texte libre ou colonnes inutiles.
    - **[Qualité](#qualite)** : Score global, anomalies, doublons, heatmap de NA, placeholders.
    - **[Multivariée](#multivariee)** : ACP, clustering KMeans, boxplots, projection 2D, Cramér’s V.
    - **[Catégorielle](#cat)** : Corrélations, croisements, stats groupées.
    - **[Cible](#cible)** : Analyse centrée sur une ou deux cibles (`numérique` ou `catégorielle`).
    - **[Anomalies](#anomalies)** : Détection d’outliers via Z-score ou IQR.
    """)

    st.divider()

    # 💡 Astuce navigation
    st.info("💡 Utilisez le **menu latéral gauche** pour naviguer entre les sections.")
    
    # Menu latéral fixe (ajout de boutons ou liens interactifs)
    menu_options = ["Données", "Analyse", "Qualité", "Multivariée", "Catégorielle", "Anomalies", "Cible"]
    choice = st.sidebar.selectbox("Naviguer vers", menu_options)
    
    if choice == "Données":
        st.write("Accédez à l'onglet pour charger et visualiser vos fichiers.")
    elif choice == "Analyse":
        st.write("Accédez à l'onglet pour effectuer une analyse exploratoire de vos données.")
    elif choice == "Qualité":
        st.write("Accédez à l'onglet pour analyser la qualité des données.")
    elif choice == "Multivariée":
        st.write("Accédez à l'onglet pour une analyse multivariée des données.")
    elif choice == "Catégorielle":
        st.write("Accédez à l'onglet pour analyser les données catégorielles.")
    elif choice == "Anomalies":
        st.write("Accédez à l'onglet pour détecter les anomalies dans les données.")
    elif choice == "Cible":
        st.write("Accédez à l'onglet pour analyser les variables cibles.")

    show_footer("Xavier Rousseau", "xavier-data")
