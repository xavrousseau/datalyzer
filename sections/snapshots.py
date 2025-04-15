# sections/snapshots.py

import streamlit as st
import pandas as pd


def run_snapshots():
    st.subheader("🕰️ Historique des snapshots de données")

    snapshots = st.session_state.get("snapshots", {})
    if not snapshots:
        st.info("📭 Aucun snapshot enregistré pour le moment.")
        return

    selected_snapshot = st.selectbox("📜 Sélectionnez un snapshot à explorer :", list(snapshots.keys()))
    df_snapshot = snapshots[selected_snapshot]

    st.markdown(f"### 📋 Aperçu du snapshot : `{selected_snapshot}`")
    st.write(f"📐 Dimensions : {df_snapshot.shape[0]} lignes × {df_snapshot.shape[1]} colonnes")
    st.dataframe(df_snapshot.head(10), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("♻️ Restaurer ce snapshot comme fichier actif"):
            st.session_state["df"] = df_snapshot.copy()
            st.success(f"✅ Snapshot `{selected_snapshot}` restauré avec succès.")

    with col2:
        if st.button("🗑️ Supprimer ce snapshot"):
            del st.session_state["snapshots"][selected_snapshot]
            st.success(f"🗑️ Snapshot `{selected_snapshot}` supprimé.")
            st.experimental_rerun()
