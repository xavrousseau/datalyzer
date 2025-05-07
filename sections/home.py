# ============================================================
# Fichier : home.py
# Objectif : Page d’accueil sobre et japonisante de Datalyzer
# ============================================================

import streamlit as st
from utils.ui_utils import show_header_image_safe, show_footer

def run_home():
    # 🖼️ Bannière
    show_header_image_safe("headers/header.png", height=240, alt_text="Temple de nuit")

    # 🧭 En-tête
    st.markdown("""
        <h1 style='margin-bottom: 0.5rem;'>Bienvenue sur Datalyzer</h1>
        <p style='font-size: 17px; color: #CCC; margin-top: 0;'>Explorez, nettoyez et structurez vos données avec rigueur, clarté et élégance japonaise.</p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 🧾 Présentation
    st.markdown("""
        <div style="font-size: 16px; line-height: 1.7;">
            <p><strong>Datalyzer</strong> est une application conçue pour vous accompagner dans chaque étape de l’analyse exploratoire :</p>
            <ul style="margin-top: -0.5rem;">
                <li>Nettoyage des valeurs manquantes, doublons, colonnes peu informatives</li>
                <li>Correction du typage, détection d’anomalies</li>
                <li>Analyses multivariées, catégorielles et ciblées</li>
                <li>Suggestions automatiques pour la préparation des données</li>
                <li>Export final en <code>CSV</code>, <code>Excel</code>, <code>JSON</code>, ou <code>Parquet</code></li>
            </ul>
            <p style="margin-top: 0.5rem; color: #AAA;"><em>L’interface s’inspire des principes zen : sobriété, équilibre, efficacité.</em></p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # 🚀 Accès rapide
    st.markdown("## Accès rapide aux modules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background-color: #1B1B2D; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
            <h4>Données & Fichiers</h4>
            <ul style="line-height: 1.6;">
                <li><strong>Chargement & Snapshots</strong> : Import, versioning local</li>
                <li><strong>Jointures</strong> : Fusion sur une ou plusieurs clés</li>
                <li><strong>Export</strong> : Sélection, format, compression</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background-color: #1B1B2D; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
            <h4>Analyse & Qualité</h4>
            <ul style="line-height: 1.6;">
                <li><strong>Exploration</strong> : Types, manquants, distributions</li>
                <li><strong>Typage</strong> : Détection auto, édition manuelle</li>
                <li><strong>Qualité</strong> : Score global, colonnes à corriger</li>
                <li><strong>Multivariée</strong> : ACP, clustering, corrélations</li>
                <li><strong>Cible & Catégorielle</strong> : Corrélations croisées</li>
                <li><strong>Suggestions</strong> : Préparation automatique</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<p style='font-size: 14px; color: #888;'>Utilisez le <strong>menu latéral</strong> pour accéder à chaque fonctionnalité.</p>", unsafe_allow_html=True)
    show_footer(author="Xavier Rousseau", github="xavier-data", version="1.0")
