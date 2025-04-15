# utils/snapshot_utils.py

import streamlit as st
import datetime

def save_snapshot(label=None):
    """
    Sauvegarde un snapshot du DataFrame actif dans session_state["snapshots"].
    """
    df = st.session_state.get("df")
    if df is None:
        st.warning("Aucune donnée active à sauvegarder.")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    label = label or "snapshot"
    snapshot_name = f"{label}_{timestamp}"

    if "snapshots" not in st.session_state:
        st.session_state["snapshots"] = {}

    st.session_state["snapshots"][snapshot_name] = df.copy()
    st.success(f"📸 Snapshot enregistré : `{snapshot_name}`")

def restore_snapshot(snapshot_name):
    """
    Restaure un snapshot comme DataFrame actif.
    """
    snapshots = st.session_state.get("snapshots", {})
    if snapshot_name not in snapshots:
        st.error(f"❌ Snapshot introuvable : {snapshot_name}")
        return

    st.session_state["df"] = snapshots[snapshot_name].copy()
    st.success(f"✅ Snapshot restauré : `{snapshot_name}`")
