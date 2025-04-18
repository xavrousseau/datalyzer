# config.py

import streamlit as st

def configure_app():
    st.set_page_config(
        page_title="EDA Explorer – Analyse exploratoire de données",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # CSS personnalisé pour boutons, sliders, mise en forme responsive
    st.markdown("""
        <style>
            /* Boutons Streamlit */
            .stButton>button {
                color: white;
                background: #0099cc;
                border-radius: 0.5rem;
                padding: 0.5em 1em;
            }

            .stDownloadButton>button {
                background-color: #28a745;
                color: white;
                border-radius: 0.5rem;
            }

            .stSlider>div {
                background-color: #f0f0f5;
            }

            /* Masquer le footer Streamlit */
            footer {visibility: hidden;}

            /* Adaptation mobile */
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
