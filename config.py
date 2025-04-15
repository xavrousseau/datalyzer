# config.py

import streamlit as st

def configure_app():
    st.set_page_config(
        page_title="EDA Explorer – Analyse exploratoire de données",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Style CSS personnalisé (boutons, sliders, etc.)
    st.markdown("""
        <style>
            .stButton>button {
                color: white;
                background: #0099cc;
            }
            .stDownloadButton>button {
                background-color: #28a745;
                color: white;
            }
            .stSlider>div {
                background-color: #f0f0f5;
            }
        </style>
    """, unsafe_allow_html=True)
