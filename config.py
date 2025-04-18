# config.py

import streamlit as st

def configure_app():
    st.set_page_config(
        page_title="EDA Explorer – Analyse exploratoire de données",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS personnalisé : boutons, sliders, barre de progression, responsive
    st.markdown("""
        <style>
            /* Polices cohérentes */
            body, button, label, .css-1cpxqw2 {
                font-family: "Segoe UI", "Roboto", sans-serif;
            }

            /* Boutons principaux */
            .stButton>button {
                color: white;
                background: #0099cc;
                border-radius: 0.5rem;
                padding: 0.5em 1em;
                transition: all 0.2s ease-in-out;
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
            }

            .stDownloadButton>button:hover {
                transform: scale(1.03);
                background-color: #218838;
            }

            /* Slider */
            .stSlider>div {
                background-color: #f0f0f5;
            }

            /* Barre de progression */
            .stProgress > div > div {
                background-color: #00c49a;
            }

            /* Masquer le footer Streamlit */
            footer {
                visibility: hidden;
            }

            /* Responsive mobile */
            @media (max-width: 768px) {
                .block-container {
                    padding: 0.5rem 1rem !important;
                }
                .css-18ni7ap {
                    padding-top: 0 !important;
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
