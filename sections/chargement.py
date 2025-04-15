# sections/chargement.py

import streamlit as st
import pandas as pd
import csv
from io import StringIO

from utils.filters import select_active_dataframe
from utils.log_utils import log_transformation


def run_chargement():
    st.title("📊 EDA Explorer – Application d'analyse exploratoire de données")
    st.markdown("---")

    uploaded_files = st.file_uploader(
        "📥 Sélectionnez un ou plusieurs fichiers",
        type=["csv", "xlsx", "parquet"],
        accept_multiple_files=True
    )

    if "dfs" not in st.session_state:
        st.session_state["dfs"] = {}

    if uploaded_files:
        for file in uploaded_files:
            name = file.name
            ext = name.split(".")[-1].lower()
            try:
                if ext == "csv":
                    text = file.read().decode("utf-8", errors="ignore")
                    sep = csv.Sniffer().sniff(text[:2048]).delimiter
                    df = pd.read_csv(StringIO(text), sep=sep)
                elif ext == "xlsx":
                    df = pd.read_excel(file)
                elif ext == "parquet":
                    df = pd.read_parquet(file)
                st.session_state["dfs"][name] = df
                st.success(f"✅ {name} chargé ({df.shape[0]} lignes × {df.shape[1]} colonnes)")
                log_transformation(f"Chargé : {name} – {df.shape[0]} lignes")
            except Exception as e:
                st.error(f"❌ Erreur avec {name} : {e}")

    if st.session_state["dfs"]:
        df, selected_name = select_active_dataframe()
        st.markdown(f"🔎 **Fichier sélectionné : `{selected_name}`**")
        st.dataframe(df.head(10), use_container_width=True)
