# ============================================================
# Fichier : home.py
# Objectif : Page d’accueil professionnelle complète de Datalyzer
# ============================================================

import streamlit as st
from utils.ui_utils import show_header_image_safe, show_icon_header, show_footer

def run_home():
    # 🎴 Bandeau visuel principal
    show_header_image_safe("headers/header_torii_sunrise.png", height=300)

    # 🎌 Titre principal
    show_icon_header(
        emoji="🎌",
        title="Bienvenue sur Datalyzer",
        subtitle="Explorez vos données avec la rigueur japonaise et l'élégance zen."
    )

    # ✨ Présentation élégante
    st.markdown("""
    **Datalyzer** est votre compagnon interactif pour :
    - **Nettoyer** vos jeux de données,
    - **Analyser** vos variables sous tous les angles,
    - **Corriger** vos typages,
    - **Détecter** anomalies et outliers,
    - **Exporter** vos jeux nettoyés.

    🧭 _Naviguez à travers chaque étape grâce à une interface claire, moderne et inspirée de la culture japonaise._
    """, unsafe_allow_html=True)

    st.divider()

    # 🎏 Voyage visuel japonais
    st.markdown("## 🎏 Voyage visuel japonais")

    images = [
        ("headers/header_sakura_peaceful.png", "🌸 Sérénité sous les cerisiers"),
        ("headers/header_waves_blossoms.png", "🌊 Vagues et fleurs entrelacées"),
        ("backgrounds/bg_dragons_waves.png", "🐉 Dragons protecteurs des océans"),
    ]

    selected = st.selectbox("Choisissez une ambiance :", [caption for _, caption in images])

    for img_path, caption in images:
        if caption == selected:
            show_header_image_safe(img_path, height=400, alt_text=caption)
            break

    st.divider()

    # 🗺️ Navigation rapide propre
    st.markdown("## 🗺️ Navigation rapide")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📂 Gestion des fichiers")
        st.markdown("""
        - 📥 **Chargement & Snapshots** : Importez vos fichiers, gérez les versions intermédiaires.
        - 🔗 **Jointures** : Fusionnez plusieurs sources intelligemment avec suggestions.
        - 💾 **Export** : Exportez vos jeux nettoyés dans plusieurs formats (.csv, .xlsx, .json, .parquet).
        """)

        st.subheader("💾 Export final")
        st.markdown("""
        - 📥 **Sélection de colonnes**
        - 📄 **Choix du format**
        - 📤 **Téléchargement rapide**
        """)

    with col2:
        st.subheader("🔍 Analyse exploratoire")
        st.markdown("""
        - 🔎 **Exploration** : Types, valeurs manquantes, distributions, corrélations.
        - 🧾 **Typage** : Correction interactive ou automatique des types.
        - 🧪 **Qualité** : Score global, anomalies, doublons, colonnes constantes.
        - 📊 **Analyse multivariée** : ACP, clustering, corrélations avancées.
        - 🚨 **Anomalies** : Détection fine d'outliers via Z-Score ou IQR.
        - 📋 **Analyse catégorielle** : Croisements, corrélations entre variables catégorielles.
        - 🎯 **Analyse cible** : Approfondissement autour d'une ou plusieurs cibles.
        - 💡 **Suggestions** : Colonnes à encoder ou vectoriser automatiquement.
        """)

    st.divider()

    # 💡 Astuce de navigation
    st.info("💡 Utilisez le **menu latéral** 🏯 pour accéder directement à chaque étape de votre analyse.")

    # 📜 Footer harmonieux
    show_footer(author="Xavier Rousseau", github="xavier-data", version="1.0")
