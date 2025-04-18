# config.py

import streamlit as st

def configure_app():
    st.set_page_config(
        page_title="EDA Explorer – Analyse exploratoire de données",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS global personnalisé
    st.markdown("""
        <style>
            /* Police harmonisée */
            html, body, [class*="css"] {
                font-family: "Segoe UI", "Roboto", sans-serif;
            }

            /* Boutons principaux */
            .stButton>button {
                color: white;
                background: #0099cc;
                border-radius: 0.5rem;
                padding: 0.5em 1em;
                font-weight: 600;
                transition: all 0.2s ease-in-out;
                border: none;
            }

            .stButton>button:hover {
                transform: scale(1.03);
                background-color: #007fa3;
            }

            /* Boutons de téléchargement */
            .stDownloadButton>button {
                background-color: #28a745;
                color: white;
                border-radius: 0.5rem;
                transition: all 0.2s ease-in-out;
                border: none;
            }

            .stDownloadButton>button:hover {
                transform: scale(1.03);
                background-color: #218838;
            }

            /* Sliders */
            .stSlider>div {
                background-color: #f0f0f5;
                padding: 0.2em;
                border-radius: 0.5rem;
            }

            /* Barre de progression */
            .stProgress > div > div {
                background-color: #00c49a;
            }

            /* En-têtes */
            h1, h2, h3 {
                font-weight: 700;
            }

            /* Masquer footer Streamlit */
            footer {
                visibility: hidden;
            }

            /* Mode responsive */
            @media (max-width: 768px) {
                .block-container {
                    padding: 0.5rem 1rem !important;
                }

                h1, h2, h3 {
                    font-size: 1.2rem !important;
                }

                .stButton>button, .stDownloadButton>button {
                    font-size: 0.9rem !important;
                }
            }
        </style>
    """, unsafe_allow_html=True)
