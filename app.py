# app.py

import streamlit as st

# Configuration de la page Streamlit
from config import configure_app

# Utils (depuis dossier utils/)
from utils.snapshot_utils import save_snapshot, restore_snapshot
from utils.log_utils import log_transformation
from utils.filters import select_active_dataframe

# Sections fonctionnelles
from sections.chargement import run_chargement
from sections.jointures import run_jointures
from sections.analyse_explo import run_analyse_exploratoire
from sections.analyse_cat import run_analyse_categorielle
from sections.cible import run_cible
from sections.qualite import run_qualite
from sections.multivariee import run_multivariee
from sections.snapshots import run_snapshots
from sections.export import run_export

# =============================================================================
# 🎨 INITIALISATION
# =============================================================================
configure_app()

if "page" not in st.session_state:
    st.session_state.page = "chargement"

# =============================================================================
# ✅ ÉTAPES CLÉS DU MODULE EDA
# =============================================================================
EDA_STEPS = {
    "types": "🧾 Types",
    "missing": "❓ Manquants",
    "histos": "📊 Distributions",
    "outliers": "🚨 Outliers",
    "stats": "📈 Stats",
    "cleaning": "🧹 Nettoyage",
    "correlations": "🔗 Corrélations"
}

# =============================================================================
# 🧭 MENU DE NAVIGATION MODERNE
# =============================================================================
def nav_menu():
    st.markdown("## 🚀 Navigation")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### 📁 Chargement")
        if st.button("📂 Chargement", use_container_width=True):
            st.session_state.page = "chargement"
        if st.button("🔗 Jointures", use_container_width=True):
            st.session_state.page = "jointures"
        if st.button("🕰️ Snapshots", use_container_width=True):
            st.session_state.page = "snapshots"
        if st.button("💾 Export", use_container_width=True):
            st.session_state.page = "export"

    with col2:
        st.markdown("### 🔍 Analyse")
        st.markdown("**Exploration & Qualité**")
        if st.button("🔍 Analyse EDA", use_container_width=True):
            st.session_state.page = "eda"
        if st.button("📊 Catégorielle", use_container_width=True):
            st.session_state.page = "cat"
        if st.button("🎯 Cible", use_container_width=True):
            st.session_state.page = "cible"
        if st.button("🚨 Qualité", use_container_width=True):
            st.session_state.page = "qualite"
        if st.button("🧪 Multivariée", use_container_width=True):
            st.session_state.page = "multi"

    st.markdown("---")


# =============================================================================
# 📊 SIDEBAR : PROGRESSION EDA
# =============================================================================
if "dfs" in st.session_state and st.session_state["dfs"]:
    validation = st.session_state.get("validation_steps", {})
    n_total = len(EDA_STEPS)
    n_done = sum(1 for k in EDA_STEPS if validation.get(k))
    progress_pct = int(n_done / n_total * 100)

    st.sidebar.markdown("### 📊 Progression analyse EDA")
    st.sidebar.progress(progress_pct / 100)
    st.sidebar.markdown(f"**{n_done} / {n_total} étapes validées ({progress_pct}%)**")

    st.sidebar.markdown("### 📌 Étapes")
    for key, label in EDA_STEPS.items():
        status = "✅" if validation.get(key) else "🔲"
        st.sidebar.write(f"{status} {label}")

    if st.sidebar.button("🔄 Réinitialiser l'analyse"):
        st.session_state["validation_steps"] = {}
        st.success("✔️ Progression réinitialisée.")

# =============================================================================
# 🔁 ROUTAGE VERS LES SECTIONS
# =============================================================================
if st.session_state.page == "chargement":
    run_chargement()

elif st.session_state.page == "snapshots":
    run_snapshots()

else:
    df, selected_name = select_active_dataframe()

    if st.session_state.page == "jointures":
        run_jointures()
    elif st.session_state.page == "eda":
        run_analyse_exploratoire(df)
    elif st.session_state.page == "cat":
        run_analyse_categorielle(df)
    elif st.session_state.page == "cible":
        run_cible(df)
    elif st.session_state.page == "qualite":
        run_qualite(df)
    elif st.session_state.page == "multi":
        run_multivariee(df)
    elif st.session_state.page == "export":
        run_export(df)

    # 🎉 Affichage du message final si toutes les étapes sont complétées
    all_steps_done = all(st.session_state.get("validation_steps", {}).get(k) for k in EDA_STEPS)
    if all_steps_done:
        st.balloons()
        st.success("🎉 Toutes les étapes EDA ont été complétées avec succès ! Vous pouvez exporter ou approfondir votre analyse.")
